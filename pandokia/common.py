#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
# common.py - bunch of library functions used by parts of pandokia
#

import cStringIO
import datetime
import time
import os
import os.path
import re
import urllib
import types

import pandokia
cfg = pandokia.cfg

######
#--#--# CGI
#
# function to check if CGI user is authorized
#   currently returns priv level:
#       0 is not authorized
#       1 is authorized
#           (we may make multiple levels of access later)
#

def check_auth() :
    # Assume they are not authorized, then look for a reason to allow them in.
    auth_ok = 0

    # If the web server checked them with BasicAuth, we will use that:

    if ( "AUTH_TYPE" in os.environ ) and ( os.environ["AUTH_TYPE"] == 'Basic' ) :
        if cfg.user_list is None :
            # If there is no user_list in the config, any authenticated user is accepted.
            auth_ok = 1
        else :
            # If the config contains user_list, only those people are authorized.
            if os.environ["REMOTE_USER"] in cfg.user_list :
                auth_ok = 1

        # One way or another, we have an answer now
        return auth_ok

    # The web server is not enforcing authentication.

    if cfg.user_list is None :
        # we don't have a list to restrict to, so anybody is ok
        auth_ok = 1
    else :
        # we have a list of users, but we don't know who this one is
        auth_ok = 0

    return auth_ok

#
# function to create a URL for a link back to our own CGI
#
# query_dict is a list of cgi parameters
# linkmode is the 'query' value to pass in; 
#

def selflink( query_dict, linkmode ) :
    """
    query_dict is a dict of all the cgi parameters
    linkmode is the name of the query field to include
    """
    l = [ 'query=' + urllib.quote_plus(linkmode) ]
    for i in query_dict :
        v = query_dict[i]
        if v is None :
            continue
        l.append( i + '=' + urllib.quote_plus(str(v)) )
    return get_cgi_name() + "?" + ( '&'.join(l) )

#
# convert a dictionary into a set of <input type=hidden> html
#

def query_dict_to_hidden( query_dict ) :
    l = [ ]
    for x in query_dict :
        v = query_dict[x]
        if v is not None :
            l.append( '<input type=hidden name=%s value=%s>'%(x,v) )
    return '\n'.join(l)

cached_cgi_name = None

def get_cgi_name() :

    global cached_cgi_name

    if cached_cgi_name is None :
        import pandokia.pcgi

        # we prefer to use the cgi name from pcgi, because that is what the
        # web server told us the cgi name really is.  But, we might not be in
        # a cgi; in that case, we use whatever is in the config file.
        try :
            cached_cgi_name = pandokia.pcgi.cginame
        except AttributeError :
            cached_cgi_name = cfg.cginame

    return cached_cgi_name


#
# like selflink, but create a whole href
#   parameter 'text' may contain html.
#

def self_href( query_dict, linkmode, text ) :
    return '<a href="%s">%s</a>'%(selflink(query_dict, linkmode),text)


######
#--#--# DB
#
# database functions
#
# Currently, we only use sqlite3.  Later, there will be cfg.db_type
# that switches among different database access libraries.
#
# Since we were in a hurry to get it working, we use certain sqlite3
# features:
#
# These sqlite features are:
#
# PRAGMA synchronous = OFF;
#   FULL = pause to wait for data to get to disk; guards against
#       db corruption in case of system crash, but slow
#   NORMAL = pause only at the most critical moments
#   OFF = hand off writes to the OS and continue; as much as 50
#       times faster than FULL, but if the OS crashes or you
#       lose power, the db might get corrupted.
#   We are not doing many writes in this cgi, and power fail /
#   os crashes are pretty rare.  If our db gets hosed, we'll
#   either live without the old data or rebuild it.
#
# db.text_factory = str
#   cause all strings to be extracted as str instead of unicode.
#
#   Some of the STSCI log files contain byte sequences that look like
#   invalid UTF-8 sequences.  It manages to insert the invalid UTF-8
#   into the database, but chokes on extracting them.  So, for now,
#   it's all 8 bit ASCII.  Or 8859-1 if you prefer...
#

def get_db_module() :
    try :
	# if you have python 2.5, this is part of python (if you
	# have the sqlite libraries)
        import sqlite3
    except ImportError, e :
	# if you have python 2.4, you have to install pysqlite2,
	# which is about the same as sqlite3, but with the library
	# in a different name.
	import pysqlite2.dbapi2 as sqlite3
    return sqlite3

# db is the main database
# qdb is the query-related database
#
def open_db ( ):
    sqlite3 = get_db_module()
    global db
    dbname = cfg.dbdir+"/pdk.db"
    if not os.path.exists(dbname) :
        print "NO DATABASE FILE",dbname
    db = sqlite3.connect(dbname,timeout=10)
        # timeout is how long to wait if the db is locked; mostly
        # only an issue if an import is happening
    db.execute("PRAGMA synchronous = OFF;")
    db.text_factory = str;
    return db

def open_qdb ( ) :
    sqlite3 = get_db_module()
    global qdb

    # timeout = 45 seconds. we may have to wait as long as it takes
    # to implement somebody else's transaction.  That can only be
    # as long as we allow the cgi to run.  In practice, this timeout
    # is rare/nonexistant on our Xeon, but happens once in a while on
    # our 400 mhz UltraSparc.

    dbname = cfg.dbdir+"/pdk_query.db"
    if not os.path.exists(dbname) :
        print "NO DATABASE FILE",dbname
    qdb = sqlite3.connect(dbname, timeout=45 )
    qdb.execute("PRAGMA synchronous = OFF;")
    qdb.text_factory = str;
    return qdb


#
#

re_funky_chars = re.compile('[^ -~]')   
# used to remove control characters.  Yes, it works on strings with \0
# in them.

re_single_quote = re.compile("'")


def next_name( v ) :
    global name_dict_counter
    n = str(name_dict_counter)
    name_dict[n] = v
    name_dict_counter += 1
    return n

def where_tuple(list) :
    global name_dict_counter, name_dict
    name_dict = { }
    name_dict_counter = 0

    and_list = [ ]
    for name, value in list :
        if ( value == '*' ) or ( value is None ) :
            # if value is "*", we don't need to do a
            # comparison at all.  In sqlite, " xxx glob '*' "
            # takes much longer than leaving out the glob operator.
            or_list = [ ] 
        else :
            # If value is a list, the query is to match any of the values.
            # If it is not a list, we have a list of 1 value.
            if not isinstance( value, types.ListType ) :
                value = [ value ]

            # print "VALUE", name, value
            or_list = [ ]
            for v in value :
                if v is None :
                    # Our convention is that None matches anything,
                    # so if one of the possible values is None, then this
                    # field will always match
                    or_list = [ ]
                    break

                v = str(v)

                # I assume any control character is hostile action.  It
                # is convenient to just quietly drop it.
                v = re_funky_chars.sub('',v)

                #
                n = next_name( v )
                # if value contains a wild card, add a GLOB
                # action, otherwise add '='.
                if '*' in v or '?' in v or '[' in v :
                    or_list.append( name + " GLOB :" + n + " " )
                else :
                    or_list.append( name + " = :" + n + " " )
                
        # print "or_list",or_list
        if len(or_list) > 0 :
            and_list.append( '(' + ( ' OR ' .join( or_list ) ) + ')' )

    res = ' AND '.join(and_list)

    # if we some how managed to avoid adding any conditions to the
    # string, we also do not want the word "WHERE " in it.  The
    # user then has "select ... from table" + ""
    if res != "" :
        res =  "WHERE " + res
    return res, name_dict


#
# convert a test_run name entered by a user into a real test_run name; various
# nicknames get translated into real names.
#
def find_test_run( run) :

    # there are a whole bunch of daily nicknames

    if run.startswith('daily_') :

        if run == "daily_latest" :
            # We usually use daily_latest to mean today; we used to search the database
            # for the latest one, but if we assume it is today, it runs lots faster
            d = datetime.date.today()
            return "daily_%04d-%02d-%02d"%(d.year,d.month,d.day)

        # daily_yesterday is "yesterday" except it is friday if today is monday; you
        # really don't get much from comparing sunday's results to monday's
        if run == 'daily_yesterday' :
            d = datetime.date.today()
            if d.weekday() == 0 :
                # if today is monday, find friday
                d = d - datetime.timedelta(days=3)
            else :
                # tuesday - friday, find yesterday
                d = d - datetime.timedelta(days=1)
            return "daily_%04d-%02d-%02d"%(d.year,d.month,d.day)

        if run.startswith("daily_") :
            daymap = { "mon":0, "tue":1, "wed":2, "thu":3, "fri":4, "sat":5, "sun":6 }
            t = run[6:9]
            if t in daymap :
                t = daymap[t]
                n = 0
                d = datetime.date.today()
                while d.weekday() != t :
                    d = d - datetime.timedelta(days=1)
                    n = n + 1
                    if n > 10 :
                        raise Exception("bug")
                return "daily_%04d-%02d-%02d"%(d.year,d.month,d.day)

    # did not find any special names
    return run


#
# not fully developed - used so the day_report can go back to the day before
#

def previous_daily( test_run ) :
    if not test_run.startswith("daily_") :
        return None
    n = test_run.split( '_' )
    n = n[1]
    n = n.split("-")
    try :
        n = datetime.date(int(n[0]),int(n[1]),int(n[2]))
    except :
        return None
    n = n - datetime.timedelta(days=1)
    return "daily_%04d-%02d-%02d" % ( n.year, n.month, n.day )

