from google.appengine.ext import db

class Paste(db.Model):
    time = db.DateTimeProperty(auto_now_add=True)
    title = db.StringProperty()
    mime = db.StringProperty()
    content = db.BlobProperty(required=True)
    name = db.StringProperty()