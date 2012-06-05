from PyQt4.QtCore import Qt,QTimer
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from PyKDE4.kio import KIO
from PyKDE4.kdeui import *
from PyKDE4.kdecore import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *

import subprocess
import time
import json
import os
import dbus

from config import Config
from shareit_plasmoid_configui import PlasmoidConfigUI
import emailui

import images_rc
import Paste

def getClipboard():
    return QApplication.clipboard().text()
    
def setClipboard(text):
    return QApplication.clipboard().setText(text)
    
def sendNotify(title, text):
    if not hasattr(sendNotify,'knotify'):
        sendNotify.knotify = dbus.SessionBus().get_object("org.kde.knotify", "/Notify")
        
    sendNotify.knotify.event("warning", "kde", [], "ShareIt-Plasmoid - %s"%title, text, \
                        [], [], 0, 0, dbus_interface="org.kde.KNotify")

class SharePlasmoid(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
    
    def init(self):
        self.setHasConfigurationInterface(True)
        self.resize(150,150)
        self.setAspectRatioMode(Plasma.Square)
        self.setAcceptDrops(True)
        
        self.modes = [
            {
                "name":"UPLOAD", 
                "icons":[QPixmap(":/images/upload%d.png"%x) for x in range(1,6)],
                "handler": self.handleUpload
            },
            {
                "name":"MAIL",
                "icons":[QPixmap(":/images/email%d.png"%x) for x in range(1,6)],
                "handler": self.handleEmail
            },
            {
                "name":"CODE",
                "icons":[QPixmap(":/images/code%d.png"%x) for x in range(1,6)],
                "handler":self.handleCode
            }
                
        ]
        self.curMode = 1
        
        
        self.iconState = {"mouseover":False, "drag":False, "uploading":0}
        
        self.tooltip = Plasma.ToolTipContent()
        self.tooltip.setMainText("Drag drop text, images or file(s) to share")
        self.tooltip.setSubText("The link to share will be copied to your clipboard")
        self.tooltip.setImage(self.modes[self.curMode]['icons'][3].scaled(64,64))
        Plasma.ToolTipManager.self().setContent(self.applet, self.tooltip)
        
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.update)
    
    
    def createConfigurationInterface(self, dialog):
        self.configUi = PlasmoidConfig(self)
        page = dialog.addPage(self.configUi,"Settings")
        
        self.connect(dialog, SIGNAL("okClicked()"), self.configAccepted)
        self.connect(dialog, SIGNAL("cancelClicked()"), self.configDenied)
        
    def showConfigurationInterface(self):
        dialog = KPageDialog()
        dialog.setFaceType(KPageDialog.Plain)
        dialog.setButtons(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel))
        self.createConfigurationInterface(dialog)
        dialog.resize(400,300)
        
        dialog.exec_()
    
    def configAccepted(self):
        print "configAccepted"
        
    def configDenied(self):
        print "configDenied"
        
    def hoverEnterEvent(self, e):
        self.iconState['mouseover'] = True
        self.update()
        
    def hoverLeaveEvent(self,e):
        self.iconState['mouseover'] = False
        self.update()
        
    def dragMoveEvent(self, e):
        self.iconState['drag'] = True
        accept = None
        if e.mimeData().hasImage() or e.mimeData().hasUrls() or \
                e.mimeData().hasHtml() or e.mimeData().hasFormat('text/plain'):
            if e.mimeData().hasUrls():
                urls = [x.toLocalFile().toLocal8Bit().data() for x in e.mimeData().urls()]
                if len(urls):
                    accept =True
                else:
                    accept = False
            else:
                accept = True
        else:
            accept = False
        
        if accept:
            e.accept()
        else:
            e.ignore()
        
        self.update()
        
    def dragLeaveEvent(self,e):
        self.iconState['drag'] = False
        self.update()

    def dropEvent(self, e):
        self.iconState['drag'] = False
        self.update()
        
        pasteData = {}
        if e.mimeData().hasImage():
            img = e.mimeData().imageData().toPyObject()
            buf = QBuffer()
            buf.open(QIODevice.ReadWrite)
            img.save(buf, "PNG")
            pasteData['type'] = 'image'
            pasteData['mime'] = 'image/png'
            pasteData['data'] = buf.data()
        elif e.mimeData().hasUrls():
            pasteData['type'] = 'url'
            pasteData['data'] = [x.toLocalFile().toLocal8Bit().data() for x in e.mimeData().urls()]
        elif e.mimeData().hasHtml():
            pasteData['type'] = 'html'
            pasteData['mime'] = 'text/html'
            pasteData['data'] = e.mimeData().html()
        elif e.mimeData().hasFormat('text/plain'):
            pasteData['type'] = 'text'
            pasteData['mime'] = 'text/plain'
            pasteData['data'] = str(e.mimeData().text())
        else:
            print "Bummer!"
        print type(pasteData['data'])
        self.modes[self.curMode]['handler'](pasteData, e.mimeData().text())
        
        if self.iconState['uploading'] == 0:
            self.updateTimer.start(150)
        self.iconState['uploading'] += 1
    
    def wheelEvent(self, event):
        self.curMode = (self.curMode + len(self.modes) + (1 if event.delta()<0 else -1)) % len(self.modes)
        self.update()
            
    def done(self, job):
        self.iconState['uploading'] -= 1
        if self.iconState['uploading'] == 0:
            self.updateTimer.stop()
         
        try:
            if job.error():
                raise Exception("Unable to send the object.")
            
            data = job.data().data() #convert QByteArray to str
            print data
            response = json.loads(data)
            setClipboard(response['url'])
            sendNotify("Shared!", 'You can access it at <a href="%s">%s</a>.<br><sub>The link has also been copied to your clipboard</sub>'%(response['url'],response['url']))
        except Exception,e:
            sendNotify("Oops!", 'Something went wrong somewhere..')
     
    def paintInterface(self, painter, option, rect):
        painter.save()
        pad = 2
        
        if not hasattr(self, '_uploadIconIndex'):
            self._uploadIconIndex = 3
            self._uploadIconIndexIncrement = 1
        
        if self.iconState['uploading']:
            if self._uploadIconIndex == 5:
                self._uploadIconIndexIncrement = -1
            elif self._uploadIconIndex == 1:
                self._uploadIconIndexIncrement = 1
            self._uploadIconIndex += self._uploadIconIndexIncrement
            
        if self.iconState['drag']:
            pen = QPen(QColor(128,128,128))
            pen.setStyle(4)
            painter.setPen(pen)
            highlightRect = QRect(rect.left()+pad,rect.top()+pad,rect.width()-2*pad, rect.height()-2*pad)
            opacity = painter.opacity()
            painter.setOpacity(0.5)
            painter.fillRect(highlightRect,QColor(0,0,0))
            painter.setOpacity(opacity)
            self._uploadIconIndex = 5
        elif self.iconState['mouseover']:
            self._uploadIconIndex = 5
        elif not self.iconState['uploading'] and not self.iconState['mouseover']:
            self._uploadIconIndex = 3
            
        targetRect = QRect(rect.left()+pad, rect.top()+pad,
                        rect.width()-2*pad, rect.height()-2*pad)
        img = self.modes[self.curMode]['icons'][self._uploadIconIndex-1].scaled(targetRect.size())
        painter.drawPixmap(targetRect, img, QRect(0,0,targetRect.width(), targetRect.height()))
        
        painter.restore()
        
    def handleUpload(self, pasteData, text):
        contentType, postData = Paste.uploadFile(pasteData)
        
        self.job = KIO.storedHttpPost(QByteArray(postData), \
                    KUrl("%s/paste"%Config.getInstance()['appurl']), \
                    KIO.HideProgressInfo)
                    
        self.job.addMetaData("content-type", "Content-Type: %s"%contentType)
        self.job.addMetaData("accept", "Accept: */*")
        self.job.addMetaData("user-agent", "User-Agent: share-plasmoid")

        self.job.result.connect(self.done)
        self.job.start()
        
    def handleCode(self, pasteData, text):
        contentType,postData = Paste.pasteCode(text)
        self.job = KIO.storedHttpPost(QByteArray(postData), \
                    KUrl("%s/paste"%Config.getInstance()['appurl']), \
                    KIO.HideProgressInfo)
                    
        self.job.addMetaData("content-type", "Content-Type: %s"%contentType)
        self.job.addMetaData("accept", "Accept: */*")
        self.job.addMetaData("user-agent", "User-Agent: share-plasmoid")

        self.job.result.connect(self.done)
        self.job.start()
        
    def handleEmail(self, pasteData, text):
        print type(pasteData['data'])
        dialog = KPageDialog()
        dialog.setFaceType(KPageDialog.Plain)
        dialog.setButtons(KDialog.ButtonCode(KDialog.Ok | KDialog.Cancel))
        width, height =  dialog.size().width(), dialog.size().height()
        
        self.emailUi = QWidget()
        self.emailDialog = emailui.Ui_Dialog()
        self.emailDialog.setupUi(self.emailUi)
        
        width = self.emailUi.size().width() + 30
        height = self.emailUi.size().height() + 30
        
        page = dialog.addPage(self.emailUi,"Settings")
        
        self.connect(dialog, SIGNAL("okClicked()"), 
            lambda: Paste.email(
                str(self.emailDialog.txtEmailTo.text()).strip(),
                str(self.emailDialog.txtSubject.text()).strip(),
                str(self.emailDialog.txtBody.toPlainText()).strip(),
                pasteData
            )
        )
        self.connect(dialog, SIGNAL("cancelClicked()"),lambda: ())
        
        dialog.resize(width,height)
        
        dialog.exec_()
        
        self.iconState['uploading'] -= 1
        if self.iconState['uploading'] == 0:
            self.updateTimer.stop()
        
def CreateApplet(parent):
    return SharePlasmoid(parent)
