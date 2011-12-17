import os

def mysql(clear) :
    import pandokia.db_mysqldb as dbx

    f = open("access_mysql")
    hostname,username,password,dbname = f.readline().strip().split(';')

    dbx = dbx.PandokiaDB( {
        'host' : hostname, 
        'user' : username, 
        'passwd' : password, 
        'db' : dbname   
        } )

    if clear :
        dbx.execute('drop table if exists test_table')

    return dbx

def sqlite(clear) :
    import os
    import pandokia.db_sqlite as dbx

    if clear :
        try :
            os.unlink('db_sqlite')
        except OSError :
            pass

    dbx = dbx.PandokiaDB('db_sqlite.db')

    if clear :
        dbx.execute('drop table if exists test_table')

    return dbx

def postgres(clear) :
    import os
    import pandokia.db_psycopg2 as dbx

    try :
        f = open("access_postgres")
        hostname,username,password,dbname = f.readline().strip().split(';')
        d = { }
        if hostname != '' :
            d['host'] = hostname
        if username != '' :
            d['user'] = username
        if password != '' :
            d['password'] = password

    except IOError :
        d = { 'database' : 'pandokia' }

    dbx = dbx.PandokiaDB( d )

    if clear :
        dbx.execute('drop table if exists test_table')
        dbx.execute('drop sequence if exists test_sequence')
        dbx.execute('create sequence test_sequence')

    return dbx

