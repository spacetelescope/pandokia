#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import time
import sys
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
    # which is the name of a table that we want to clean.  We will call
    # this function once for each of the tables result_log, result_tda,
    # result_tra, and result_tca (when we get that table)
    #
    # The point of this loop is to avoid locking the database for more
    # than a few seconds.  sqlite locks the entire database when it
    # does something, so if I try to process millions of records
    # in a single transaction, other users may get a database timeout.
    #
    # Instead, we flip through the key_id in the table, finding records
    # to delete.  By limiting each search to a range, we keep the
    # select from holding a read lock for too long.  By collecting
    # fairly small piles of records to delete, we keep it from holding
    # a write lock for too long.
    #
    # Empirically, the database cleaning takes longer, but other
    # users are able to get in between transactions.

    print "start clean key_id", which, time.time()

    c = db.execute("SELECT MIN(key_id) FROM "+which)
    (min_key_id,) = c.fetchone()

    c = db.execute("SELECT MAX(key_id) FROM "+which)
    (max_key_id,) = c.fetchone()

    print "max record number",max_key_id

    inc = 100000
    max_kills = 200

    kill  = [ 1 ] 
    while min_key_id < max_key_id :
        print "search",min_key_id
        kill = [ ]

        # sql is safe - 'which' is a parameter I passed in as one of a few constants
        c = db.execute("SELECT DISTINCT key_id FROM "+which + " WHERE key_id >= ? and key_id <= ?", (min_key_id,min_key_id+inc))

        # set the min key number to the next value to use, in case we don't find anything
        # in this query
        min_key_id = min_key_id + inc

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
                if len(kill) >= max_kills :
                    # when the batch is long enough, leave the loop and do some deleteing
                    break
                min_key_id=key_id

        c1 = None
        c = None

        # Delete all the key_id's that are in the kill list.
        if len(kill) > 0 :
            print "kill"
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

    #

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
        c = db.execute("SELECT name FROM distinct_test_run WHERE name GLOB ?",(x,))
        for (y,) in c :
            print "DELETE ",y
            db.execute("DELETE FROM result_scalar WHERE test_run = ? ", (y,) )
            db.execute("DELETE FROM distinct_test_run WHERE name = ? ",(y,) )
            db.commit()
            print "DONE ",y

    db.close()

    print "don't forget to 'pdk clean' "


def get_user_name() :
    # may need to do something more for ms windows
    return os.getlogin()
