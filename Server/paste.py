from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from uuid import uuid4
import ShortLink
import mimetypes
import Paste

APP_KEY = "OWI0NDdhMDktMzJmNC00NGIyLTlmOTMtODA1NGNmNjA5M2QyZDAzZjMyZmMtZGYzMi00NTdjLWI0"
class Paster(webapp.RequestHandler):
    def post(self):
        key = self.request.get("key")
        if key != APP_KEY:
            self.error(404)
            return
        
        content = self.request.get("content")
        if content in (None,""):
            self.error(400)
            return
        
        title = self.request.get("title")
        mime = self.request.get("mime") or "application/octet-stream"
        
        keyName = str(uuid4())
        Paste.Paste(title=title, content=str(content),key_name=keyName, mime=mime).put()
        
        url = self.request.url[:self.request.url.index("/paste")] + "/" + keyName + "/paste"
        
        #Add a possible extension to the link
        ext = mimetypes.guess_extension(mime)
        if ext: url += ext
        
        self.response.out.write(json.dumps({"result":"success", "url":ShortLink.getShortUrl(url)}))
        self.response.out.write("\r\n")
        
    def get(self):
        if self.request.get("key") == APP_KEY:
            self.response.out.write(json.dumps({"result":"success"}))
        else:
            self.error(404)
        

application = webapp.WSGIApplication([('/paste',Paster)],debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
