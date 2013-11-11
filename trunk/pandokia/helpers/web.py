import urllib2
import cookielib
import urllib

cookiejar = cookielib.LWPCookieJar()
cookie_processor = urllib2.HTTPCookieProcessor(cookiejar)

def GET( url, args=None, cred=None ) :
    """do http get

    url is the URL you want
    args is a dict of cgi args
    cred is ( host, realm, username, password )
    """

    auth_handler = None

    arg_string = ''

    if not args is None :
        arg_string = "?" + urllib.urlencode( args )

    if not cred is None :
        ( host, realm, username, password ) = cred
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm, host, username, password)

    if auth_handler :
        opener = urllib2.build_opener(cookie_processor, auth_handler)
    else :
        opener = urllib2.build_opener(cookie_processor )
    urllib2.install_opener(opener)

    print "URL",url
    f = urllib2.urlopen(url + arg_string)
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
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm, host, username, password)

    if auth_handler :
        opener = urllib2.build_opener(cookie_processor, auth_handler)
    else :
        opener = urllib2.build_opener(cookie_processor )

    urllib2.install_opener(opener)

    print "URL",url
    data = urllib.urlencode(args)
    req = urllib2.Request(url, data)
    f = urllib2.urlopen(req)
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

