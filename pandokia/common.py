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

pdk_db = pandokia.cfg.pdk_db

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
    for i in sorted(query_dict.keys()) :
        v = query_dict[i]
        if v is None :
            continue
        if not isinstance(v,list) :
            v = [ v ]
        for v in v :
            l.append( i + '=' + urllib.quote_plus(str(v)) )
    return get_cgi_name() + "?" + ( '&'.join(l) )

#
# convert a dictionary into a set of <input type=hidden> html
#

def query_dict_to_hidden( query_dict ) :
    l = [ ]
    for x in sorted(query_dict.keys()) :
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

# bug: look for ending with a thing that looks like a date instead of starting with "daily_"

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
    c = pdk_db.execute("SELECT email FROM contact WHERE project = :1 AND test_name = :2 ORDER BY email",(project, test_name))
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
    return 'Nobody'

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
# quote a string so we can use it in a shell command.
#

def csh_quote(s) :
    """
    Quote a string so we can use it in a csh command without getting hurt.

    x = csh_quote( s )

    Remember that the csh parser is pretty stinky.  If you use a special
    character and this doesn't work, don't be too shocked.

    """

    # result string is quoted with single quotes.  Here is the start.
    l = [ "'" ]

    for x in s :
        if x == '\n' :
            l.append('\\\n')
        elif x == '!' :
            l.append('\\!')
        elif x == '\\' : 
            l.append('\\\\')
        elif x == "'" :
            # end single quote for preceeding string
            l.append("'")
            # put a single quote that is quoted by double quotes
            l.append('"')
            l.append("'")
            l.append('"')
            # start single quote for next part of string
            l.append("'")
        else :
            l.append(x)

    # result string is quoted with single quotes.  Here is the end.
    l.append( "'" )

    return ''.join(l)


def sh_quote(s) :
    """
    Quote a string so we can use it in a sh command without getting hurt.

    x = sh_quote( s )

    """

    # this string is hard to write in any readable way, so I construct it
    # in a (slightly) more readable way:

    qt = [ "'",             # close quote
            '"', "'", '"',  # "'"
           "'",             # open quote
        ]
    qt = ''.join(qt)

    # put ' around the string and replace any internal single quotes
    # with another string that has quoted single quotes
    s = s.split("'")
    return "'" + qt.join(s) + "'"


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

######

print_stat_dict_tuple = ( 'P', 'F', 'E' )

def print_stat_dict(stat_summary) :
        s = [ ] 
        for x in print_stat_dict_tuple :
            if x in stat_summary :
                s.append( "%s=%d"%(pandokia.cfg.status_names[x], stat_summary[x]) )
        for x in stat_summary :
            if not x in print_stat_dict_tuple :
                if stat_summary[x] > 0 :
                    name = pandokia.cfg.status_names.get(x,x)
                    s.append( "%s=%d"%(name, stat_summary[x]) )
        if len(s) > 0 :
            print " ".join(s)
        else :
            print "Nothing to report"

######


B64IMG_FAVICO = 'None'
B64IMG_HEADER = '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'
