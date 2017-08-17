#
# pandokia - a test reporting and execution system
# Copyright 2009, 2011, Association of Universities for Research in Astronomy (AURA)
#

#
# This is a default config file for pandokia.  It is imported
# by the CGI and by the command line to find all the configuration
# data.
#
# This is configuration code is executed every time the CGI starts up,
# so don't get crazy with automatic discovery.
#

######
#
# To select the database to use, import the appropriate database
# driver and instantiate a connection to the database.


def readpass(fn=None):
    f = open(fn, 'r')
    return f.read().strip()


def complex_readpass():
    # import os.path
    # d=os.path.dirname(__file__)
    d = '/ssbwebv1/data2/pandokia/'
    pf = 'mysql_password'
    try:
        f = open(d + pf)
    except:
        try:
            f = open(d + "/alt_password")
        except:
            return None
        s = f.read()
        f.close()
        return s.strip()
        try:
            f = open(d + pf, "w")
            f.write(s)
            f.close()
            import os
            os.chmod(d + pf, 0o600)
        except:
            pass
        f = open(d + pf)

    s = f.read()
    f.close()
    return s.strip()

from .config import config

db_cfg = config['database']
db_backend = db_cfg['backend']
db_arg = None

if db_cfg['password_type'] == 'file':
    password = readpass(db_cfg['password'])
else:
    password = db_cfg['password']

# Configure backend(s)
if db_backend == 'sqlite':
    import pandokia.db_sqlite as dbd
    db_arg = db_cfg['db']

elif db_backend == 'mysql':
    import pandokia.db_mysqldb as dbd
    db_arg = {'host': db_cfg['host'],
              'user': db_cfg['user'],
              'passwd': password,
              'db': db_cfg['db']
              }

elif db_backend == 'postgres':
    import pandokia.db_psycopg2 as dbd
    db_arg = {'host': db_cfg['host'],
              'user': db_cfg['user'],
              'passwd': password,
              'db': db_cfg['db']
              }

else:
    raise Misconfigured('Unknown database backend: {}'.format(backend))

# Is db_arg good to go?
if db_arg is None:
    raise Misconfigured('Verify database backend configuration: {}'.format(backend))

# Instantiate database interface
# This does not actually open the database unless you try to talk to it
pdk_db = dbd.PandokiaDB(db_arg)


######
# Who are authorized users:
#
# user_list = None
#   any user authenticated by the web server is authorized
#   if the web server did not perform authentication, any user is authorized
#
# user_list = [ 'alice',  'bob', 'eve' ]
#   the web server must perform authentication, and only these users are authorized
#
# This feature is not well-tested.
user_list = config.getlist('access_control', 'users')

# which users can see/operate the admin interfaces
admin_user_list = config.getlist('access_control', 'admins')

######
#
# What is the URL for this pandokia instance?  This link is included
# in email notices.
#
pdk_url = config['cgi']['url']


######
#
# When pdk run recursively searches a directory tree for tests, it will ignore
# any directory with one of these names.
#
exclude_dirs = config.getlist('pandokia', 'exclude_dirs')


######
#
# This list is searched in order to identify the test runner used to run a
# file.  If a file name does not match any pattern here, then it does not
# contain tests.
#
# If the name of the runner is None, that the file does not contain tests.
#

# You don't need to edit this unless you create a new type of test
# that requires different code to test it.
runner_glob = config.getlist_nested('pandokia', 'runner_glob')


######

debug = config.getboolean('pandokia', 'debug')

#
# set server_maintenance to a string to cause the cgi to issue a
# "server maintenance" page in response to any transaction.
# This gives you a chance to do database maintenance without hurting
# anybody.
# server_maintenance = 'backing up database'
server_maintenance = config.getboolean('cgi', 'server_maintenance')

#
# name of cgi for use in generated html.
# We actually use the cgi name as reported to us by the web server if it
# is available, but if we are not running in the context of a web server,
# we use this value.
#
cginame = config['cgi']['url']

#
# list of known status values, in order they appear on reports
#
statuses = config.getlist('pandokia', 'statuses')

# names of statuses
_status_names = config.getlist('pandokia', 'status_names')
status_names = dict(zip(*[statuses, _status_names]))

#####
#
# used if the user has nothing in their email preferences
#
#   ( project, format, maxlines )
#       formats: n=none, c=contact, s=summary, f=full
default_user_email_preferences = config.getlist_nested('pandokia', 'default_user_email_preferences')

#####
#
# how many days old must a qid be to expire
default_qid_expire_days = int(config['pandokia']['default_qid_expire_days'])


#####
#
# when a test name is FOO_xxx, look to see if FOO is in this list;
# when a test name is FOO_BAR_xxx, look to see if FOO_BAR is in this list.
# if it is, it is a type of recurrent test and next/previous links
# make sense.

recurring_prefix = config.getlist('pandokia', 'recurring_prefix')
#####
#
# Some tests write HTML into their log.  If enable_magic_html_log is
# set to True, the display will offer a link that shows only the
# html portion of the log.  Click that link to see the log output
# beginning with <!DOCTYPE or <html and ending with </html>.
#
# One of our projects uses mechanize to talk to a Django application;
# if django shows an error page, you can click the link to see
# what it should look like.
#
# If you turn this feature on, anybody who writes your tests can
# insert arbitrary HTML to be displayed on the user's browser.
# It is a security problem if you cannot trust everybody who
# writes your tests.
#
enable_magic_html_log = config.getboolean('cgi', 'enable_magic_html_log')


#####
#
# END OF CONFIGURATION
#
flagok_file = config['pandokia']['flagok_file']
