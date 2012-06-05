import os
import json

class Config:
    def __init__(self, filePath):
        self.filePath = filePath
        try:
            self.config = json.loads(open(filePath,'r').read())
        except Exception,e:
            self.config = {}
            self._writeConfig()
    
    def __getitem__(self, key):
        if key in self.config:
            return str(self.config[key])
        raise KeyError(key)
    
    def __setitem__(self, key, value):
        self.config[key] = value
        self._writeConfig()
        
    def _writeConfig(self):
        f = open(self.filePath,'w')
        f.write(json.dumps(self.config,indent = 4))
        f.close()
    
    @staticmethod
    def getInstance():
        return Config(os.path.expanduser('~/.shareitplasmoid.cfg'))
    