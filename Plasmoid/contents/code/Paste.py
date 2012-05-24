from PyKDE4.kio import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import subprocess
import tempfile
import os
import zipfile
import mimetypes
import json
import multipart
import string
import random

def upload(fileName,mime):
    fields = [('mime', mime)]
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
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + LIMIT)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % mimetypes.guess_type(filename)[0] or \
                        'application/octet-stream')
        L.append('')
        L.append(value)
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
        def getFilesFromDir(dirName):
            if not os.path.isdir(dirName):
                return []
            
        zipFileName = getTempFile()
        z = zipfile.ZipFile(zipFileName,'w')
        for f in fileNames:
            if os.path.isfile(f):
                z.write(f, os.path.basename(f))
            elif os.path.isdir(x):
                pass
        z.close()
        res = upload(zipFileName, 'application/zip')
        os.unlink(zipFileName)
        return res

def paste(obj):
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