def next_daily( test_run ) :
    if not test_run.startswith("daily_") :
        return None
    n = test_run.split( '_' )
    n = n[1]
    n = n.split("-")
    try :
        n = datetime.date(int(n[0]),int(n[1]),int(n[2]))
    except :
        return None
    n = n + datetime.timedelta(days=1)
    return "daily_%04d-%02d-%02d" % ( n.year, n.month, n.day )


#
# look up a contact for a test
#
def get_contact( project, test_name, mode='str') :
    # 
    c = db.execute("SELECT email FROM contact WHERE project = ? AND test_name = ? ORDER BY email",(project, test_name))
    s = [ ]
    for x in c :
        s.append(x[0])
    if mode == 'str' :
        return " ".join(s)
    elif mode == 'list' :
        return s
    else :
        raise Exception("get_contact invalid mode %s"%mode)

######
#--#--# GENERAL
#
# This is a simple MVC expander, without the M and C. :)
#
# Input is text and symbol tables; output is text with variables expanded.
#
# usage:
#
# expand( text, dictlist = [ globals(), locals(), { ... } ],
#               valid = { ... }, format='text' )
#
# Variables in the input text will be substitued with the values from
# the dictionaries passed in.
#
# Variables are specified in the form:
#       %name/format;
# name is the name of the variable, and format is a method of
# substitution.  
#
# It looks for name in the dictionaries in dictlist, using the first
# value it finds.  If name is not defined, the value is 'UNDEF'.
#
# format is one of:
#       text    substitute the string exactly with no changes
#       cgi     if value is a string, urllib.quote_plus(value)
#               else urllib.urlencode(value)
#       html    cgi.escape(string, quote=True)
#       ''      default format
#
# To get a % sign, use "%;"
#
# If the parameter 'valid=' is given, name must be in valid to be expanded
# and valid[name] is the format to use, regardless of the format in the format string.
# Thus, you can limit the list of variables that can be expanded and be sure
# that the user can't screw up your html, even if you do not create the text yourself.
# 

# bug: describe how it works

# I don't think this is actually used in this release.  I copied it in from another
# project, but never got around to using it.

var_pattern = re.compile("(%[^;]*);")

def expand(text, dictlist = [ ] , valid = None, format='' ) :
    result = cStringIO.StringIO()
    textlist = re.split(var_pattern, text)
    for x in textlist :
        if x.startswith('%') :
            x = x[1:].split('/')
            name = x[0]
            if valid : 
                if not name in valid :
                    result.write("(%s-NOT-VALID)"%name)
                    continue
                else :
                    this_format = valid[name]
            if len(x) > 1 :
                this_format = x[1]
            else :
                this_format = format
            if name == '' :
                result.write('%')
            else :
                val = 'UNDEF'
                for y in dictlist :
                    if name in y :
                        val = y[name]
                        break
                if this_format == '' or this_format == 'text' :
                    result.write(str(val))
                elif this_format == 'cgi' :
                    if isinstance(val, basestring) :
                        val = urllib.quote_plus(val)
                    else :
                        val = urllib.urlencode(val)
                    result.write(val)
                elif this_format == 'html' :
                    val = cgi.escape(str(val),quote=True)
                    result.write(val)
                else :
                    result.write(str(val))
        else :
            result.write(x)
    return result.getvalue()


######
#--#--# CGI
#
# HTTP headers
#

cgi_header_csv = "content-type: text/csv\n\n"

cgi_header_html = "content-type: text/html\n\n"


######
#--#--# CGI
#
# what user are we logged in as
#

current_user_name = None

def current_user() :
    if 'REMOTE_USER' in os.environ :
        return os.environ["REMOTE_USER"]
    return None

######
#--#--# GENERAL
#
# convert to/from a datetime
#

def parse_time( arg ) :
    '''
    parse one of several time formats into a datetime 

    It tries these formats in this order:

    time_t
        1263488141
        1263488141.25

    sql (like TIMESTAMP in sql-92, without time zones)
        2010-01-14 11:55:41
        2010-01-14 11:55:41.25

    ctime()
        Thu Jan 14 11:55:41 2010

    We don't even try to parse ISO 8601 because it is so freaking
    complicated.  If your system can generate 2008-06-04T13:28:00.00
    (one of the many 8601 formats), you can replace the 'T' with a
    space yourself, and the 'sql' format will read it.

    All times are local time, except date(1) which has a time zone.

    The returned value has a precision of microseconds; this is a
    limitation of the python datetime object.  date and ctime formats
    do not include fractional seconds, so we do not parse them.

    If you need to convert the returned value into a string, use:

    >>> d=parse_time('2010-01-14 11:55:41.251234')
    >>> sql_time(d)
    '2010-01-14 11:55:41.251234'

    You can then use that value in string comparisons in your SQL statements.

    '''

    # time_t
    #   1263488141
    #   1263488141.25
    try :
        x = float(arg)
        d = datetime.datetime.fromtimestamp(x)
        return d
    except ValueError:
        pass

    # sql time:
    #   2008-06-04 13:28:00.00
    try :
        if '.' in arg :
            x = arg.split('.')
            d = datetime.datetime.strptime(x[0],'%Y-%m-%d %H:%M:%S')
            d = d.replace(microsecond=int((x[1]+'000000')[0:6]))
        else :
            x = time.strptime(arg,'%Y-%m-%d %H:%M:%S')
            d = datetime.datetime(year=x[0], month=x[1], day=x[2],
		hour=x[3], minute=x[4], second=x[5] )
	    # not in 2.4:
            # d = datetime.datetime.strptime(arg,'%Y-%m-%d %H:%M:%S')
        return d
    except ValueError :
        pass

    # ctime
    #   Thu Jan 14 11:37:39 2010
    # (no usec)
    try :
        d = datetime.datetime.strptime(arg,'%a %b %d %H:%M:%S %Y')
        return d
    except ValueError:
        pass

    # didn't match anything?  ok, well the last exception is
    # as good as anything else we might raise
    raise


def sql_time(d) :
    '''
    turn a datetime into a string that looks like TIMESTAMP in SQL-92

    >>> sql_time(datetime.datetime(2010, 1, 14, 11, 55, 41)) 
    '2010-01-14 11:55:41.000000'

    '''
    # do not use ".%f" - it doesn't work
    return d.strftime('%Y-%m-%d %H:%M:%S') + ( '.%06d' % d.microsecond )



######
#--#--# GENERAL
#
# determine the host name, for reporting purposes
#
# For now, I don't care about the domain because it is always the same
# for me and writing .stsci.edu after the host name all the time just
# causes clutter.  Later, we'll make it configurable whether to
# trim off the domain or not.
#

hostname = None

def gethostname( ) :
    global hostname
    if hostname is None :
        import platform
        hostname = platform.node()
        if "." in hostname :
            hostname = hostname.split(".")[0]
    return hostname
    # bug: decided when to use fqdn or not; override hostname in config; etc



######

page_header_text = None


def page_header() :
    global page_header_text

    # check for cached, though the cached copy will probably never be needed
    if page_header_text is not None :
        return page_header_text


    try :
        s1 = cfg.server_title
    except AttributeError :
        s1 = "<h1><a href=%(url)s><img src='data:image/png;base64,%(image)s' alt='' border=0></a>&nbsp;Pandokia</h1>"

    page_header_text = s1 % { 'url' : get_cgi_name(), 'image' : B64IMG_HEADER }

    return page_header_text
