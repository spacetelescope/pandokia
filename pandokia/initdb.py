#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import pandokia.common
import pandokia
import os.path

sqlite3 = pandokia.common.get_db_module()

# find a data file that is in the same directory as where
# our code is.
def getfile(n) :
    return os.path.dirname(__file__) + "/" + n

# execute a file of sql statements in a specific database
def run_sql_file( db, filename, verbose ) :
    f = open(filename,"r")
    while 1 :
        # this bit of code reads lines to get a complete statement.
        stmt = f.readline()
        if stmt == "" :
            break
        while not sqlite3.complete_statement(stmt) :
            l = f.readline()
            stmt = stmt + l

        # verbosely say it
        if verbose :
            print "---"
            print stmt

        # execute the statement.  Since we are only using create table,
        # create index, and so on, we don't need to look at the cursor
        c = db.execute(stmt)
        if verbose :
            for x in c :
                print x

    f.close()
        

def run(args) :
    if len(args) == 0 :
        print "The database directory is "
        print "   ",pandokia.cfg.dbdir
        print ""

    verbose = '-v' in args 

    # warn if the database already exists - you may want to create the database file
    # and do things to the empty database (e.g. sqlite pragma auto_vacuum) before
    # creating the table
    dbname = pandokia.cfg.dbdir+"/pdk.db"
    if os.path.exists(dbname) :
        sys.stderr.write( "warning: database already exists: %s\n"%dbname )

    # make the empty file so we don't get an error in open_db
    open(dbname,"w").close()

    # feed the sql commands to init the database
    db = pandokia.common.open_db()
    filename = getfile("initdb.sql")
    run_sql_file(db, filename, verbose)
    print "db initialized"

    return 0

