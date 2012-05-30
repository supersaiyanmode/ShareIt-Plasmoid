from PyQt4.QtGui import QWidget
from configui import Ui_Dialog
from config import Config

import urllib
import json

class PlasmoidConfigUI(QWidget,Ui_Dialog):
    def __init__(self,parent):
        self.config = Config.getInstance()
        
        QWidget.__init__(self)
        self.parent = parent
        self.setupUi(self)
        self.txtAppId.setText(self.config['appid'] or "")
        self.txtAppKey.setText(self.config['appkey'] or "")
    
    def btnTest_clicked(self):
        self.btnTest.setText("Testing..")
        value = self.getAllConfig()
        try:
            url = "http://%s.appspot.com/paste?key=%s"%(value['appid'],value['appkey'])
            print url
            r = urllib.urlopen(url)
            res = r.read()
            print "res", res
            if json.loads(res)['result'].lower() == "success":
                self.btnTest.setText("Success!")
                
                #Save to self.successConfig, and write to config File upon "OK"
                self.config['appid'] = value['appid']
                self.config['appkey'] = value['appkey']
            else:
                raise Exception("error")
        except Exception, e:
            print e
            self.btnTest.setText("Failed!")
        
    def getAllConfig(self):
        val = lambda x:str.strip(str(x))
        
        return {"appid": val(self.txtAppId.text()), "appkey":val(self.txtAppKey.text())}
