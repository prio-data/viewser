
from urllib import parse
import webbrowser

def open_browser(base,*args,**kwargs):
    querystring = parse.urlencode(kwargs)
    url = "/".join([base] + list(args))
    if querystring:
        url += "?"+querystring
    webbrowser.open(url)
