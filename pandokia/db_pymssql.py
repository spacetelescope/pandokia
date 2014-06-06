#
# pandokia - a test reporting and execution system
# Copyright 2014, Association of Universities for Research in Astronomy (AURA) 
#
# pymssql database driver - for Microsoft SQL Server
#

###
### WARNING: pymssql can only have _one_ active cursor at a time.  This
### limits the portability of this database layer unless we work out
### a solution.
###
#
# Ideas:
#
# db.execute() returns a cursor.  Each cursor could track if it is
# still in use.  (i.e. It is in use until the __del__ is called.)
# Then when we call db.execute() and a cursor is already active, we
# make a new connection and return a cursor off the new connection.  
# This hoses up transactions, though...
#
# db.execute() returns a cursor.  Internally, we duplicate the
# functions of a cursor and fill it with c.fetchall() before
# returning it.  It may use a lot of memory for the list, but
# if you are aware of this and do not intend to process all
# the data, you might make a shorter query.
#
# db.execute() only has one cursor.  If it determines that the
# cursor is still in use when you run db.execute() again, it
# throws an exception.  Applications have to "del c" to get
# rid of the cursor before db.execute() again.
#


__all__ = [ 
    'db_module',
    'db_driver',
    'PandokiaDB',
    'thread_safe',
    ]

# http://pymssql.org/
# https://pypi.python.org/pypi/pymssql/2.1.0

import pymssql as db_module

# use this when something is so specific to the database that you
# can't avoid writing per-database code
db_driver = 'pymssql'

# from dbapi
thread_safe = db_module.threadsafety

import pandokia.db

# debugging 
_tty = None
# _tty = open("/dev/tty","w")

import os

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
        if access_arg.get('password',1) is None :
            raise Exception("password specified as None")
        self.db = db_module.connect( ** ( self.db_access_arg ) )

    def start_transaction( self ) :
        if self.db is None :
            self.open()
        self.execute("BEGIN TRANSACTION")

    def commit(self):
        if self.db is None :
            return
        self.db.commit()

    def rollback(self):
        if self.db is None :
            return
        self.db.rollback()

    #
    # execute a query in a portable way
    # (this capability not offered by dbapi)
    #

    _pat_from = re.compile(':([a-zA-Z0-9_]*)')

    _pat_to = '%(\\1)s '

    def execute( self, statement, parameters = [ ], db = None ) :
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

        if ( _tty is not None ) and not ( statement.startswith('EXPLAIN') ) :
            _tty.write("--------\nQUERY: %s\nparam %s\n"%(statement,str(parameters)))
            _tty.write(explain_query( statement, parameters ) +"\nWARN: ")
            c.execute("SHOW WARNINGS")
            for x in c :
                _tty.write(str(x)+"\n")
            _tty.write("\n\n\n")

        # print parameters,"<br>"
        c.execute( statement, parameters )

        # return the cursor
        return c

    ## how much table space is this database using, in bytes
    ## not portable to other DB
    def table_usage( self ) :
        c = self.db.cursor()
        c.execute("sp_spaceused")
        n = c.fetchone()
        num, unit = n[1].split()
        if unit == "KB" :
            unit=1024
        elif unit == "MB" :
            unit= 1024*1024
        elif unit == "GB" :
            unit = 1024*1024*1024
        return float(n[0]) * unit


##########
#
"""
MS SQL Server notes


show databases
    select name from master..sysdatabases

show tables
    select * from information_schema.tables

describe tablename
    exec sp_columns tablename

    sp_help @tablename


change password

    ALTER LOGIN username  WITH PASSWORD = 'newpassword' OLD_PASSWORD = 'oldpassword'

"""
