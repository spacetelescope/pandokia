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
# interface code as pdk_db; set db_arg to what pdk_db.open_db()
# will need to know to access your database
#
# The database interface code is named for the dbapi package
# that talks to that database, but all lower case.
#

def readpass() :
    import os.path
    f=open(os.path.dirname(__file__)+"/password")
    s=f.read()
    f.close()
    return s.strip()

if 1 :
    # Database: SQLITE
    #           http://www.sqlite.org/
    #
    # sqlite3 - ships with python
    #           http://docs.python.org/library/sqlite3.html
    # pysqlite - same driver, developed separately from python distribution
    #           http://code.google.com/p/pysqlite/
    import pandokia.db_sqlite as pdk_db
    import os

    # db_arg is the file name of the database; default here is to store it
    # in the install dir, but normally you would point this somewhere that
    # you have a big disk to store your data
    db_arg = os.path.dirname(os.path.abspath(__file__))

if 0 :
    # DOES NOT WORK YET
    # Database: Postgres
    #           http://www.postgresql.org/
    # psycopg
    #           http://initd.org/psycopg/
    # 
    import pandokia.db_psycopg2 as pdk_db
    db_arg = 'dbname=test'

if 0 :
    # Database: MYSQL
    #           http://www.mysql.com/
    # MySQLdb
    #           http://mysql-python.sourceforge.net/MySQLdb.html
    import pandokia.db_mysqldb as pdk_db

    # db_arg is a dict of the parameters to pass to connect()
    db_arg = { 'host' : 'goldink', 
            'user' : 'pyetc', 
            'passwd' : readpass(),
            'db' : 'test_pandokia2'
        }


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
user_list = None

# which users can see/operate the admin interfaces 
admin_user_list = ( 'sienkiew', 'Nobody' )

# 
adminlink = '<br> <a href=CGINAME?query=admin>Admin</a> <br>',


######
#
# os type for each host
#

# a dict mapping the host name to the OS name to display
#
# a purist would spend a lot of time writing/testing code to
# store this in the database,  I'm too busy.
#
os_info = {
    # this is sample data - you can list your own machines here
    # or you can leave this blank.

    "arzach":   "RHE 5 / 64",
    "banana":   "Mac x86",
    "basil":    "Solaris 10",
    "bond":     "Mac Leopard",
    "cadeau":   "Mac Leopard",
    "doof":     "Centos 5.3",
    "dukat":    "Windows/XP",
    "ekky":     "Mac x86",
    "etc-dev1": "RHE4 / 64, ETC",
    "gaudete":  "RHE 4 / 64",
    "herbert":  "RHE 4 / 32",
    "macbert":  "Mac PPC",
    "motoko":   "RHE 4",
    "quagga":   "RHE 3",
    "ssbwebv1": "RHE 5 / 64",
    "thor":     "RHE 4 / 64",
    "timthe":   "Mac PPC",
    "tufnel":   "Solaris pipeline",

    }

######
#
# What is the URL for this pandokia instance?  This link is included
# in email notices.
#
# This should be the URL of the CGI, but if you .
pdk_url = "https://www.example.com/pandokia/pdk.cgi"


######
#
# When pdk run recursively searches a directory tree for tests, it will ignore 
# any directory with one of these names.
#

exclude_dirs = [
    '.svn',
    '.subversion',
    'CVS',
]

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
runner_glob = [
#   ( 'not_a_test*.py',     None        ),      # file name that is recognizably not a test
    ( 'pycode*.py',         'pycode'    ),      # special runner that just executes python code
    ( '*.py',               'nose'      ),      # nose on a file here
    ( '*.snout',            'snout'   ),        # nose on an installed file
    ( 'test*.sh',           'shell_runner' ),   # single test in a shell script
    ( 'test*.csh',          'shell_runner' ),   # single test in a csh script
    ( '*.xml',              'regtest'   ),      # legacy system used at STScI
]


######

debug = True

#
# set server_maintenance to a string to cause the cgi to issue a 
# "server maintenance" page in response to any transaction.
# This gives you a chance to do database maintenance without hurting
# anybody.
# server_maintenance = 'backing up database'
server_maintenance = False

#
# name of cgi for use in generated html.
# We actually use the cgi name as reported to us by the web server if it
# is available, but if we are not running in the context of a web server,
# we use this value.
#
cginame = "https://ssb.stsci.edu/pandokia/pdk.cgi"

#
# list of known status values, in order they appear on reports
#
statuses = [ 'P', 'F', 'E', 'D', 'M' ]

# names of statuses
status_names = { 
    'P' : 'pass',
    'F' : 'fail',
    'E' : 'error',
    'D' : 'disable',
    'M' : 'missing',
    }

#####
#
# used if the user has nothing in their email preferences
#

default_user_email_preferences  = [
#   ( project, format, maxlines )
#       formats: n=none, c=contact, s=summary, f=full
    ( 'astrolib',       'n',    100 ),
    ( 'multidrizzle',   'f',    100 ),
    ( 'pydrizzle',      'f',    100 ),
    ( 'pyetc',          'n',    100 ),
    ( 'stsci_python',   'f',    100 ),
    ( 'stsdas',         'f',    100 ),
    ]

#####
#
# how many days old must a qid be to expire
default_qid_expire_days = 30


#####
#
# END OF CONFIGURATION
#
flagok_file = "/eng/ssb/tests/pdk_updates/%s.ok"
