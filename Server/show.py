from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import Paste
import logging

class Show(webapp.RequestHandler):
    def get(self,key):
        try:
            obj = Paste.Paste.get_by_key_name(key)
            if not obj:
                raise Exception()
            self.response.headers["Content-Type"] = obj.mime
            self.response.out.write(obj.content)
        except Exception, e:
            self.error(404)

application = webapp.WSGIApplication([('/(.*)/.*',Show)],debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
