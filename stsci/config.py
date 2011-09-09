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

if not 'pdk_db' in globals() :
    # Database: MYSQL
    #           http://www.mysql.com/
    # MySQLdb
    #           http://mysql-python.sourceforge.net/MySQLdb.html
    import pandokia.db_mysqldb as pdk_db

    # db_arg is a dict of the parameters to pass to connect()
    db_arg = { 'host' : 'localhost',
            'user' : 'pandokia',
            'passwd' : readpass(),
            'db' : 'pandokia'
        }

