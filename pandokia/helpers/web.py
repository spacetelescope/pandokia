try:
    from http.cookiejar import LWPCookieJar
    from urllib.parse import urlencode
    from urllib.request import HTTPBasicAuthHandler, HTTPCookieProcessor, Request, build_opener, install_opener, urlopen
except ImportError:
    from cookielib import LWPCookieJar
    from urllib import urlencode
    from urllib2 import HTTPBasicAuthHandler, HTTPCookieProcessor, Request, build_opener, install_opener, urlopen


cookiejar = LWPCookieJar()
cookie_processor = HTTPCookieProcessor(cookiejar)


def GET( url, args=None, cred=None ) :
    """do http get

    url is the URL you want
    args is a dict of cgi args
    cred is ( host, realm, username, password )
    """

    auth_handler = None

    arg_string = ''

    if not args is None :
        arg_string = "?" + urlencode( args )

    if not cred is None :
        ( host, realm, username, password ) = cred
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(realm, host, username, password)

    if auth_handler :
        opener = build_opener(cookie_processor, auth_handler)
    else :
        opener = build_opener(cookie_processor )
    install_opener(opener)

    print("URL %s"%url)
    f = urlopen(url + arg_string)
    return f

def POST( url, args={ }, cred=None ):
    """do http post

    url is the URL you want
    args is a dict of cgi args
    cred is ( host, realm, username, password )
    """

    auth_handler = None

    arg_string = ''

    if not cred is None :
        ( host, realm, username, password ) = cred
        auth_handler = HTTPBasicAuthHandler()
        auth_handler.add_password(realm, host, username, password)

    if auth_handler :
        opener = build_opener(cookie_processor, auth_handler)
    else :
        opener = build_opener(cookie_processor )

    install_opener(opener)

    print("URL %s"%url)
    data = urlencode(args)
    req = Request(url, data)
    f = urlopen(req)
    return f


def rot13_6(a) :
    r = ''
    for x in a :
        if x.isupper() :
            x=chr(((ord(x)-65)+13)%26 + 65)
        elif x.islower() :
            x=chr(((ord(x)-97)+13)%26 + 97)
        elif x.isdigit() :
            x=chr((ord(x)-48+6)%10+48)
        r = r + x
    return r

#####
#
# retrieve a cookie by name from 

def get_cookie( host=None, directory=None, name=None ) :
    if host == '-' :
        host = sorted(cookiejar._cookies)[0]
    if host is None :
        return cookiejar._cookies
    elif directory is None :
        return cookiejar._cookies[host]
    elif name is None :
        return cookiejar._cookies[host][directory]
    else :
        return cookiejar._cookies[host][directory][name]
    
###
"""
to do someday:

make an object of this, like
https://gist.github.com/rduplain/1265409
"""

