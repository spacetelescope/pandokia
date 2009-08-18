#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import pandokia.common
import pandokia
import os.path
import sqlite3

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
        print "Specify which database to initialize with"
        print "    pdk initdb db"
        print "    pdk initdb qdb"
        return

    verbose = '-v' in args 

    if 'db' in args :
        # don't init the database if it already exists
        dbname = pandokia.cfg.dbdir+"/pdk.db"
        if os.path.exists(dbname) :
            sys.stderr.write( "database already exists: %s\n"%dbname )
            return 1

        # make the empty file so we don't get an error in open_db
        open(dbname,"w").close()

        # feed the sql commands to init the database
        db = pandokia.common.open_db()
        filename = getfile("initdb.sql")
        run_sql_file(db, filename, verbose)
        print "main db initialized"

    if 'qdb' in args :
        # don't init the database if it already exists
        dbname = pandokia.cfg.dbdir+"/pdk_query.db"
        if os.path.exists(dbname) :
            sys.stderr.write( "database already exists: %s\n"%dbname )
            return 1
        # make the empty file so we don't get an error in open_db
        open(dbname,"w").close()

        # feed the sql commands to init the database
        db = pandokia.common.open_qdb()
        filename = getfile("initqdb.sql")
        run_sql_file(db, filename, verbose)
        print "query db initialized"

    return 0

