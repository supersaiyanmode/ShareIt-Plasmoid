from PyKDE4.kio import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import subprocess
import tempfile
import os
import zipfile
import mimetypes
import json
import string
import random

from smtplib import SMTP
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders  

from config import Config


def zipFiles(fileNames):
    zipFileName = getTempFile()
    z = zipfile.ZipFile(zipFileName,'w')
    for f in fileNames:
        if os.path.isfile(f):
            z.write(f, os.path.basename(f))
        elif os.path.isdir(x):
            pass
    z.close()
    return zipFileName

def upload(fileName,mime):
    fields = [('mime', mime), \
                ('key', Config.getInstance()['appkey']) \
    ]
    
    files = [('content',fileName,open(fileName,'r').read())]
    
    boundaryChars = list(string.lowercase) + list(string.uppercase) + \
                    [str(x) for x in range(10)] + ['_'*10]
    random.shuffle(boundaryChars)    
    
    LIMIT = '----------'+''.join(boundaryChars[:15])
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(str(value))
    for (key, filename, value) in files:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % mimetypes.guess_type(filename)[0] or \
                        'application/octet-stream')
        L.append('')
        L.append(str(value))
    L.append('--' + LIMIT + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % LIMIT
    return content_type, body

def getTempFile():
    return tempfile.mkstemp()[1]
    
def writeTempFile(content,mode='w+b'):
    fileName = getTempFile()
    f = open(fileName,mode)
    f.write(content)
    f.close()
    return fileName

def pasteImage(obj):
    fileName = writeTempFile(obj['data'])
    res = upload(fileName,obj['mime'])
    os.unlink(fileName)
    return res

def pasteText(obj):
    fileName = writeTempFile(obj['data'],'w')
    res = upload(fileName,obj['mime'])
    os.unlink(fileName)
    return res

def pasteHTML(obj):
    fileName = writeTempFile(obj['data'],'w')
    res = upload(fileName,obj['mime'])
    os.unlink(fileName)
    return res
    
def pasteFile(obj):
    fileNames = obj['data']
    if len(fileNames) == 1:
        mime = mimetypes.guess_type(fileNames[0])[0] or 'application/octet-stream'
        return upload(fileNames[0],mime)
    else:
        zipFileName = zipFiles(fileNames)
        res = upload(zipFileName, 'application/zip')
        os.unlink(zipFileName)
        return res

def uploadFile(obj):
    if 'type' not in obj:
        return
    res = ""
    if obj['type'].lower() == 'image':
        res = pasteImage(obj)
    elif obj['type'].lower() == 'url':
        res = pasteFile(obj)
    elif obj['type'].lower() == 'html':
        res = pasteHTML(obj)
    elif obj['type'].lower() == 'text':
        res = pasteText(obj)
    return res
    
def pasteCode(text):
    return "text/plain", text
    
def email(emailID, subject, body, obj):
    if 'type' not in obj:
        return
    attachFile = None
    body = ""
    if obj['type'].lower() == 'image':
        attachFile = (writeTempFile(obj['data']), "image.png", "image/png")
    elif obj['type'].lower() == 'url':
        if len(obj['data']) == 1:
            attachFile = (writeTempFile(open(obj['data'][0]).read()),
                        os.path.basename(obj['data'][0]),
                        mimetypes.guess_type(obj['data'][0])[0])
        else:
            attachFile = (zipFiles(obj['data']), "archive.zip", "application/zip")
    elif obj['type'].lower() == 'html':
        print type(obj['data'])
        body = obj['data']
    elif obj['type'].lower() == 'text':
        body = obj['data']
        
    sendEmail(body,subject, emailID, attachFile)
    if attachFile:
        os.unlink(attachFile[0])
    
def sendEmail(body, subject, emailID, attach):
    username = "thrustmaster25@gmail.com"
    pwd = 'ThrustmaximuM'
    msg = MIMEMultipart()
    msg['Subject']= subject
    msg['From']   = username
    msg['To']   = emailID
    
    print type(body)
    
    if body:
        try:
            msg.attach(MIMEText(body))
        except Exception,e:
            print "grrrr.."
            try:
                msg.attach(MIMEText(str(body)))
            except Exception ,e:
                open('temp','w').write(body)
                print "written!"
    
    if attach:
        fileName, baseName, mime = attach
        mime = mime.split("/")
        part = MIMEBase(mime[0], mime[1])
        try:
            part.set_payload(open(fileName, 'rb').read())
        except Exception, e:
            return (False, "Invalid Attachment specification!")
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % baseName)
        msg.attach(part)
    conn = SMTP('smtp.gmail.com',587)
    conn.ehlo()
    conn.starttls()
    conn.ehlo()
    conn.login(username,pwd)
    try:
        conn.sendmail(username, emailID, msg.as_string())
    finally:
        conn.close()
    return (True,"Email Sent!")