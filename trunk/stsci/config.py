#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#
# This is just stuff to APPEND to config.py for the stsci configuration.
# See also pwform.html for the weird dance we do to get the password
# into a file that is only readable by the web server.

pdk_url = "https://ssb.stsci.edu/pandokia/pandokia.cgi"

cginame = 'https://ssb.stsci.edu/pandokia/pandokia.cgi'

flagok_file = "/eng/ssb/tests/pdk_updates/%s.ok"

recurring_prefix = (
    'daily',
    'etc_daily',
    'etc_midday',
    'etc_hst_daily',
    'etc_jwst_daily',
    'jwst',
)

if not 'pdk_db' in globals() :
    # Database: MYSQL
    #           http://www.mysql.com/
    # MySQLdb
    #           http://mysql-python.sourceforge.net/MySQLdb.html
    try :
        import pandokia.db_mysqldb as pdk_db
        import pandokia.db_mysqldb as dbd

        # db_arg is a dict of the parameters to pass to connect()
        db_arg = { 'host' : 'ssb.stsci.edu',
                'user' : 'pandokia',
                'passwd' : complex_readpass(),
                'db' : 'pandokia'
            }

        # This does not actually open the database unless you try to talk to it
        pdk_db = dbd.PandokiaDB( db_arg )

    # on systems where we can't import the database driver, assume
    # we don't actually have a database and therefore it won't matter.
    except ImportError :
        pass


enable_magic_html_log = True
