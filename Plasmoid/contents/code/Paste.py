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

def upload(fileName,mime):
    return (multipart.post_multipart('file-sharer.appspot.com','/paste',
            [('mime', mime)],
            [('content',fileName,open(fileName,'r').read())]
    ))


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
