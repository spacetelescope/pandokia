#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#

#
# sqlite3 database driver
#

__all__ = [
    'commit',
    'db_module',
    'execute',
    'explain_query',
    'open_db',
    'pdk_db_driver',
    'where_dict',
    ]



# use this when something is so specific to the database that you
# can't avoid writing per-database code
pdk_db_driver = 'sqlite'


import os


#
# Since we were in a hurry to get it working, we use certain sqlite3
# features:
#
# These sqlite features are:
#
# PRAGMA synchronous = OFF;
#   FULL = pause to wait for data to get to disk; guards against
#       db corruption in case of system crash, but slow
#   NORMAL = pause only at the most critical moments
#   OFF = hand off writes to the OS and continue; as much as 50
#       times faster than FULL, but if the OS crashes or you
#       lose power, the db might get corrupted.
#   We are not doing many writes in this cgi, and power fail /
#   os crashes are pretty rare.  If our db gets hosed, we'll
#   either live without the old data or rebuild it.
#
# db.text_factory = str
#   cause all strings to be extracted as str instead of unicode.
#
#   Some of the STSCI log files contain byte sequences that look like
#   invalid UTF-8 sequences.  It manages to insert the invalid UTF-8
#   into the database, but chokes on extracting them.  So, for now,
#   it's all 8 bit ASCII.  Or 8859-1 if you prefer...
#


# The database engine is named "sqlite3" if it was installed with
# python, or "pyqslite2" if it was installed separately.
try :
    import sqlite3 as db_module
except ImportError, e :
    import pysqlite2.dbapi2 as db_module


xdb=None

def open_db ( access_str=None ):
    global xdb
    if access_str is None :
        if xdb is not None :
            return xdb
        import pandokia.config
        access_str = pandokia.config.db_arg+"/pdk.db"

    if not os.path.exists(access_str) :
        print "NO DATABASE FILE",access_str

    xdb = db_module.connect(access_str,timeout=10)
        # timeout is how long to wait if the db is locked; mostly
        # only an issue if an import is happening

    xdb.execute("PRAGMA synchronous = OFF;")
    xdb.text_factory = str;

    # must have case_sensitive_like so LIKE 'arf%' can use the
    # indexes.  With non-case-sensitive like, any LIKE clause
    # turns into a linear search of the table.
    xdb.execute("PRAGMA case_sensitive_like = true;")
    return xdb

#
# generic commit so the user doesn't need to grab the db handle

def commit( db = None ) :
    if db is None :
        if xdb is None :
            open_db()
        db = xdb
    db.commit()

#
# explain the query plan using the database-dependent syntax
#
def explain_query( text, query_dict ) :
    f = cStringIO.StringIO()
    c = execute( 'EXPLAIN QUERY PLAN '+ text, query_dict, xdb )
    for x in c :
        f.write(str(x))
    return f.getvalue()


#
# execute a query in a portable way
# (this capability not offered by dbapi)
#

def execute( statement, parameters = [ ], db = None ) :

    # choose the default database
    if db is None :
        if xdb is None :
            open_db()
        db = xdb

    # convert the parameters, as necessary
    if isinstance(parameters, dict) :
        # dict does not need to be converted
        pass
    elif isinstance(parameters, list) or isinstance(parameters, tuple) :
        # list/tuple turned into a dict with string indexes
        parameters = { str(x+1) : parameters[x] for x in range(0,len(parameters)) }
    elif parameters is None :
        parameters = [ ]
    else :
        # no other parameter type is valid
        raise db_module.ProgrammingError

    # for sqlite3, :xxx is already a valid parameter format, so no change is necessary

    # 
    c = db.cursor()
    c.execute( statement, parameters )

    return c


#
# use the glob-type where_dict
#

from pandokia.db import where_dict

