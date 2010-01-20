#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import time
import sys
import sqlite3
import os
import pandokia.common


#
# a qid identifies an arbitrarily chosen group of test results.  The CGI
# creates them in response to some queries, but we need some way to get
# rid of them.
#
def clean_queries() :

    qdb=pandokia.common.open_qdb()

    old = time.time() - 60*86400
    print "start delete old queries", time.time(), int(old)

    qdb.execute("DELETE FROM query_id WHERE time < ? ", ( old, ) )
    qdb.commit()

    print "end  delete old queries", time.time(), int(old)


def clean_key_id(which) :
    print "start clean key_id", which, time.time()

    min = 0

    kill  = [ 1 ] 
    while len(kill) > 0 :
        kill = [ ]
        print "search"
        # sql is safe - 'which' is a parameter I passed in as one of a few constants
        c = db.execute("SELECT DISTINCT key_id FROM "+which + " WHERE key_id >= ?", (min,))
        tyme = time.time()
        # This is a loop over the key_id's that are greater than the minimum key_id
        # that we are looking at.  The key_id's are chosen from the attribute table
        # that we are cleaning.
        for (key_id,) in c :
            # For each key_id, see if there is a result_scalar entry for that key_id.  If
            # there is, leave it.  If not, delete the attribute entries.
            c1 = db.execute("SELECT count(*) FROM result_scalar WHERE key_id = ?",(key_id,))
            (count,) = c1.fetchone()
            if count == 0 :
                # don't just delete it now - save up a batch to do all at once
                kill.append(key_id)
                if len(kill) >= 100 :
                    # when the batch is long enough, leave the loop and do some deleteing
                    break
            min=key_id
        print "        ",time.time()-tyme

        c1 = None
        c = None

        # Delete all the key_id's that are in the kill list.
        print "kill",kill
        tyme = time.time()
        for key_id in kill :
                # sql is safe - which is a parameter I passed in as one of a few constants
                db.execute("DELETE FROM "+which+" WHERE key_id = ?",(key_id,))

        # Commit!  The whole point of deleting in chunks is so that a specific transaction
        # does not grow too large.  Also, we don't keep the database locked for so long.    
        # (sqlite only locks the entire database, not tables or rows.)
        db.commit()
        print "        ",time.time()-tyme

    print "done"
    print "end   clean key_id", which, time.time()


def clean_db(args) :

    global db
    db = pandokia.common.open_db()

    clean_key_id("result_log")
    clean_key_id("result_tda")
    clean_key_id("result_tra")
    clean_queries()

    db.close()


#
# entry point:
#
# pdk delete_run testrun
#
def delete_run(args) :
    global db
    db = pandokia.common.open_db()

    print "Deleting from database", pandokia.common.cfg.dbdir

    # This is preserving the integer primary key on the result_scalar table.  If you 
    # delete the last record, then insert a new one, the same primary key might get used again.
    # We can't allow that because the primary key is used to join across tables, so we
    # never allow the last record to be deleted.  
    #
    # We do this by always inserting a record that we are not going to delete.  We only
    # need one, though, at the end of the table.
    db.execute("DELETE FROM result_scalar where test_run IS NULL AND project IS NULL AND host IS NULL AND context IS NULL AND test_name IS NULL ")

    db.execute("INSERT INTO result_scalar ( test_run, project, host, context, test_name ) VALUES (NULL,NULL,NULL,NULL,NULL)")

    if ( len(args) > 0 ) and ( args[0] == "--wild" ) :
        args = args[1:]
        if args[0] == '--mine' :
            user_name = get_user_name()
            args = [ 'user_' + user_name + '_' + x for x in args[1:] ]
        print 'args', args
        for x in args :
            if x == "*" :
                print "* is too dangerous - nothing done"
                db.close()
                return 1
        for x in args :
            print "DELETE ",x
            db.execute("DELETE FROM result_scalar WHERE test_run GLOB ? ", (x,) )
            print "DONE ",x
            db.commit()
            print "DONE COMMIT"
        pass
    else :
        for x in args :
            print "DELETE ",x
            db.execute("DELETE FROM result_scalar WHERE test_run = ? ", (x,) )
            print "DONE ",x
            db.commit()
            print "DONE COMMIT"

    db.close()

    print "don't forget to 'pdk clean' "


def get_user_name() :
    # may need to do something more for ms windows
    return os.getlogin()
