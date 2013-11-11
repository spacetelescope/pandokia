
##########
# import test configuration
import os
import pandokia.helpers.importer as i
tc = i.importer( 'test_config', os.environ['PDK_TOP']+'/config' )
config = tc.cfg

exec('import pandokia.db_%s as dbd'%tc.cfg['test_database']

##########

pdk_db = dbd.PandokiaDB( tc.cfg['test_database_%s'%tc.cfg['test_database'] )

user_list = [ ] 

# which users can see/operate the admin interfaces 
admin_user_list = ( 'sienkiew', 'Nobody', )

# This link is included in email notices.
pdk_url = "https://www.example.com/pandokia/pdk.cgi"

# don't descend into these directories to find tests
exclude_dirs = (
    '.svn',
    '.subversion',
    'CVS',
)

debug = True

# server_maintenance = 'backing up database'
server_maintenance = False

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


default_user_email_preferences  = [ ]

# how many days old must a qid be to expire
default_qid_expire_days = 30

# when a test name is FOO_xxx, look to see if FOO is in this list;
# when a test name is FOO_BAR_xxx, look to see if FOO_BAR is in this list.
# if it is, it is a type of recurrent test and next/previous links
# make sense.

recurring_prefix = (
    'daily',
    'weekly',
    'monthly',
    )   


flagok_file = "/eng/ssb/tests/pdk_updates/%s.ok"
