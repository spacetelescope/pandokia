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

    if run.endswith('_latest') :
        prefix = run[0:-len('_latest')]
        if prefix in cfg.recurring_prefix :
            return run_latest(prefix)

    if run.endswith('_yesterday') :
        prefix = run[0:-len('_yesterday')]
        if prefix in cfg.recurring_prefix :
            d = datetime.date.today()
            if d.weekday() == 0 :
                # if today is monday, find friday
                d = d - datetime.timedelta(days=3)
            else :
                # tuesday - friday, find yesterday
                d = d - datetime.timedelta(days=1)
            return "%s_%04d-%02d-%02d"%(prefix,d.year,d.month,d.day)

    return run

    #### abandoning the rest for now

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


def run_previous( prefix, test_run ) :
    if prefix is None :
        prefix = recurring_test_run(test_run)
        if prefix is None :
            return None
    c = pandokia.cfg.pdk_db.execute("SELECT test_run FROM distinct_test_run WHERE test_run LIKE :1 AND test_run < :2 ORDER BY test_run DESC LIMIT 1",
        ( prefix+'%', test_run ) )
    x = c.fetchone()
    if not x :
        return None
    return x[0]

def run_latest( prefix ) :
    c = cfg.pdk_db.execute("SELECT MAX(test_run) FROM distinct_test_run WHERE test_run LIKE :1 ",
        ( prefix+'%', ) )
    x = c.fetchone()
    if not x :
        return None
    return x[0]

def run_next( prefix, test_run ) :
    if prefix is None :
        prefix = recurring_test_run(test_run)
        if prefix is None :
            return None
    c = pandokia.cfg.pdk_db.execute("SELECT test_run FROM distinct_test_run WHERE test_run LIKE :1 AND test_run > :2 ORDER BY test_run ASC LIMIT 1",
        ( prefix+'%', test_run ) )
    x = c.fetchone()
    if not x :
        return None
    return x[0]
    


#
# look up a contact for a test
#
def get_contact( project, test_name, mode='str') :
    # 
    pdk_db = pandokia.cfg.pdk_db
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
        s1 = "<h1><a href=%(url)s><img src='data:image/%(imgfmt)s;base64,%(image)s' alt='' border=0></a>&nbsp;Pandokia</h1>"

    page_header_text = s1 % { 'url' : get_cgi_name(), 'image' : B64IMG_HEADER, 'imgfmt' : B64IMG_FORMAT }

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

def recurring_test_run(test_run) :
    l = test_run.split('_')
    if len(l) > 1 :
        prefix = l[0]
        if prefix in cfg.recurring_prefix :
            return prefix
    if len(l) > 2 :
        prefix = '%s_%s'%(l[0],l[1])
        if prefix in cfg.recurring_prefix :
            return prefix
    return None

######

hostinfo_cache = { }
def hostinfo( name ) :
    if not name in hostinfo_cache :
        c = cfg.pdk_db.execute("SELECT hostname, os, description FROM hostinfo where hostname = :1",(name,))
        x = c.fetchone()
        if x is None :
            x = (name, '?', '?')
        else :
            # converting db object to a tuple
            x = (x[0],x[1],x[2])
        hostinfo_cache[name] = x
        return x
    return hostinfo_cache[name]

######




B64IMG_FAVICO = 'None'
B64IMG_HEADER = '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'
B64IMG_FORMAT = 'jpeg'
