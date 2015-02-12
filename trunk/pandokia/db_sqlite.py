#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#

#
# sqlite3 database driver
#

__all__ = [
    'db_module',
    'db_driver',
    'PandokiaDB',
    'threadsafety',
    ]

# system imports
import os
import cStringIO

# need some common code
import pandokia.db

# The database engine is named "sqlite3" if it was installed with
# python, or "pyqslite2" if it was installed separately.
try :
    import sqlite3 as db_module
except ImportError :
    import pysqlite2.dbapi2 as db_module

# from dbapi
threadsafety = db_module.threadsafety

#
# Since we were in a hurry to get it working, we use certain sqlite3
# features:
#
# These sqlite features are:
#
# PRAGMA synchronous = NORMAL;
#   FULL = pause to wait for data to get to disk; guards against
#       db corruption in case of system crash, but slow
#   NORMAL = pause only at the most critical moments
#   OFF = hand off writes to the OS and continue; as much as 50
#       times faster than FULL, but if the OS crashes or you
#       lose power, the db might get corrupted.
#
# You would think that OFF might be a good choice because we don't do a
# lot of writes, but we have a problem once or twice a year that seems to
# be related to killing an import.
#
# db.text_factory = str
#   cause all strings to be extracted as str instead of unicode.
#
#   Some of the STSCI log files contain byte sequences that look like
#   invalid UTF-8 sequences.  It manages to insert the invalid UTF-8
#   into the database, but chokes on extracting them.  So, for now,
#   it's all 8 bit ASCII.  Or 8859-1 if you prefer...
#


# use this when something is so specific to the database that you
# can't avoid writing per-database code
db_driver = 'sqlite'

#
# The database interface object
#


class PandokiaDB(pandokia.db.where_dict_base) :

    IntegrityError = db_module.IntegrityError
    ProgrammingError = db_module.ProgrammingError
    OperationalError = db_module.OperationalError
    DatabaseError    = db_module.DatabaseError

    # name of this driver.  could be a constant.
    pandokia_driver_name = __module__.split('db_')[1]

    db = None

    def __init__( self, access_arg ) :
        if isinstance( access_arg, dict ) :
            access_arg['database'] = os.path.abspath( access_arg['database'] )
        else :
            access_arg = { "database" : os.path.abspath( access_arg ) }

        self.db_access_arg = access_arg

    def open( self ) :
        if self.db is None :
            self.db = db_module.connect( **self.db_access_arg )
            self.db.execute("PRAGMA synchronous = NORMAL;")
            self.db.text_factory = str;

            # must have case_sensitive_like so LIKE 'arf%' can use the
            # indexes.  With non-case-sensitive like, any LIKE clause
            # turns into a linear search of the table.
            self.db.execute("PRAGMA case_sensitive_like = true;")
            return

        # other database drivers may test for a timed-out connection here,
        # but sqlite is just an open file on the local disk.  There is no
        # timing out of connections
        return

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

    def rollback_or_reconnect(self):
        return self.rollback()
        # sqlite has no disconnect

    #
    # explain the query plan using the database-dependent syntax
    #
    def explain_query( self, text, query_dict=None ) :
        print "TEXT",text
        print "DICT", query_dict
        f = cStringIO.StringIO()
        c = self.execute( 'EXPLAIN QUERY PLAN '+ text, query_dict )
        for x in c :
            f.write(str(x))
        return f.getvalue()

    #
    # execute a query in a portable way
    # (this capability not offered by dbapi)
    #
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

        # for sqlite3, :xxx is already a valid parameter format, so no change is necessary

        # 
        c = self.db.cursor()
        c.execute( statement, parameters )

        return c

    # how much disk space is used
    def table_usage( self ) :
        return os.path.getsize(self.db_access_arg)

    # sqlite has no "next" function - it has implicit sequences and lastrowid
    next = None
