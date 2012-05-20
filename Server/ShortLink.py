from google.appengine.api.urlfetch import fetch as urlfetch, GET, POST
try:
    import json
except Exception,err:
    from django.utils import simplejson as json

def getShortUrl(url):
    if not hasattr(getShortUrl,'key'):
        try:
            getShortUrl.key = open('goo-gl-key','r').read().strip()
        except Exception,e:
            return url #return url without shortening

    API_key = getShortUrl.key
    res = urlfetch(url='https://www.googleapis.com/urlshortener/v1/url?key='+API_key,
                    method=POST,
                    payload=json.dumps({'longUrl':url}),
                    headers={'Content-Type':'application/json'})
    if str(res.status_code) != '200':
        return url
    return json.loads(res.content)['id']
    
    