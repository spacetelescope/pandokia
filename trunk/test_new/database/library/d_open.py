#
# Connecting to the test database
# ---
#
# Remember that none of these actually connect to the database until
# you actually attempt a database interaction.
# 
import os

import pandokia.helpers.importer as i
tc = i.importer( 'test_config', os.environ['PDK_TOP']+'/config' )
config = tc.cfg

def get_db_access(dbname) :
    s = 'test_database_%s_enable'%dbname
    if not ( s in config ) or not config[s] :
        raise NotImplementedError("database %s not enabled in %s/config" % (dbname, os.environ['PDK_TOP']) )
    return config['test_database_%s'%dbname]

def mysql(clear) :
    import pandokia.db_mysqldb as dbx
    d = get_db_access('mysqldb')
    dbx = dbx.PandokiaDB( d )
    if clear :
        dbx.execute('drop table if exists test_table')
    return dbx

def sqlite(clear) :
    d = get_db_access('sqlite')
    import pandokia.db_sqlite as dbx
    if clear :
        try :
            os.unlink(d)
        except OSError :
            pass
    dbx = dbx.PandokiaDB( d )
    return dbx

def postgres(clear) :
    d = get_db_access('psycopg2')
    import pandokia.db_psycopg2 as dbx
    dbx = dbx.PandokiaDB( d )
    if clear :
        dbx.execute('drop table if exists test_table')
        dbx.execute('drop sequence if exists test_sequence')
        dbx.execute('create sequence test_sequence')
    return dbx

