#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#
# psycopg database driver
#
# This is almost exactly the mysql driver, but with a few things changed
# for postgres.

__all__ = [ 
    'db_module',
    'db_driver',
    'PandokiaDB',
    'threadsafety',
    ]

import psycopg2 as db_module
import re

# from dbapi.  psycopg2 is level 2 (can use same db connection in
# multiple threads).
threadsafety = db_module.threadsafety


import pandokia.db

# debugging 
_tty = None
# _tty = open("/dev/tty","w")

import cStringIO as StringIO
import os

# use this when something is so specific to the database that you
# can't avoid writing per-database code
db_driver = 'psycopg2'

import re

class PandokiaDB(pandokia.db.where_dict_base) :

    IntegrityError = db_module.IntegrityError
    ProgrammingError = db_module.ProgrammingError
    OperationalError = db_module.OperationalError
    DatabaseError    = db_module.DatabaseError

    # name of this driver.  could be a constant.
    pandokia_driver_name = __module__.split('db_')[1]

    db = None

    def __init__( self, access_arg ) :
        self.db_access_arg = access_arg

    def open( self ) :
        if self.db is None :
            self.db = db_module.connect( ** ( self.db_access_arg ) )
            return

        # bug: see if the connection timed out, and reconnect it

    def start_transaction( self ) :
        if self.db is None :
            self.open()
        self.execute("START TRANSACTION")
        # bug: should we use one the options at
        # http://www.postgresql.org/docs/9.1/static/sql-start-transaction.html

    def commit(self):
        if self.db is None :
            return
        self.db.commit()

    def rollback(self):
        if self.db is None :
            return
        self.db.rollback()

    def rollback_or_reconnect(self):
        raise NotImplemented('rollback_or_reconnect not implemented')

    #
    # explain the query plan using the database-dependent syntax
    #
    def explain_query( self, text, query_dict=None ) :
        if self.db is None :
            self.open()
        f = StringIO.StringIO()
        c = self.execute( 'EXPLAIN '+ text, query_dict )
        for x in c :
            f.write(str(x))
        return f.getvalue()

    #
    # execute a query in a portable way
    # (this capability not offered by dbapi)
    #

    _pat_from = re.compile(':([a-zA-Z0-9_]*)')

    _pat_to = '%(\\1)s '

    def execute( self, statement, parameters = [ ] ) :
        if self.db is None :
            self.open()

        # convert the parameters, as necessary
        if isinstance(parameters, dict) :
            # dict does not need to be converted
            pass
        elif isinstance(parameters, list) or isinstance(parameters, tuple) :
            # list/tuple turned into a dict with string indexes
            tmp = { }
            for x in range(0,len(parameters)) :
                tmp[str(x+1)] = parameters[x]
            parameters = tmp
        elif parameters is None :
            parameters = [ ]
        else :
            # no other parameter type is valid
            raise self.ProgrammingError

        # for mysql, convert :xxx to %(xxx)s
        statement = self._pat_from.sub(self._pat_to, statement)

        # create a cursor, execute the statement
        c = self.db.cursor()

        # print parameters,"<br>"
        c.execute( statement, parameters )

        # return the cursor
        return c

    ## how much table space is this database using
    ## not portable to other DB
    def table_usage( self ) :
        c = self.execute("SELECT pg_database_size( :1 )", ( self.db_access_arg['database'], ) )
        return c.fetchone()[0]

    # 
    def next( self, sequence_name ) :
        if self.db is None :
            self.open()
        c = self.db.cursor()
        c.execute("select nextval('%s')"%sequence_name)
        return c.fetchone()[0]


'''
Ubuntu:

    sudo apt-get install postgresql-client
        gets a client

    sudo apt-get install python-psycopg2
        gets the python client

    sudo apt-get install postgresql
        gets a server

    su postgres

    psql postgres
        \password postgres
        ...enter a password...
            sets password for postgres database user

        create database pandokia;
        create user mark;
        grant all on database pandokia to mark ;

    /etc/postgresql
        config

    /var/lib/postgresql/8.4/main
        data?


Fedora:

    yum install postgresql
        client

    yum install python-psycopg2  
        python client

    yum install postgresql-server
        server

    su postgres
    initdb -D ~postgres/data

    su
    service postgresql start 
    
    su postgres

    psql postgres
        \password postgres
        ...enter a password...
            sets password for postgres database user


Create the database:

    su postgres
    psql postgres
        create database pandokia;
        create user mark;
        grant all on database pandokia to mark ;

        alter user NAME password 'PSWD';

Finding the config file:

    psql postgres
        show config_file;

    "pg_ctl reload" or "kill -HUP server" after editing config
    server is the process running "postmaster"
    (didn't work for me)


psql pandokia
    start the interactive client on the pandokia database


psql
    \d
        like show tables
    \l
        like show databases
    \d tablename
        like describe tablename
    \connect name
        like "use name"


'''
