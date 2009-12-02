#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
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
# This version of pandokia only knows how to use sqlite3 as a database.
# dbdir is the directory where the database files are stored.
# This directory _and_ the database files must be writeable to
# the cgi.

# This line causes the database to be stored with the installed code,
# but you can put any fully qualified path name here.
import os.path
dbdir = os.path.dirname(os.path.abspath(__file__)) + '/pandokia_db'

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

######
#
# os type for each host
#

# a dict mapping the host name to the OS name to display
#
# a purist would spend a lot of time writing/testing code to
# store this in the database,
#
os_info = {
    # this is sample data - you can list your own machines here
    # or you can leave this blank.

    "banana":   "Mac x86",
    "basil":    "Solaris 10",
    "bond":     "Mac Leopard",
    "cadeau":   "Mac Leopard",
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
    ( '*.py',               'nose'      ),      # nose on a file here
    ( '*.snout',            'snout'   ),        # nose on an installed file
    ( 'test*.sh',           'shell_runner' ),   # example of writing a test runner
    ( '*.xml',              'regtest'   ),      # legacy system used at STScI
]


######

debug = True

#####
#
# END OF CONFIGURATION
#
flagok_file = "/eng/ssb/tests/pdk_updates/%s.ok"