B64IMG_FAVICO = 'None'
B64IMG_HEADER = 'iVBORw0KGgoAAAANSUhEUgAAAFoAAABhCAYAAABWFbZsAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9oEFA8bIbuJbxgAACAASURBVHja7LxpsK3ZXd73W+887vnMdx56bhFaatSRwBIIk8QUUyrYDo4LEzAqp/zBCg52iIGmKAgOKUxBYqayKcwQg5yYEkMKByEhRgl1t3qebvcd+p55z/ud3zXkwz66qTgBuyUSVyVaVfvLrn3O2ed513rW//88z1rCGMMXxv/zw/oCBF8A+v9Tw/nX32iaGktYNG2D63q4rvt/+4Pj8ZjRaMR//0M/aI82hupvfOsH2b97CyEs0rSL5/lYlkXbNhij8bwA1/O+APRnh+uuwYhcl3+dv/cP7jqBHxjP89Wv/PNf5vkXnn3/cjYddntdmrb5ja/4wF90r1y9b2VZFmVZUBUFSdrBth2auvr/9YwW/7ab4W/+1m/wvi99H3Xd8A/+wXd98LnPPP+TxyeH6LahlQ22pRmNRnzNV38t3/CNf0VcvnIdy7KI4gQAKVscx/0C0P+m8epLzxME8c4PfM93H7z44ovEcUwcx5RliW3brFZLTk7eQmjNtatXec+Xvved3/E9/+3Ty8WM4cY2QogvcPSfNaqyZLVc8As/+ROssvLgYx/9Ha5du4bjOAx6faogpG1boiBkb3tAUeQc3d3nd37rt39me7T5yjv/wvu/LQiCMun0v1B1/FnD830+9pu/8V23b909+MM//CM2NjawbZswDKmqCsuysCyLpmkwwmY02qLbH6GkeOzD/+JfftPv/85v/X7S6XN8vO98Aeg/Y7RNw7UHH/7Bk5PTHc/z2N3dxXVdNjY22Nraotfr0e/3cRyH2WzBbLGi1x2xvXsegctH/7ePP3b39hvO+ORIfYE6/oyhpOQ3f/UjJkk6bG5vYTkOURRRVRXL5RLLsjDGEAQBGo3WmqptODfa4rF3Ps7Tzz3FT/6PP/avkl78aw8/+s5/9IUZ/acMqeSVF154jul0jOd57O3tEQQBOzs77O3t4bouRVFgWRZB6GGEJkoSbMchz3MeefQdHOwffPnhwfGPfIE6/pSxWi35mf/hx944Pjni8cffxebmJkVRsLu7i1IKy7LY2tri/Pnz+L6P5zkkSQTC4LgWbuBiWRYPPfII08Wcv/mtf9lUZU6erwDI85y6qiiL/N7fLPKcyXgcZav1Z6qqZDEf95fLqTWbTZCypW0bWtn+OwFsOj8G4OTkwJvPJztZvuTk9GBQVgWrfPG5UYcQAsdzcRwLYRl832eZZViWRbfbJUkSptMpq9WKIAgwTY1tuxjHQhrFfD5nuDGkKAocx+Hw8IAsz7eVlJZW+sDzA4zRWLaNVoo8z/B8H61UsVourLIsgtVyag+Go1madDFm/Z2MUWj970YMk1I+9v0/+KFv/8xTr1w+2D/5quHG8JPdfho/8Z73/uLf/uCHfuhtAz2dTXue681ff/0mg+4QWqjrGiybupX0+j3AIGzB9u42Simapk/TtFiWhed5gEEpRZFnbHaHTE+nfOu3/vXD7//+HxDdbp/RcBPP91FKcvPNN7rPfubpNoiiv+553s8ZKXUrm3DQT9vXX33etWyunbt438vbO+dxHMtRWnk9d1T8vwHur/zGjz+wWKyiGy/dfOr3fvePmI1zdO2itSAIBu9+/oWn6HQ3X6/qkjCI3h7Qg/5g/saNN7p13f5S0ul9kwGkBmMMxhiapqFtG6qqQhtJp9MhDHtYloXjOOvl3bY4rkViQhzHYXtzl9//w9/nO7/j75jv/Pv/tbh960Z4643Xy6/8qq998Ef/4ff/7N2j43cnSYcw9H+320u/Wwgz2tvZnkRRNGvb+ok3bt746aZpv7037Hpb29vPXb74wH/X728+uzHa/b/W/3VO05b4XkQrK0K/Q1lnOJaH5/nUbUlV57RNjbBsBIJ+d5NWNrRtk3762Y97T33mDy/ats8f/9Gf/Mwrr7z2WD7PsJSFTUjk+VSNZD6bkKbxtzxw//0vtE0twiAyb7szfP3V17rf9Z1/72Obg/4XO5agNxhSVRVJkhBFAVorjDG0ssZ1XZRSGC3wfAchBEWRobWkrmssy2I6Kzg5HpMVM9q6+L5eP+XRRx763tl08c35Mv+vtOARy7FZrRbr2rytUK3E89a/D0tgWRZ75/cYDgeNH0Wv/Yd/6a88urW1R9NUIMy5JOnuK62MZds4tgvGYNBI3Yo46Josn6OVxvd9wqBDXiywbZcXXv4TlssxVVVSFEX0+uuvfucnP/mpr3nl5dcfa1tF4Ef00y6rRUadS9KoR6/Xo5AZs/z041evX/0bv/o///btz2pFb4ujX3/5hYXvu19s+x51WSGlvFdH27ZAa4XjOAjLUBQFVVUgjaRtFUIYHMeibjR1U7FaLfCcAXvbe6xWEUfHb33v1mCTwzt3WWWLn0ujGM91qeuc0BGk3YS7d+e0TUMroWkaYr+D7wYsTubUy8JbLOePHN3ef971gx9OO/EPpd2I4cbmi42sPqy0eb0/Gn1GuFbkB/4kSXr63V/0HzR5tqCqS5577fdw7eiBKm9f8ZyIO7dvmf39W5wcHnHjxhssFiuqUqIlDDoj6rqmKRUbvRH+KMSyLJSWtMWSOOL9vZ5zzXW922+boz/1ex978uZrrz0Z+96aby1BWVUEQXBGDxZZtrpHHUqtZ7dSa5CrqqKqS6qqQgjDfD4ndC3SqMt7nniCyfgyp6eHnBzN6CYptgNpGrHSklmxwiJhOOxjjKCWLVVV0WSSsi7ppT1UpQmdkKPb+4+sVqufE8LQS1MGg95OGAdfGcYRN9WLpIMOVV0z3Nzgxaf+gLt377J38RrzLGO5KJ8ultVjb7z6JvPplHy1QsuGxWLFcDDC1gaBjaVsHOMRuAGO7dO2LZtbGzgO9DdcXrrxGb76q7/uxun4LTZG598e0Ldee+l7j+/c+t7pySmbWzsIIbDMuiQLwxAhbKqqYrVaUTclSbJW6bSGpmkBQRTGGA3zxYxOp0cnHuDYLsssIwhjvuRLnuDlV17g7p0bGGA6nuG6LmnSJc8rhOXgBh7ZtMZgoy3QSjOeLnAci7Zt2RgOSZMBq9USVTYU0wJaCxcf2WpyWaJ0y42D18llyeXr9/HpTz5L1cD+4cljk6Mxw24PXRtG/Q1OTk64cP4ydd2yvbWB4zjUdQPAcHNEv9PDtR2iKETpmv3j+bcknYS93Qv+nwbynwn0jZefZXo6ZjGZUOUFo80NmqahrmuCIMBxHOI4JssyXNel2+2ys71H07QcHR2SZRmT6Sl5vqKu5Vn1sY/ruji+Ra/TxwlCPD+gkgZbayxl8PwIFBR5wWBzi/5gSFlbZGVBS45UElnXhAS4XkhRK2RW0TQS00oaBFYksEqFMRatavB8ByUtLOnx6otv8ubtAxZlzWJVsLuxRVs3eJYDWGzvniPLMnqDAXGcEkURYRgCYAR0Oz1CP6LMV7St5uDk9Jvvf/RhHnzgnb/0ObXgRrcIo7l6+RKR5+O7Hp1Oh6qqqOsarSVgWC6X2I7g4OCAplbYtkvbSsqy4vjoFNu2QYDvhzSqYLjZR9hg2TbLZcZilRP4EQhJuSxIhYdUGseNyPIGy6koa4XnJbihoW4bHN9HOw5l09JKgzCQpj1mywlZWeFKhed55PmKPMuoqpLhcIjQDod3DsgzyXyZM9zYwrZdZFkSxRGDrU1wbMJ4XaLVbUOzbGmV5P7772ewMWC1LJC1xHZ9ivmUIEref+36gxRV3nxOQFuOS9W03P/QQ2Rlw/HJmCAIsM+UOiEMg8EAW9hsDDYIQp/5fI6SGse1qauS4WDAxsYGSilOT0/xAp84GRAEEVIYGiUZbGyztbfH888/z0Iv8a0WrxfT5AWL1ZKszlHSUC3nrPIl0mhq3azppc4JHJc0ThCOwRYQeC7CaJRs0EqhtWZrtIkxhnE2Z5LPCZMuu1FMlhUcjsdcPb9LWRfUZYHtOnTjiEW2whIKSzgkgY+tFK50sbWDRqFoWRUT3vHFD/Bdf/dHRdvWtLLBdd5G1fH93/FNX9NUNqs8oygKkrTH9OCQzY0NPM/jpZdeYjQarGe+MdR1TZxELJdLtNZYlkWSJPT7ffb39+n1ely6dInL166yzDPyfN1yO75HfzRktVrRSE2rFMJySDodpvM588WCJI4xWlBVFb4fUiwXtFLi+SGWYyONptvt0pYVQRChlEJrOD6aoLVGCEFZK8bjMdN8im3bLFYL6kqT5zlCSY6OjojDkHxVEUYRZZFRNg39fp/drW2EWe8fSlo0bctsNcWPLJwAvuWb/9ZOli9I4u7bU++mk0PCKH0uXy1YLNb17FNPPcV0uaIsSy5fvowBZos5Dz/6CHG6BngwXNfYjuPQNA2e5xEEAXVds7m5SRRFtG2LZzu4aYf5fM7xwSGe51FVFcNen8nshF53iJKabFUwGm0i5RqQ4WiLOImob97kdDKmaSS9Xo9svqQoKorFCqkVTdPiFWt663Q6SCm5e3iMEIK4myKVYTI7QCpwbQeExXy2xBU2c73Asj2SNOX6/Q/R6/UwUqGkpKlqFosZRZ3hBjaT6Qlf93Vfu/uOR9579DnJpL3eJvc/+q5fnp5+jI2NDY6Pj1ksFnS6PZIkYbFYcP36dW7dfpObN2/ieQ62bXNyckLbttR1TVEU1HVNv9+/Z3clSUJbN+RlQVVVtG2LUgopJUEQ0Ol02NrYZrXIyLKMJOlR5CVaa/KywfEagiAiTXtIBU0tqcoW1w2YThYIpVECLM9HArXSHE+mHB0dEYYhu7u7FHnJ6ekpRVkihI3v+wz7I0LHI88yut0h99/3MJeuXCZKE7TWtFVNWzeoVuIWY8gkdZMx2u7yrnd92eHnpEcrJTFG8/ynP/FuKSW2bXPnzh2iKGa5XHLrzm263S6267C7t0eSJHi+w3w+5/T0hKasGAwG1HW9XrJlSRiGNE3DnTt38HwfIQRSSsqypG3XCtxMa+q6Jl+tqMsS1w+ZzyccHZ+QdDvr9j6K0FozHA6p6prV+JQgCPBsB0sIbNsmiGPSbhelFLMbN1gsFoync5544gG2tra48eqLZFlO27bYnotlfMqyBMcw6o+4eOEy9913H4vVEjdYf9ckSSAyLOcLNpIhm+d6PPOZT/FXv/7b3rm3e/XtC/9VVRAEEf/4Rz5k6rrGGHOvrba15tFHH2W2mOO6LrPZDK3luv2e1WxvbxPHEQdv3b2n5q1WKxzHYTQard3wKCIvCpRS97IiZVlSliX9fh8pJZ0kBTSOZ2NZMBwNkFqTFSuMZUhGG2itUbqlrkuWS+ilnTVdCJuok5JEAVprXFuQRAEXz+/hOdb6ZXlEXoRt12hjqKsCXSvifshykXF8fMzTTz/N5atXzmRfD1k3eK7L1tYWuZqTVzN2L2zzvi/7mqePTm4ThenbA/qzG8n5i/eLw5tvGcuykVLSti2NWtfKO+f21ryYZRwdHbDMM5q24mQyptfrIs+o4LN+YhAEzOdzmqbhwoULGK0p8hzbtomiCMe2wRgc28ZojetAKzWOY+EHNhpFmdcsVyuELchyDyklTVOCUEhVY5C0bYXSBr+KyFbrTraTxljCEA56+J6DYwuqqsH3Q5IwoWoqQj/EswJc4RO5EWjNarVgPp/ihR4XLlxgazSkrRtsy6JdFSg74vv+9k8JgO3Ni29/RislmU9PAPMxy7JQSlHXNVmWschKopdf5sr91+n1euzu7tI0FZ/+9KfZ3dtmsVjQtg1XL1xi0O9zenqKZVnYtk1+BuwLL7xAFEVEUYQQ6yrCdV08z6NpmjP9G6oyw6Bpmpq6qSjrjFW+pDEtQq95vaxyQNM0FUWR4QiBMZq2qmirisB1GXS79DsdXNclSRIODw+pipq8zEidlEGvT5Kk1KsGIS3CMGQ06hKkPto0NG3BbH6Kakt816OtG97af4vBdu/z8wyP9m8OhW1NDg7efH8lWyqlyduaSrYUdcXR4T671y6QNwVe42KhGXRS6my98ammZd95i16vg9QtQhi0lght1jt307IsZwip6ff7tFIyns5otSJJErI8J0wCbt89YDjYwAgLqRxkaxN4CZa2kDKgyCva1sdIhVYt+bxk2OkSui5e6CGFojEtlm+zmM3JxyVCWOtNsC1YFgv82KE3OIdWhspU9IYjett9/CTBcz2iMKSf9Oj4EbptWVUVWZYxHR+98Je/6a/98OcFdJR0J7/wsz+wdXx4G1yHStbkVYmxLYIoRGFwXJemVUync27fvMP25hZlXZLnFn7gM56eUtYZO1u7ZMsVQtjMJ3PiOCZNUxaLBUVVomcGPwqRRlPVNePJhEa2WK5FUZX4QQmWRVXVKGnWdXTdIKsZjVQYocGAkgZlawSgjSTwHIQFFgLHcel2+4DF7TtvIZWibdcrJ8sLXnv1dSzXI4pj+hsjdi+cZ2drG991oW3xHRvZNGhhcDwbaVqC0M8vXb7vn31enmFVFn/14M4be1JKlDIUVUlWFtQowkFKb3eEkjZomxeefZmmlszn8zUnJwFlU7K7u03btixWc+ozU0Ca9eds28YLA8qmxvJcyqri7uEBRoDwHBRrJ717VjWUZXlvQ/Z9/0z3rjBGImWN1C2ut6aMrFgxW0xxsBCtQVY1spZYlsX2zi67u7vEnZQgTAijlCBIwPJQUuB5Ea4TknYGKLX+e5+lNiFAqRatNb7v8uQP/tgTn3fcwHXdfy60eSoIY1rjMhgMWFUaL2/BsWlQTKczqlUFCHZ29hiOuozHx1iuwfYEB8eHjEYjXNsl8Hzu3LmL5/kIf11+JYPe+uEIQ4vGi0PypmJV5AwGA0LfZblc0jQ1GjAGlAal1LoUNA3CcmjaEtAYx8Y2mrJWxGGErFo8zyP2ItwwoG5b5vM5xrJxXR8hbBw7wHI8jBEgBLI13L6zj9KCbhqxtdHHUgobg5YtQRwgZYVlf34e5f8BtBfEX/zur/prr7zwyZcTN0F3AgaVBjunRXM0PsWUd6E2jAZdTk+PqeolYeLjBg5FW2CMQcr1TBoMBqSLOcJYREHIapUzm80Ybm/eK+vszGWxWmI5NrPFHNKEqqooyxrX92maFv+sGlpHiiuEEDRtg2ULWtngOzauHWC7HstVzqDnnTnsBcenJ8xWGcs8oyhrmqpFCBtTSaRWLJcZnh/RmhXyrbtsDXuEnksaekRRiBAG1xOEccTJ+PjPB+g8WzZ3bt94n2U59IYDggSM5eP6c07HU/pRxCjtUa1yLl3aIfBcZssJIMmKklWxwg9clJEsFuuOLggCiiznZJzR6XS4fPkydw8PsCyLyWRCURQYpdFn0QNXcAZ0RV6WpGkHrTVN06wfoAFlNI5t0xoNCKQWLPKSVVZyao0Z9Of0V0Ns16GsW/KypqwaWrUuO8u6oqgK6rqhair2jw6JooiyzOlEPrZtMxiMGPZSQt/B9iErF0hV/fkA/dILf9CeHN96Zxz1mExmOHaIi8Uo7aLqBgeDoGaxOuGZz5xw/eo1lJEIx2dZrCibgm53hySMqN0az/PW4cckZjabkWUZcdLDsx0mkwlaKhwEtu+vzdy6YbFYnNGEpFWKy5evMJsvybIMIQS2sJFtg+f7NG2Nbbn4foAwIJuWUtcs2hqqnFDELPMV2ZkcYIwga1a0bYvvh0RJgJ+EKKkRNigjKYoc9ywXvlgsMKnP6f4Rji944OFHxZ8L0KONHWdn7/LvzsbjvymQOI5F4PskkUc/7aKMJK9yrl85z+H+AatsTt1WnOvs0R/1sQuXyeSU9MIFbNtmPB6vTQLXR2pF3daY1QLPDYiC8N5MNcZgWRadJGE5b3Fdl04nQBlD27b3FDghBAILJQ1O7EGj0AhaZdCtpC4b7FCwrAoaJfH9AqXMWdDHuacqWhYIG6RssF0fYwvatkEpSVEUFEXBa+NTQs/myuU9giB4cJFNeeSL3hsC5ecN9Lnz98kkiX+4XC3Z291FGxupbbSycD2fum7xCh+FIYoTxuMxx8fHKGlhWsVeb4eFmTE5mLCzt0vt1hipGY+nSKPB8vD8kKLMCMMQaSRRFNDIFmkU/VGf6XxB6IVIrUnSLlleslxm+H5MWdQI28ZxPISxcFpN4DjYSuOHIbUBZQyBF6KlQhctRms828YIQ6s1jdagBbawMNZaBtDGgABhWSyWp9zdfxPPtRDdmFIUxFG4/Hv/5Y8e/LlFwl575dNP3Hj1uZ+s65p19KoBNNbZJ9YzUNI0kloqtrZ2uH71PrY3d7h8/jKWtkjjFGGgKkpGgyFKrWelbNeikdLtmg/r9fINopg47eK5IRgbx/WpG4lh3ZmuVjl13aKkOXOdNUasqxDLtc5owCcJI5IkotPp0Ot073Wfbdv+n1aFZVlYjn1P9DJSgTH4tkPgeuR5zu07byJVQ2/Yx3IE/9Ff+k9PWtmgtf78OXq5mGy6rv8px/Gypqm+bjabPaaNTXcQoFpz5qgIgsCjqCvKbIWNYXt7E9uy1jnpDCwjSNP0TI9o7qX8HcdZ18FtS5qmGGGjtaEoSwwWGIeqXMulVVXheR6u6699QGNQukWqllZKEBocn9CNaKoaP46wXBfftjC2hRaCsm1ojUa4DkYIzBnAviWw5TpnopUi9AOaRiJaRVPmKFNz585dotBnd3sD1xPMFxN3e/u8LJucOEo/P6DzbHFy7sID9Iebz4+Pj6mbivHkBGkswiAB4ZJnBY1scRyHvb09oiBEyTNeW2VUeUGrJa7rssxWCCx2dnaQUlK36mwWGabTKV4QnZWBDlUlCcOUtm2JowDbAqXMuhQzFq69Ds8oDLZj0Npgn/GqEzgosy49XdvBiwJ838fyHDAKW9hrTVkptNL38oSdTgejoMoLtDSEgYMRNiJO0LLm+OiUV4NXeeih+9jeOu+//MrT9bVrD39eU9p+8sknSTt9inxJtpr92snRnQ+ul7wiywsc22NnZw+tNEEUYAuBEJBEEZ7n4TsuaZqitWb/cE1lxycnTKczirJCa83u3jk2NjZo6obj42O0WVORlIrZfE4Y+iil8Lx1hEHgoJSmyCss26YsC/r9Hp1uRLeT8tmlnCQpBsFytcJxfYyAtLPOcQjLQlgWlm1jOw6O6+K5LvaZUogRuJZN4PpsbGwQeD6W72DZgs3RkH6vSxJFfPKPf/vDb9568UfTTvej585dLT8voI+Pbn/Z1s7FO2lnsPPcMx973HP9HcuyqRtFGEbs7x+stdm2RWtJEkVYlqAqckYbQywBURgw3NhgPB4TxRFRGIGw1rJqXjCZTEALfC8gSmKM0UxmY8bTU2azMUrVzCanWMIijTs0lWS1yHAdC0sASM7tbtHrxJycnGALG98L0GeaRxiGhHF4lsOoz0KW3MsCumdAC7P2OV3HxQsC0k6Hfr+PFiCctS5fFSVVWeC5NpbFB9H6+mx2dP1Pnvntv9/tDv9pGCTa83zyYoXn+v/21LG1ffH3lstpcu7C9aeBv+M4zi8j2CnGc44lXLx0Dd/3EcKQrzLatkWclWWqlff+GcvAlStXmMymGA3t2XLNy5qyLJmcTNYhScvgOA5pGmKsLsvVgk7PZTmzSNOYIAhYLkqUMpRlxdb2AK0bHnn4QSLfY//uXYqy5bVXXyNNOnT7A2zLwrNsVN3g2w5hEK4p58wJt+7t6uuQprAswjhCGcGyKZFCU9XtWZsu6CQpru3hWDZNXXurxeIbRe3w6//rz8uHH3hCvO8vfLV5O5x9r+rodAZZtppb73nf13eFEGxsbDAajbAdi+lszGq1oKnqdRCmKM5c6fXTbKuaYrVuKhzH4fLly1y5coWdnZ17vmGapiRJim07a5c8jej1U9JOgGW3aFMzGPTpd3t4jktbSXqdLjYO+2/dXZdqQpDGCRu9AYFj009jbCFQrWQ+W3J4eMjp6ek9w+Kzr3VMTeDaDoHnr3nctmm0Ikhi/Dii1BLLdej1euzs7HLhwiX6/T5C2DS1ZDqdMp1OkVIefPTjv2qyfOG8ber47PjNj/zTb//DT/z6L1nCTsuyRNUVkesSOjZtuYK8xmpbsukRqIzA0ai6RDWSKm9AaJI0Jo1jOp0uW5ubjDa2GY62CIMEbSyqpiTPM4yBc3uXuX7lIbZG2yxmU/q9TdK0jzEOt26/hdKa2ewU2VQ8+tCDXLpyEWEbTo4PWEwW9NINhHZRWtPqEqklRiviKETrtdTZVAUWEIchtuMjbBthCxQay7FoVEMt1x5i5DkEngcokjhCGIVqatqypFqsqJZLHC1SV4j/JMsmyUMPP/4HlmW/fXP267/xv/ip557+/Z9UShH5PlGvz507d8mW+dnsVhT5isn8mLQMgBKjLZJkhOskuH6MLSyklFAVSClxXA/XhuEgQakLbGz2OTk55IUXXmIxz/G9mAvnL+H5AidMkdJi8vodasvg+w4NmsB32d7dZmN7C9+1GA6HHLx1gpSGxTwn6oUgNFEYo6WhlZIoDJnMF6RRjNSA5eD6HqpeK4Ou6+J463bb9jziOIY6pylL9i6cIwgc0jjExqfKDBUKIWzavMSxokemx/vfkK0WP9/rbxy8baDPSAzbtmm1QknY3NjG91a88eYtZDmn149JOxFe7ILVYrkhwtUoKuYnFb5fYHsuSRJxeHyE7dn3MtK226HMl1w6f4l8WXDz5uss56fMpl0c19C/2GWSZejQRXuC0+WEpN/h8rktwk6C67po3ZIkCb3BkMlpca9WN8awWizx/fCsNRe4XgSOj1Atru+BI3AsF4+13p2v1l6oLSzaosARiqbKGJ8eoroJgTcgCTx83wXjoZuWYrGiLHPKpoz/xa/8xMG3ffB7Prfjb03VEsfBOsSNg8Bl4IRYdsBqcYTn2wSBgxc6KFySOAXLxfdjbC+i1xvgOBZKN1hC4VmC7QsjQJKXHmVe8OFf/pX1w5Q1ULJaHdM0Dc2bb3D5+kPs371Dnq2wtQHTEnkuW8MecRxTVTl75y9werLk5psvk3Q7FG2J7bi4oQU4WMJDGlDGc9xwGQAAIABJREFUAsfl+tWr5MWKvMmo65q2lri2g++6dNMEz3WZz6csiimuI3AsRRS6hL5DFHjMyxVZsaLvd4n8gFI35KvskRs3XjA/8EN/K/zW//y/qX0/NP3u8N8M9G/95i/Fn/zdX/vPqqrB6Jw4TvH8AM8NqFH4oaJuh3iOhdQtlgpIeyP8IMZyAoTt4tkOVa3wjEBYguFoxPZ2D9ttEFZDt98FLfiD3/8EH/rQh/jyDzzBeLLPs88+y9NPPc/+/j6nd0/x3BhRVoyGI1RdkfoBl7Z3UE2LOnNdymptS7Wtupf0VHWF6/qURcbG9h7X7ruOUhLX0vheF6tQWEKzNRixnOdoqSiWK7xuwtawTxFoxpMjAn8TgeHk+JCFYxMnIZ1OB1UohGXRVBVxN8G1LZbz2WAyOTp4+MF3oZTEtp0/HehXX3rGu3DhgfJXD37u240xNK5AWAFpJ0TYDq6wcJTLINilLmqm8zmLvKE1NZ1egCVq0iTE9WxGgwG+79PUGct8SYvGEgZNi+eUvPj8p/llafPJP/o97rt/wJd/4N3sbHfIlzlROCYvak5O5/TjmF4YYnyXjWEX33Ww0y6eahifnOK6LucvXeLW7UNcO6CQFall4whwfY/p+JTxoIclDKrNOTp4i2vXLvHIA9dx7AjZaIw0GNPiOJo8X+LaNbLucG57mzRNmZyeINBEYQchBKt2gbbAD0MWiwXTYsbF6w//Ypr0vgbI/kzq+PDP/8T7bdv++P/yi//kA0UpH2vk+vTr3vlzCNtDWFA3zVl8YN2OV61mPJ5Ra4dKrSVMbTns9XcwrosfJ0yWMw6OT1EiojdwCAJNkhhct+Wnf+ofs7uzyfnzQ45PXidNI778/e/hx3/8n2C76zyGEIbpaoYQhpKWg8Upe90eCkO/36fT7/P0M58E4+E4Nq5wSS2JZdksVnN62+fwPYemKqjLDM/SuJZh/+Yt7r/vEaJ+n7JumE5POJ0cIoSmylcErsditkCYtV3XiROapmEymeAEPkq1+F4Mvo0dWJwe3nqP6zjZZ9v7P7W8e8e13cHFyw8cPvVHf/h3lXIeb2u1DqMEPkka0+33yIoVebnEDzo4vstytUJhuPPWbbAEcRIjUQTRWpGTan2U4uT0CN+3iRIPzxfYosLGJ1+2vPc9T9DpQitndNIUWds8++LrNNpQSYmyLYTvUZuW0c4INwkYDrZo6oaDg7t8+lPPUJYaYzmcnB7TqJpyuuDK+R2COOVH/tGPcvP2Td648Qobgy5XL+2RRgGyapnPVuvaeDZnvpgymZ9SNQVtXpGGCXGcIFXLbDZnMZtT1w1ZljNfzlDCIFVDmARYwN07b7380vNPjd/x733JY3Hcfe5eY/Svz+iyNDz16U8hou43yEoyXxRkWcZ4WaFtn8FwB9+NkY1CViWmUbRlhWMEkedyevQWlinpDhJCV9BLElpTUJU5RV7x/Iu3SQfvIEwjZtkK5dU8/v7rJLHHomzZ27uOFl0+89LvYYsew9RHmwmtMFRNgeto5osJ6Is4UqKblsiNqUpNlq3Px/Q6FrvnOzx63zW+7D3vo6lTbKUwWcNOv8eFc10ee/w6keWSZzUvvnIbjeLW3Tu4vkcaRihdIV1Fb6OP7dl0k3gdXdOGOE7xsxx/KZCqwXUcVKtRRtMq8cjp6dEHPvw//fT3fcl7P8ATT3wldbPOkniuT1HllGWOfXV36+Dw8PDJ+WqVLrKCqq5wrHX0tm0aXMcmDL31AaBCsZznRFGKVtDtDCiygtPxBCUVi8US23KZTWeEQcxgOOD45IDVas7Fixcpi4y0sxb0bccjCHoo5fPSi7f56Ec/QZkZBA5SKoQjaNsa2dbotuH65cuc2zhHXTXceP1N3rz1FmHSocwLksTiXY/dz1f9xceJfIc4SHjzjZs8+8yfoGVGGCt6PY8kCvHcgLxseOjhL8ILE9CGtl5rG7JVDEdDfN9FI1Gqpqnrs6yg4PDg9lkmcIjtrN8Lg5AkTd/V1PmXNk3xB+981/vHju3e2xQtYeHYDlZZ5FRVSZavqMsVaRigZIVlNN00QbctgevQCdf2kzGCxWIFxiLPWiwiwmBAv3sOgc1HPvIRDvaPmM+X3Lm9j5IWb9445Bf+2b/kzTfGnJ6URNEmtt1luZQ89dTL/Ppv/CvK0hAnHdJuhyCOUE1L5PnsbWwRCY+tzojAXevVN2/fYraYUlUFwlnvEY888g7yxRLZ5Lhuzu6OzaDfYPSYq5d2cDCUuaaVNnHSp6zXJkan08P3Y/JlyfbWHlHYQSvDapWTZRmWBbP5Ka0s2d3bQ2k4PZlgWQ5xmHDp0hVUo6jr9t23br3qv/bqs/dXdclyNRMGg207OK6Hff+F7Se10GCB69i4tlhnjWWDkRIhNDaG0WhAt9vFDzzSTrLWEaRcHxpKOvR7Q6o6Q0rJyfEpx8cndDpdbt26zWpZUFeS2WTOjdffYnyy4o0b+7z6ym1eevEGaTyk2x2RFwVBEqOUZDadIQSMOl3K5Yovffzfp5aGZ57/DC+8+DxNq8By8FyHMLIRVsv5zS6qLiiKOefO9dnYTLEdhZGS7c0d+sOL/O4nPk0jBVtbF+l0uoxPx6wWS+q6IU27JHFCGASEkY9qW5qmZLlcrFeX1uvo8RkPV1VFVVYYDKvlksVq+cBTT338I8899wfTr/iK/xj7rD1vmhrH9WyauqKVNU1V0jSS0I3XKR0tWSwW2EIRxT6dQRfXN3TiBGEH4DRMJznHp4fsH9xkc2vEYDAkChOaRrO5uY1lWRwe7nPnrVtnNBSSFxZ5XhCFHR58+BxV2XB0dEzdruNeZV2hMbiWQ1E0BG5EJ+lSYzM+nbLMMmqpCd0Y23VZ5TOOT8ccH8Vcu7xLXs8pm4q4E7KxMaTb3UKIgI/+zh+zyiXXH7yM0obJfMZkMqGq1lECgc1qlaMjm42tHknoka1mjDaGNHWLH0ZoBfPZjLKs8X2fw8Nj4jjGdwPaevX+2A9f003zfVVVPClla/V6Iy1lg/1ljz/8ZC1r/NCnqmukNKxWGUYIfM9HCIuqbkBAEDnUbUFerFCqRliCIHCRWhJFIZub22AspNRI2bJYzFku5xhjeNe7HufatfvZ2NhGSs2Vy9c5d+4Ce7vncZx1DKvb73A6GbNYLlFGUVclthEIbbhy5RqNsXn+pecpmpKyaTBY9Ht9fN8mz6fMJhMsy0W4AcZysdwYTcjdwwUvvHSTZWboD7dQGtzAZ7GYMx2P2d+/Qy/tMNros7OzSV4sqJuKIl9hCYPrerStYrFY577niwVGa5IkwUiF57isFkuyfMlg0Me17fc/89THn7x987knH3vXB9Z6ype/54uedDyXWjYss5wwjImTDhiLKOniOC7TxZzVIqdRLbbtYDselmUTRhHdTp+6URRFw2Je0Ov1uXjxPFevXsH1LOKz+zsuXrpAEEaMx3O2t3dp5TpFWpQFi+Wc/YMDlqsZddOgMSitcD0f1/OJ45her4cbRNy+c4dVsaRuW1zPR1gOQeiwsdmnKlru7I85Hq94/Y0jnn/pDjdunrAqQOExGOww2tjiwuWLTGYTjo4OOD68S+C4XL16kZ2dbY5PDuj1Uk5Oj3AccGwH1w1Ikx4GcHwf3/UBwebGFpawmE1mlEWJH7jUVUVVlqi2Zb5YfO3d/Vd+9oGHHtf2+979jidbJdEC0u6Q8XSB63nYjk9VNiRJB8tex6KKrOb4aEpelGxubhNFHWwrQEobo9d3Ktm2Q1FkeL7Dzs423W6KZQkWixlRnJ4FZBpmsymf+cwzzGZTTk6PmS+mSCkpypKyKu9dG2QEDAZD4iSlbhSvvfEarazJihLHD7Etaw2IA4GfMto8j+OkGCtG2B3q1kY4Ia4fsbN9jqSTcHh8yDPPPs1kcsrpyRGbm0O2N7fo9lLOX9jj6GifXi+lqRqUBIyNZTl0Bn3A4HoewsB8NufqlSvIVrJaLImTAN91cbBwHQcsseMF3ndXuvg+p13WOAoGVsxCNXiWjecFLJqKxhYs2pZKQ6AtbMtlWWWYlcPzL73BpUuX2NjYojfoMp1PKKs5iJSLl65Q5BVv3TnC8wJOjtcHgHTlgRAMR30G1wZ0+h0ODg+5c3SHWrVgPPJWoRA4loNtQxh47J7bQXiCfifFkhotDZ7noE2DG6Q4fsrB8Zy4G3LxoasYqeh0OpRlcU+8Ekbjui7ZvODNV27T5IbxeInnJoynC5LOKWHos5ye0ks7KFUTJyGO7Z2lawu0MXiex3K5wg88iiLj9sEtsBU7lze5++Ytet0+ynZYZAs2zu1w+84JrfWMcaSU62MDbct0PKPX6ZJVDYvVCi+KGS9mbAz61FWFbRRb29vrs4WNZDpbYDvrowwXLpxjfHLKZDLm9ddfR0lDECQ8+MDDyNYw6G/g2oK6rqhly92b++vguJT4vo80GsHafcmXBd1OglYtoeevY2BOzPbmALTEd1wa42EsG2FDFMf4XkSn00OWitBzQSpEqzg9PESplqouWBwfM5nMiMKENEqZmFN6vS5JEqCMZjKZIIwi7UQIcXYhl4IoirBtl6Zen2Hs9XpUdcnm5iZNW2BsWM5XXL1+BdUYlnlFlPjs3z3Ei0OSXhfH8tf3HlVVgeO5HI0naMtBGHAtm9HOLt1Osr6bYjlHKcXx8TG2bTOdzqnrluFwSJ6XPPTQI9y8eZOjoyNm0wWdTo80Tdnc2CYMIw6PDwmigJPTU9Jej7ataZsG3/HJ2wKlG4bdDr4QoCV5VeJZAzb6Pe67co35fEIcB+SLDCkb3CAkDDy6nYhsUbAcj1FZjmxr2rZh0OswHPaxfZcCzWQ2oalLjFpbU1vbGwyHPeLEQ6rm7Iheief6CEtjjCIKfYwRRFFE4AukbDg9PSXLV1RVxuUrF5GyoQ4a9o+PcByPOOmCsTl/YW99FHC1xFkV+fpQ5dmNMXEck1UNTdNQjMdoramrdeqzyFbYtuDKlStn517UvQNBcRzT1uubaDzPx3XWpc8nPvFxRqNNRqMRYZqwvbtDOugReD7Hx8fMTheEUcDmYAPXWXuQpq7JFgVCah558CEu7Z0n9j2Ub1NWK1zXxlEOQRCQRCEbwz6xH7CcrNaABH1efukFqnqJNhV5nhGFPnWZsVguCPyIre0RnU5MEDr0+h3iOEQ0hnm99kUd67PH9GriOEVgMR6f0ukkpGkKwtDvdzFaYFs+3W4fx3c5PDwksgR106JWGYvFgqYqcRRmDbJWa0dbWAhtCFwPJwgJ/YA4DCmKNd9dunSJKIoYDAY4joOUkizLeO211wj99YUhZVlSNyUbG8Oz9HzBrVtvEnd7zJcLOp0OWiqiKOH8+YvrdJLjUlY5h4f7/O9VnVlzJMmVnb9YPPaI3LEVUF3d1SvZ5JCSqJkHafTX6rfJbMYksxlyRLLZZFVX1wYUgERmRkbGvrnrwbNA6QGGR2Qgw92vn3vOd7u6oe86TlZLzlZLTlYL4tAHY+TJ00t+fPkSQyqE5eDYDnWRo6SkaHO2xZY4Dvn2H74FFH3XUI4lInSZBhaeLwiDhK+++oogCFiv7xjajp9vP/DlZ9/yzTff8ObNayzbRimdM6zrhrPTENN84MOHD9r7Hcf4vs9ms+bk5ITtdssgJfF0StO2OE6AKzxcu6Fveuy2bR+DlXEcozA5Ob2glSbRZMpyuaTvW+YT7dZ3HIcgCLi6fPoYc2uahqvLp7iOQ5ZlDMPAzc0Npqn7h+/fv+fnn39GFdqWUBUlq9Wplg+Fg4O+Rldpzah0pF24NlmWUdc1WZaxWMywK0FRFICJbQt810dYDn3Tk+42NGPHdDnDcRyiacJ0FlGXOdNlzH6/p0pLJpMJnz/7ksVCwwBWq1Pu7m9YLjSA62G9xXGcI+fPpmk6wiBiv9d6zSdrRVVWGJhYpkOR1yzmJ9i1YLvdUlQN2X5H4IUslyds7u+wZ1HyaJWSyqKTCmyHD2+v+enNWyzLIg70m3p2dkZwTLBeX18/Rss+mVZe//QTd3d3RJF27i+XC66uLhFCo9gcYZM+bHjy5AmnyxVV0yJcwaigaXukAaYwEa6D41qoseenNz8hHIOnzy5RShHFCb5XMmCSxEssJejbAWM0EIaJKSWeaRD5AltKZNMS2DYlI6aCJIp5cn5BGMa8f3eNLWzOT55Q1yVhGLFdr3Fcm6HX26IQ4tirhL7vieKQ/FA8kni6riNNM1w34+zylPtugyt8LPQusEtznGCC9Ytn5y/quqYsS7a7PXf3a3a7PU0/avRa29LUFavlkiAIdCzZcY5/XNe6QugDVe/PDpvNhoeHB25ubo5eiI7PPntKIHzOT85QUlHWDaZlM0pFO0q6caBtCg55Rj/ow8xQitPTE5q2BgO6fuDd+2vadiDdV5iGxdCNyL6nbzsCVyBQrD/e0BclbVGw3zxgjQNPz8/51a9/w3y2BAzkaJAkEw6HnPXDWnfFDUuHj4oDfd8ihI2wHaSEyWTKdvtAEAbEcUKapmy3qSaOtS1ZlhF4HiYWN+/vKKsay3YBm7ZvsbO8xnMt/MDDcFy8OKQdJfVmR1t3NE3H5cUlT59c0iuTw6Hi7Ozy6DQKCY7GQsuykBIwBMvVKZ4r6LqWPEsZBo1kuL1eY5oWm8Me0xUIL+Lm4xopDa2WHSrdlmpyHGFqIWsa8d03X3N+uiI/1KgRHaOrahynoBOtPijbluliwsnZCtcwqMsSGQZ8/vnnnJyvsI6rbuwVbuhxd3tzdK9mhIEgDATS6FGmBAvi6Uzn1UdttwviiEk857Dd8eTqiuVySdPW9KphNBqWZxP++OMPfP/L37A8PaEpW5puwPUC3DDEPj8/x/UEw9AiBkXVjezu11iWxenFOSeLE85Pz5klE/rRYHV6wn6/Z7X6OzbCMAxc132MqpVlTl1VgOLy8hLf9UjTlIuLC25uPzKdTai6losnZ2y3KUNv0Ba1XiWm4uLiEsuUfPPVFwSuxWI2w3c9ek/Xtsv5AknOcrmgrxqauuRstaSscv70xxviScTZ2SlffPUlljCJk6k+tJuSKIowDZ3qvb+/Jd1vMQzJ2fmSrtM1fd/3rFYrzVv1dLa8LEvydo9hGOz3e7I80wCBcSDPSy2EKYM//J//4Ne/+DVbuUcZHYvFknWWYf3jP3z/wnFsXFdgWi6uH3B6fs58ucK0bJq2Y79LGdqRvCi5vrk+4jJDTk9XTCYTTEs7TC3bQKqBtq6oqpK2atjcb7i/XxP4IdP5TJd0h4zlyYo4iHn/9gOmNBkbTXWp6lJ75QxF39T87re/5fL0HM9xiCczpDI4FCXCcZnPZgjbwhGC+WKGHxhUTc7z559z+fSK2WLGfD7HPArxSRixXq+Ro9aJ+74jCHyqqqDtauq6IY5j2rbVEIAkoTqCAlzX5exkSV4cCKNQo4Sahr4fmc7mVGWHddxmqrJmdXKKcBzyosAJPOxPbnjPc2GAppc0TUfd9Uhl4PsBi+mCKAip2w7PcyiKA0UR6VO5rQkCHVGrqz1pmrLb7bi7ueNvf3tFHCR8/tnnvK+uGY23fP7lc87Ggaqp+Y8//AFzVMyShD7rSPcbeiVJN1t8YeOaNkpaZGmObRooP2BQmoowmcRUVU6WZzw5O2dxukAqm3juEcY+hi2PvjuFMkaGfmSQUpdimxQwkVJS1zWr1QpbwO3tPUopFgvNU91sNnRdh38sb/u2wvFs8uLAZDbH92JuPm4wjRpLuAgXHtY7ojDm1eufWCxW2I6HMY5Y//13/+mFHEfKqmDAZj5f0AwDzTDQdT1dN/LHP/75SJBpmU6nx73Zx/Uczdkoc3a7LZvNPWVZ0tUtlmFxcX7B97/8HtO06LqWZDFjm+6YLxYkkwQhXL5+/jWzeIYc4OHwQN22VEXJ+fk5Ukq22x2eH6Ckwe12y5/+8gMYMEtiijzHD32++e5rrp5e4fsWk9kEhUGSTHFcF88PsLBom47r6/fsdilDryGyhgGmZQASqQbu79fYto1/7Cb5vs8wDEeDZoSBIs8PCM/TqLeq5e72AUu4jIPBqEayPKfrB4IwZP2wIY4jsnSH9WQxeVHXJckkwXY9yrqlbFr+/Je/UtUNJ6tT/uvv/pFpMmOUPe/fv6WqKoaxx/d9iuJwhL7aTKcJi+mc5XLJfDYlCkLevHmNME0MDETg4YUBZV3x/voDTT/Q9SNtN9IPktGSuJ6Lc2RlVG3Dv/37H/if//IvbA4HHnY7fnr9MxcXZ8RxwCgHur7FD308P2C316yQsmoJ45jA16WY6zgMw0jfdRwOB7LsQF03OI5AKckwdAShh20LyrJ8ZPg5jsPd3Z0mnQGWrXM2m82Womzw3ADh+tw/bMEwYRxxPZeiLHFcl8l0Rl1VfP70M+zZdEGcBJiWpG477h82rHcpz549Y75YUpYt//b7P2AomMQ+h8OBk9PVERGRs1qtEMLSDKXjB22qGsuEpq3wXcH1zVuklHyefEeQxGT5Qceeh5Fs98DQKG0m7Fr9oLGWUwfTxF/MdSbGFnjRhMXJijwvsIyRX/3yW7KqQGFTty1eMGE2e4rvuBR5zm6baQJk09J1HVm2J4oiJsmMn39+q5mnpjoGRm3qWgtFhmFogX+/f5QahkHnaVAmQTihqhryssKwLH3AmiYmEtmBZQmafqDcPSAMk5ubD1i/+/4XL7quIS8ydlmOHyWcnJ7S9gMf7x/Ybrasliss02TzcI/rOriuw9XVE8IwfGQqKaUYuhFDGSilAYF+4CHHAcNUoCSdBFs4+HGI7XuMCh62KbfrDf2osB0D33XZ5wdNVG8aiqbBjSKCyQTHEty8e4+wDVbzGYapmM9ntF1P2dTMZqcMvcKyHcJAP/z7d2/Zpyn54XDEDI1HZJrBfp8i5Ujb6uc/P7/QKbIj5+lT2ep53jGLbpMdCuIooR8VbdvTtC22bekV0/ZEccTZ5RNGKQFFU1WYo8Ju2pI8L1isVpxPAhzP0xCRssAeeqZJxN27HxFCEIYTrq6uODs7o64GlKyZTZfUTUEY+gztiBzGI06zY5okmPMl4zBQpBkP92u8IMLAJPQ9osmCblvhTiAKYxzfRhkSi0Ef0KbiYqktZmEYkoQJX33+FMc0aMscORqURcWbn39iebIidEym0yVKwfXNDVXb8Ivvf8tuc8/Nh/f0w0jbVlR1zenpKYciRbiCeOpT1zWe5+E7Ljc3t7R1w/ff/5pX+59xPZt9nhEnAc1gsDvUSKnYphmjVI/wF+E5GF2P3Y4s5ycwSlLrgTjysL5/fvUiTGJsW5Ad9jR1hbAt2q4l3W45ZBme7zKbTfni+ZdgmNR1q2dfCcE4DkfLGHT9iIG2kLmew+FwoGk0wMq0bNa7lDdv32FbNkmYMJ8uuLw45+svv+T0ZMlsrklki/mc05NTLs7PmSYJlvEpwmEwSSJW8wVKDhzSFJA4jk0Y+ey3W/quJ4xiptM5lhD8+MOfeXL+hHHsCYKQvteouDAK2GwesCyDMIzo+wGloCxrZsmEpukwTBNbOOR5Qdl0JJM5bduxS1MwDPb77PEeMQwD/ah/bMvBEy5lkbPbbHj3/h3W918/fWGapob7GQaWZVK1DbvdDoWJZdmcnj0hDGOub26p6walQDvdFYdDRlWVFMWBXbqjGzVy3gt8bj5ec3p2zma3ZRhHwijB9Xz2+4xDnrFYLBBCy51B4GNYJuuH9WMIs22P2ZftlvV6zT59oGsqPrx7TbpZY5uKxWymw0RqxPcCNtuUoqyYz+f0Y88Xz57x17/+wK9/9SvatkUIB8cR1HWDVBLLsvE8fUlJkgRHCPpuJD8cKIqSs/NzLUUMPUrpref29lZjMaLoGDzN6bqOKI4YjwS0bJ/RNjVSSQxGrN9898ULTBNlWcRxSJan9N3IMEo8z+fk9An7Q8HDQ0rXa3E8SSaYpkXbNozjQN3UrNd33G82DIPEOEbWRqWwhcPHu3sGCW03sN9n7Pd7TFNjkYWwcRyHtm24W6/5eHNDfshJdynbzYau7RiHka7tMFSHMEZC3+NkMWcahfiBi1IDZVXStAOu67FLM9L9niAK2azv+d1/+c/87//1rzx//iWTyYRhGMnzA4Gv02Wu6zGZTHl/fc1kMmXsB4qywnEcTKHbb2/efaDvBwwDtrstZVlQViVhFOL5HrudbiqgJIEX4vsebddRlRq8ZX3zxdWLAQPH9dhuH9jv9mCazGdzukFye3tP30sMw2J1skQpnZQ6HHKqquT+/o6u71iv77BNmzgKieKEv/z4V6azOa/fvKHte0xb+9jSNOWXv/wltm3z+9//O7e3txwOe7a7LTfX13y4+YAtLG5vPzKOA67n0A8dw9jjORAEDkkUkoQhtm3g+kdcz3zO+fkFZaknzgVhiHC08f3Hv/yJ//HP/8wPP/yFk5MzHh42BEFAksSgoB90imAYR+qqoqobMA1s4TKMEstxeUh3CMui7zvy/EBdV9i2FqF838MwdH9zv9vT1A2T6QRb2JRVQV7ssX713dcvBgl1P4KUnJ2dgTJIswNpVuhTVTg4rsA0DW5vb6kqfV3dbjdUVUnX69y453jMpjMe7h9QSiEVvHz5islsRt9LHGGTHAXzjx9vcF2XojiglKSuK24+3lAVJXmWsd/tcB1B4HlMkwRH2CxWE+IkZjadYhoGQjgYhoVwPKqqpR8krutx/7Dm7m7NPstYzCZcnJ/w8LDmn/7pv/Hm53esVksNXXFd7u/vCMOIrutZnZzw8tUr1us1s8mcsm44FDl3DxvKsibdbSnL8rEa+RTp+HsJ2DO0LVVdk+5SqrogiAN2+y3Wd199+aIboZdgKo2ixLS0oF2VKAMwFOMwINWIaZiap9EPOI5gGHpGObJaLXRzYLvDcz2KomCf7vEcn6JoiMIIYdvYlr76pmmKEBZhGLJczen6lr5v8X2HtquxhUkY+YSRTxB6jGOZyLoSAAAJ1UlEQVSH5ViYBkyShMl0jmULmq6jG0cMW6+m99cfsGyHN2/fcnF5gRx7JkmMkpJxUFxeXvHy5SuWywVNUwMGRaHHm5iWDvs3dYfnezRNS9eNHIqcQUn6tiUMfUxTR6Q9zwWURhNJHSMRwgEFVV2BAYMcODk7wfr+u+9eSEwsx8M2Tbq2xzR0WCjLMmxhYdsW2AZjP2otVyrGUb+FWkyyyLKUm3fXyGHEsmzu79dE0YSuH9huNpydP6HI9iSTmMPhcLzaRgShR1EcMAzIshQ5DkRhwNOrS93lEDZyHACJYVt4QYjn+biOg4GJlIpdmmI7HtbxS3zY7PCDkN0+5erJBWWe4zgWVdVhmhZJkrBe3yOlIkliNpst+31KFMdURxHNcTxWqxWbzZbtPqWoKooyZzzm4T8Bbj91kYZhoK1ruq6lrlvGo0+Po7XO+vabr14IYROHEcIAyzCpypJx7KjKAt8PsGwblEJiIJXU/IuhY5ADEolhmhRVSdWXVG3Jrsg4vzjn8uqSIi8Ag/vbe4axITxCsB1HW4Nd1+H+/g7DMB5p69OpngjxCI89VgRKShazuc5tWzajgn4cUcqi7wcwbTw/wbIE+33K6WqBGkaeXj3BRNtnm7omikKatkXYLgqTdH9ASgPH94+CvWCQI/PlEmkobm6uabuG5WyOaVoa9RZPKPISxxKYmMhBO22LqqEfj+Nfhc1qoRVG6/mzz140ja4e+qalaSsMy6AsS9QxCav0RB2du9bjfRjlSFVXGshaFKSpfvsxLfqhx7RsLEuQ7nbkeYawLISwSNMtm+09bdtQVgdM08A0DaKj8XuxWBwD+M7jcIYkSQjDECUVYaAlSr2iGo2rQLNPq6pjRNF3ujsjLBPPEfh+QBgERzRFS5rumc5mfLi5YbU6Ia/0c9jHrdAPgmMNbTObzUjTlLqsND70iGz2PY8yzxFC4LseSirariUIdcWhQV4dXdfiuS7WF8+evvhE9rIMAwm4rkc3jpimxaiUBj01LV0/0PXd41LxfV+XQEeBfBwkTd0RhjGe4/Hx9prNw/oYUfaxhYFUPff3d/i+jgpbtkEQ+igknuNyfnYGSuG5roZUdR1JHBOFIfPF4rHrHgQhXdcfe3o6YP+w2TCdTCjzw5HebhDFCVVZcHZ2TrbPmE6npFn2SEd4+fo1SunxJkEYIKVOebVty83NDWEYstlstG3gKJl2XadD+0f+kjzeQRzXJQwCXEfgex6GUkwmCbZlYf+/0JJRKQzDYLtPsW2bstbgJ3k8XYfjgWKapl7qTY9lWQy9RCkYegOUYJ/mFIecONGtLkWLaYWEYYBlaf/zdJbo+VpqJIq0wVyYeu87OTmhLEts29Y4zaLQb/Tx8+12O5RC+wJNE2Ef1b6qQljmI5xFOFrssnyfzS7FC3zWRxxylh8Ig1hzUQ0Dz/cf4d5FoS1sm83mWM7WOI7DcqnnsXzq/GvKg0l7bBj4YUBZltS1FsdmsxlNW9N1HdYvvv36xadJbKPUl42maambhqEfKOoay7JxPA8D69ju11vJJ+JhGIbH5e5jGCauK3AcQRD6BL6H5ztMpzFJMtFk8sjH87xHiOsnwLeBiWVYTCcThn7AtmwsUxsGlVQ6x21o11AYRgyfHKlVfaSIKZQcWcxn+KFPEk9RGNjCQSqoy4JBjgRhyMuXLzFtQRBGj/rzfp/SthpOW5bl8QvVxLCyLHn+/LkGFipF4PuaECwEBpqiEPgBbdMgxxFh2wS+x2w6xXUcTB2X0G8KSlO4pNII4ENZYZo2cTIliacI4T4SEcHU3QtlUFUNZVlzOBwoy5Isyx5ZGZ/4d59GbDiOno+izedrfvjhb7x69VrXw5ZNHMePgMIgCJjNZpycnBDHMZ7j/H8Rs092AN/3NbHANBl7DU2xDfPR4CNcj36UlEfTY5pl+KGuSiaTCYeywAsDptPpYwf/E4KiqirqWvczPc8jiiIsS9PUXdflcDg8riZtPUj1zIMwfPysURRhh2HI7e2t/harBmMw9JI2DQYlqWr9D3Q8l8M+R0qp2c/23xOiZVkevywIQxchIpIk4uzsBEOOTGcJkzh5HJLT99rX5joBs+mCKIoQtq99a36AGiWO44If0HWd7nq4HsJ3Kev6iIUwCUP90I6jPReeI0COqHHADUIwDKqmxXYaRgX7Q8Hq7JTtu2sMy6TYZ7z98P5xa9AjRUrKsjzKAnoraduWIAjIskzbEmybPM85WS61nICmv1+//8BiseD161f4rsfJ6ZLra+1ssj67fPLC97VMaBjm8bdB3TZwJG1ZQu+VtiUIgkBHhOtavy1CaIqBbWOaukHrug6WaeqhZUdskBxHirwizyum0ymmaTOZTI6XnpHlckUSRcyms6PpsnmEFHqeRxiGCNdBHoEsTaMFIikltqU9JpbBUXns8HyfYZRIBUWlEZ1NVZJlOjdYViW2Lbi9u+fs4px3798xiWPy/PDI7Ntut/R9/1grazVSDzTuux6OEzuy43YSBsHx7dfEGz/wdMJ2t8OW/YDsNY6yY0RairwptK+47zBtA8sytPW1a2nbljzPmU6nTKZTfSj2nR4SM7ZUxYGxbVGmzX6T4biCq6sA4Vq4wqGta6JQkA0VgeMyv7qibVviOGYazxnakXHsGMaOQ1OhpAGuz9hJzbwzbJ3vFi6WqSMZUkoNahEGtmlxKHbEk4Sh61B9g6l66mKPaVvkhUbsz+dL5CB5uNvy8c01geOx3eyYJHN220xPivZ0ana5XDIMA5t0B6bQOZu6pWw1Xk4OknIcGdsGWwiaYdCXpOmMGsEoTKzPrp6+GKXCMC3aYWCUSlcQg74F6sPNwzBMiqJ8JC9q81/Npz3e933apqLterp+oO0kD9uNjl/MYvqx0+DsqmIc9GgP27JZ393juS51VevsyzjiBR7DOFA1JZZt6/p91BcmNSrUqLBNmygMkeNI22hTpGEYmJZBlmWPY0f6vqOpK7I0RSlDQ7iOSYGbjx952GyYTKcIW/C3l3/FcjRoZZA6CdyPAxgGXd9zKHJcz0UBTatvf57v4XouUknKtmFQknS/xzpayYZxpB8GrGdfPHuRFTmWI2j7AXV09iupy7dxVJiGTd+PuK7zODV5GIajQds6jidVmLZ5PDQCprM5STIhiHz6oceybVzh4rk+UhlEQURZVCTJlP0uwzRt7h/usB0Lz3ewHbCFzSE/aH0aSdd2mIaJHDUIVtiCsigo8gIDMEwDwzY1KNYRCMfh5zdvsISNcByEpTMmbd2SlwVFUVI2Da7vUdQVbuDy6qdXTGcz9tmeMAqpaq0pO67LdDY7Ov4PdH2PUkc21HG01TCOWJ+mSgttsg+PsMP/C8/VMGEnBVFjAAAAAElFTkSuQmCC'
