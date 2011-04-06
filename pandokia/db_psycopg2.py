#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#

import os

######
#--#--# DB
import psycopg2 as db_module
import re

xdb=None

def open_db ( access_arg=None ):
    global xdb
    if access_arg is None :
        if xdb is not None :
            return xdb
        import pandokia
        access_arg = pandokia.cfg.db_arg

    xdb = db_module.connect(access_arg)
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
    c = execute( 'EXPLAIN '+ text, query_dict, xdb )
    for x in c :
        f.write(str(x))
    return f.getvalue()


#
# execute a query in a portable way
# (this capability not offered by dbapi)
#

pat_from = ':([a-zA-Z0-9_]*)'

pat_to = '%(\\1)s '

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
        raise sqlite3.ProgrammingError

    # for psycopg2, convert :xxx to %(xxx)s
    statement = re.sub(pat_from, pat_to, statement)

    # create a cursor, execute the statement
    c = db.cursor()
    c.execute( statement, parameters )

    # return the cursor
    return c


from pandokia.db import where_dict

