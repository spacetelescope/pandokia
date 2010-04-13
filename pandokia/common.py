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
# create a sql safe WHERE clause
#
# list is a list of (name, value) pairs, where name is the name of a column
# and value is a string or wild card to match.
#
# The return value is safe to use in a database query with
#    "SELECT whatever FROM whatever " + where_str(parm_list)
# even if param_list came from a hostile user.  Little Bobby Tables
# isn't going to mess us up.  ( http://xkcd.com/327 )
#

re_funky_chars = re.compile('[^ -~]')   
# used to remove control characters.  Yes, it works on strings with \0
# in them.

re_single_quote = re.compile("'")

def where_str(list) :
    need_and = 0
    res = ""
    for x in list :
        (name, value) = x
        if value == '*' :
            # if value is "*", we don't need to do a
            # comparison at all.  In sqlite, " a glob '*' "
            # takes much longer than leaving out the glob operator.
            pass
        else :
            # WHERE expr AND expr AND expr
            if need_and :
                res = res + " AND "
            else :
                need_and = 1
            res = res + name
	        # I assume any control character is hostile action.  It
            # is convenient to just quietly drop it.
            value = re_funky_chars.sub('',value)
            # escape single quote to prevent sql injection
            if "'" in value :
                value = re_single_quote.sub("''",value)
            # if value contains a wild card, add a GLOB
            # action, otherwise add '='.
            if '*' in value or '?' in value or '[' in value :
                res = res + " GLOB "
            else :
                res = res + " = "
            res = res + "'" + value + "'"

    # if we some how managed to avoid adding any conditions to the
    # string, we also do not want the word "WHERE " in it.  The
    # user then has "select ... from table" + ""
    if res != "" :
        res =  "WHERE " + res
    return res


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


