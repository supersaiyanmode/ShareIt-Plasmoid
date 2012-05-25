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
import Paste
import images_rc
import time
import json
import os
import dbus

def getClipboard():
    return QApplication.clipboard().text()
    
def setClipboard(text):
    return QApplication.clipboard().setText(text)
    
def getAppId():
    if not hasattr(getAppId,'appid'):
        getAppId.appid = json.loads(open(os.path.expanduser('~/.shareitplasmoid.cfg'),'r').read())['appid']
    return getAppId.appid

def sendNotify(title, text):
    if not hasattr(sendNotify,'knotify'):
        sendNotify.knotify = dbus.SessionBus().get_object("org.kde.knotify", "/Notify")
        
    sendNotify.knotify.event("warning", "kde", [], "ShareIt-Plasmoid - %s"%title, text, \
                        [], [], 0, 0, dbus_interface="org.kde.KNotify")

class SharePlasmoid(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)
    
    def init(self):
        self.setHasConfigurationInterface(False)
        self.resize(150,150)
        self.setAspectRatioMode(Plasma.Square)
        self.setAcceptDrops(True)
        
        self.uploadIcon = QPixmap(':/images/upload.png')
        self.iconState = {"mouseover":False, "uploading":0}
        
        self.tooltip = Plasma.ToolTipContent()
        self.tooltip.mainText = "Drag drop text, images or file(s) to share"
        self.tooltip.subText = "The link to share will be copied to your clipboard"
        #self.tooltip.image = self.uploadIcon
        Plasma.ToolTipManager.self().setContent(self.applet, self.tooltip)

        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.update)
        
        
    def dragEnterEvent(self, e):
        self.iconState['mouseover'] = True
        self.update()
        if e.mimeData().hasImage() or e.mimeData().hasUrls() or \
                e.mimeData().hasHtml() or e.mimeData().hasFormat('text/plain'):
            if e.mimeData().hasUrls():
                urls = [x.toLocalFile().toLocal8Bit().data() for x in e.mimeData().urls()]
                if len(urls):
                    e.accept()
                else:
                    e.ignore()
            else:
                e.accept()
        else:
            e.ignore()
            
    def dragLeaveEvent(self,e):
        self.iconState['mouseover'] = False
        self.update()

    def dropEvent(self, e):
        self.iconState['mouseover'] = False
        self.update()
        
        pasteData = {}
        if e.mimeData().hasImage():
            print "Sending image!"
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
            pasteData['data'] = e.mimeData().text()
        else:
            print "Bummer!"
        
        contentType, postData = Paste.paste(pasteData)        
        
        self.job = KIO.storedHttpPost(QByteArray(postData), \
                    KUrl("http://www.%s.appspot.com/paste"%getAppId()), KIO.HideProgressInfo)
                    
        self.job.addMetaData("content-type", "Content-Type: %s"%contentType)
        self.job.addMetaData("accept", "Accept: */*")
        self.job.addMetaData("user-agent", "User-Agent: share-plasmoid")

        self.job.result.connect(self.done)
        self.job.start()
        
        if self.iconState['uploading'] == 0:
            self.updateTimer.start(80)
        self.iconState['uploading'] += 1
        
    def done(self, job):
        self.iconState['uploading'] -= 1
        if self.iconState['uploading'] == 0:
            self.updateTimer.stop()
            self._pad = 5
        
        try:
            if job.error():
                raise Exception("Unable to send the object.")
            
            data = job.data().data() #convert QByteArray to str
            print data
            response = json.loads(data)
            setClipboard(response['url'])
            #subprocess.Popen(['/usr/bin/notify-send','-u','critical','-i','kollision','Shared!',
                #])
            sendNotify("Shared!", 'You can access it at <a href="%s">%s</a>.<br><sub>The link has also been copied to your clipboard</sub>'%(response['url'],response['url']))
        except Exception,e:
            #subprocess.Popen(['/usr/bin/notify-send','-u','critical','-i','kollision','Error!','Oops! Something went wrong!' + str(e)])
            sendNotify("Oops!", 'Something went wrong somewhere..')

    def paintInterface(self, painter, option, rect):
        painter.save()
        
        if not hasattr(self, '_pad'):
            self._pad = 5
            self._padSizeDelta = 1
            
        if self.iconState['uploading']:
            if self._pad == 7:
                self._padSizeDelta = -1
            elif self._pad == 3:
                self._padSizeDelta = 1
            self._pad += self._padSizeDelta
            
        if self.iconState['mouseover']:
            pen = QPen(QColor(128,128,128))
            pen.setStyle(4)
            painter.setPen(pen)
            pad = 2
            highlightRect = QRect(rect.left()+pad,rect.top()+pad,rect.width()-2*pad, rect.height()-2*pad)
            opacity = painter.opacity()
            painter.setOpacity(0.5)
            painter.fillRect(highlightRect,QColor(0,0,0))
            painter.setOpacity(opacity)
        
        pad = self._pad
        targetRect = QRect(rect.left()+pad, rect.top()+pad,
                        rect.width()-2*pad, rect.height()-2*pad)
        img = self.uploadIcon.scaled(targetRect.size())
        painter.drawPixmap(targetRect, img, QRect(0,0,targetRect.width(), targetRect.height()))
        
        painter.restore()
        
def CreateApplet(parent):
    return SharePlasmoid(parent)
