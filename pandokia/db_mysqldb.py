#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#

#
# mysql database driver
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


# debugging 
_tty = None
# _tty = open("/dev/tty","w")

import cStringIO as StringIO
import os

# use this when something is so specific to the database that you
# can't avoid writing per-database code
pdk_db_driver = 'mysqldb'



import MySQLdb as db_module
import re

# This is the cached open database connection
_xdb=None

def open_db ( access_arg=None ):
    global _xdb
    if access_arg is None :
        if _xdb is not None :
            return _xdb
        import pandokia
        access_arg = pandokia.cfg.db_arg

    _xdb = db_module.connect( **access_arg )
    return _xdb

#
# generic commit so the user doesn't need to grab the db handle

def commit( db = None ) :
    if db is None :
        if _xdb is None :
            open_db()
        db = _xdb
    db.commit()

#
# explain the query plan using the database-dependent syntax
#
def explain_query( text, query_dict ) :
    f = StringIO.StringIO()
    c = execute( 'EXPLAIN EXTENDED '+ text, query_dict, _xdb )
    for x in c :
        f.write(str(x))
    return f.getvalue()


#
# execute a query in a portable way
# (this capability not offered by dbapi)
#

_pat_from = re.compile(':([a-zA-Z0-9_]*)')

_pat_to = '%(\\1)s '

def execute( statement, parameters = [ ], db = None ) :

    # choose the default database
    if db is None :
        if _xdb is None :
            open_db()
        db = _xdb

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

    # for mysql, convert :xxx to %(xxx)s
    statement = _pat_from.sub(_pat_to, statement)

    # create a cursor, execute the statement
    c = db.cursor()
    if _tty is not None and not statement.startswith('EXPLAIN') :
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


from pandokia.db import where_dict

