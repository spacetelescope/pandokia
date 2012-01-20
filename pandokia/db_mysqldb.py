#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#
# mysql database driver
#

__all__ = [ 
    'db_module',
    'db_driver',
    'PandokiaDB',
    ]

import MySQLdb as db_module

import pandokia.db

# debugging 
_tty = None
# _tty = open("/dev/tty","w")

import cStringIO as StringIO
import os

# use this when something is so specific to the database that you
# can't avoid writing per-database code
db_driver = 'mysqldb'

import re

class PandokiaDB(pandokia.db.where_dict_base) :

    IntegrityError = db_module.IntegrityError
    ProgrammingError = db_module.ProgrammingError

    db = None

    def __init__( self, access_arg ) :
        self.db_access_arg = access_arg

    def open( self ) :
        self.db = db_module.connect( ** ( self.db_access_arg ) )

    def commit(self):
        if self.db is None :
            return
        self.db.commit()

    def rollback(self):
        if self.db is None :
            return
        self.db.rollback()

    #
    # explain the query plan using the database-dependent syntax
    #
    def explain_query( self, text, query_dict ) :
        if self.db is None :
            self.open()
        f = StringIO.StringIO()
        c = self.execute( 'EXPLAIN EXTENDED '+ text, query_dict )
        for x in c :
            f.write(str(x))
        return f.getvalue()

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

    ## how much table space is this database using
    ## not portable to other DB
    def table_usage( self ) :
        '''sum of sizes from SHOW TABLE STATUS'''
        if self.db is None :
            self.open()
        c = self.db.cursor()
        c.execute("show table status")
        tables = 0
        indexes = 0
        for x in c :
            tables = tables + x[6]
            indexes = indexes + x[8]

        return tables + indexes

    # mysql does not use database sequences because it can do auto-increments fields
    next = None
