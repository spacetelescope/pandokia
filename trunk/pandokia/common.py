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
# 
#
def expand_test_run( run ) :
    s = find_test_run( run )
    if run != s :
        return s
    where_str, where_dict = pandokia.cfg.pdk_db.where_dict( [ ( 'test_run', run ) ] )
    print 'SELECT test_run FROM distinct_test_run %s' % where_str
    c = pandokia.cfg.pdk_db.execute( 'SELECT test_run FROM distinct_test_run %s' % where_str, where_dict )
    l = [ ]
    for x, in c :
        l.append(x)
    return l


#
# convert a test_run name entered by a user into a real test_run name; various
# nicknames get translated into real names.
#
def find_test_run( run ) :

    if run.endswith('_latest') :
        prefix = run[0:-len('_latest')]
        if prefix in cfg.recurring_prefix :
            s= run_latest(prefix)
            return s

    if run.endswith('_today') :
        prefix = run[0:-len('_today')]
        if prefix in cfg.recurring_prefix :
            d = datetime.date.today()
            return "%s_%04d-%02d-%02d"%(prefix,d.year,d.month,d.day)

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
#
# pattern for a test run name that appears to have a date in it

looks_like_a_date_re = None     # don't compile it unless we use it

def looks_like_a_date( name ) :
    global looks_like_a_date_re
    if looks_like_a_date_re is None :
        looks_like_a_date_re = re.compile('[^0-9]([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])($|[^0-9])')
    t = looks_like_a_date_re.search( name )
    if t :
        return t.group(1)
    return None

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

    # just a date
    try :
        d = datetime.datetime.strptime(arg,'%Y-%m-%d')
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
    if len(l) > 3 :
        prefix = '%s_%s_%s'%(l[0],l[1],l[2])
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
B64IMG_HEADER = 'iVBORw0KGgoAAAANSUhEUgAAAEQAAABJCAIAAAAL7xc7AAAgAElEQVRogd16Z3Sk13kefubkxKK4u+i9zACY3nvvvffee+99MIMZDHpbYAuW3MK2bJKo4khOHCuOE1uWJcsqkWRbIkVbEi2KskxyuYWk5NxVnCiWKcYnyVFycs/Fhw8zKPe57/s+7/PcD0N////RGPq/vYD/k+OXYN577913330APv7Htx88ePjKp1/6+De+/tW33vy7n7zx+r17d8E33r937/79ez/72c9+4wv+sPFLMD//bwPc37t37/Uf/+i111576ROfCAUDGoU0HHDfvH71u9/5izt33n77rTfff++9nz0c7//fW/kHjA9Osx/+8PuvvPydG9fOZEIBnUQkIOFYGBS1PGvVSJ+4dvrqK9+5+847/x35/zvjA8Dcu3v3C7//+YPeOguPFzPoZoXcKJVqhAIFhyYgIUUk5HGv+a2vffnB/Xu/+eV++PgAMH/749d3Wk0egcAhEHQikVOrdev1JplMJ+LblBIJmSilknY71Tff/Ns7d976za/4Q8YHgPmbH/ygUywpmCyrQuExGMJ2e9Bqdel0agFPI+CaJZKQyeIz6T/5sduvvPyXv/kVf8j4ADDf/PrXTBKZVSbPBALZYBBMr9FoUSgsSplGxHdqtLV4qpJMJCOeL/zRH/zmV/wh41fB3L17t9+sWeXSSixWjEZ7lUorl6smkzGXy2vW2XVyr8lQSyU3GvVqMel1G17+7p+/886d+4Cn7917cP8+IDhQcj954w3AEHfefhOQ+dtv/x1g8vfee/D+/zb1vXP3re//4Ht//Mf/8Utf+sKX//QLr/3ND95978GvBfPee+8B5q3ls26tup5I5MLh3c7a8WCjUyqWE/Fs2B/3OlMBH7jv1SqlbMxiUpydnbz66stvvvlTAAcs/+Xv/OW3vvmfv/61P/vqV7789T/74re++aff//7Lb9956979O6CJ/S/D+O6rX//iV37/2RdueP0mKonAoNF4QvaTz9z8lUb3j8CA917/0esxfyBqs5ci0UwwtL3WOej3WoXsWim30awNmo2tdmujURu0ap1KNhn2cViU3Z31L/3Jf/oPn//cl7/4R7VCupBJdJrlQa9+7XT7iceOnn7i5IXnr//u7338m9/+0k/+9kf//W/9/Oc/AwjvP7h7/8EdsMH3H4AW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'
B64IMG_FORMAT = 'png'
