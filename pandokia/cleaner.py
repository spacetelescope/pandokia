#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import time
import sys
import os
import pandokia.common


global db
db = pandokia.common.open_db()

def get_user_name() :
    # may need to do something more for ms windows
    return os.getlogin()

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


def clean_key_id(which, min_key_id=None, max_key_id=None, sleep=1 ) :
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

    if min_key_id is None :
        c = db.execute("SELECT MIN(key_id) FROM "+which)
        (min_key_id,) = c.fetchone()

    if max_key_id is None :
        c = db.execute("SELECT MAX(key_id) FROM "+which)
        (max_key_id,) = c.fetchone()

    print "max record number",max_key_id

    inc = 100000
    max_kills = 400

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

        if sleep is not None :
            print "sleep"
            time.sleep(sleep)

    print "done"
    print "end   clean key_id", which, time.time()


def clean_db(args) :

    if len(args) > 0 and args[0] == '--help' :
        print '''
pdk clean [ min_keyid [ max_keyid [ sleep_interval ] ] ]
'''
        return

    min_key_id = None
    max_key_id = None
    sleep = 1

    if len(args) > 0 :
        min_key_id=int(args[0])

    if len(args) > 1 :
        max_key_id=int(args[1])

    if len(args) > 2 :
        sleep = int(args[2])


    clean_key_id("result_log", min_key_id, max_key_id, sleep)
    clean_key_id("result_tda", min_key_id, max_key_id, sleep)
    clean_key_id("result_tra", min_key_id, max_key_id, sleep)
    clean_queries()

    db.close()


def block_last_record() :

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
# entry point:
#
# pdk delete_run testrun
#
def delete_run(args) :

    print "Deleting from database", pandokia.common.cfg.dbdir

    block_last_record()

    #
    if len(args) > 0 and args[0] == '--help' :
        print '''
pdk delete_run [ --mine ] 'name1' 'name2' 'name3'

    --mine 
        sticks 'user_YOURNAME_' in front of each test run, so you can
            pdk delete_run --mine '*'
        to delete all of your personal test runs

    name1, name2, ...
        names of test_runs to delete

'''
        return

    if len(args) > 0 and args[0] == '--mine' :
        user_name = get_user_name()
        args = [ 'user_' + user_name + '_' + x for x in args[1:] ]
    print 'args', args
    for x in args :
        if x == "*" :
            print "* is too dangerous - nothing done"
            return 1
    for name in args :
        print "ARG",name
        c = db.execute("SELECT name, valuable FROM distinct_test_run WHERE name GLOB ?",(name,))
        for (n,valuable) in c :
            print "name",n,"valuable",valuable
            if valuable != '0' :
                print "NAME",n," MARKED VALUABLE - NOT DELETED"
                continue
            new_delete(n)

def delete(args) :
    '''pdk delete -field value -otherfield othervalue ...

    deletes records from the database where all the parameters match

    This command can remove a subset of the records for a test run.
    It can also remove all the records for a test run, but leave
    the test run in the index as an empty dataset.

    The count of records in a test run will be incorrect until
    you update it.

    pdk delete -test_run foo -project bar -context baz -host xyzzy

    also accepts:

        -n      do not actually do it, just show the queries and 
                the query plan

        -wild   allow wildcards; some queries are dramatically
                inefficient when you use wildcards, so you have to
                actively ask to use them.  if you use * or ? and
                do not specify -wild, it implies -n

        -count  do not delete the records - just show how many are
                affected

'''
    import pandokia.helpers.easyargs as easyargs
    import pandokia.common as common
    opt, args = easyargs.get( 
        {
        '-test_run' : '=',
        '-project' : '=',
        '-context' : '=',
        '-host' : '=',
        '-status' : '=',
        '-n' : '',
        '-wild' : '',
        '-count' : '',
        }, 
        args 
    )

    if len(args) != 0 :
        print 'pdk delete does not take any non-flag arguments - you must have typed the command wrong'
        return 1

    dont = opt['-n']
    del opt['-n']

    wild = opt['-wild']
    del opt['-wild']

    count = opt['-count']
    del opt['-count']
    if count :
        dont = 1

    if '-test_run' in opt :
        opt['-test_run'] = common.find_test_run(opt['-test_run'])

    if len(opt) < 1 :
        print 'no args specified - nothing deleted'
        return 1

    lll = [ ]
    for x in sorted(opt.keys()) :
        v = opt[x]
        lll.append( ( x[1:], v ) )
        if not wild :
            if ( '*' in v ) or ( '?' in v ) :
                print '\nError: must use -wild for ',x,v,'\n'
                dont=1

    where_text, where_dict = common.where_tuple( lll )

    q1 = "INSERT INTO delete_queue SELECT key_id FROM result_scalar %s " % ( where_text, ) 
    q2 = "DELETE FROM result_scalar WHERE key_id IN ( SELECT key_id FROM result_scalar %s ) " % ( where_text, )

    if dont :
        print "q1",q1
        print "q2",q2
        for x in sorted(where_dict.keys()) :
            print "   ",x,where_dict[x]

        print "query plan 1:"
        print common.explain_query(q1, where_dict)

        print "query plan 2:"
        print common.explain_query(q2, where_dict)
        c = db.execute( "EXPLAIN QUERY PLAN " + q2, where_dict )

    if count :
        c = db.execute("SELECT count(*) FROM result_scalar %s" % (where_text,) , where_dict )
        print "total records",c.fetchone()[0]

    if not dont :
        block_last_record()
        c = db.execute( q1, where_dict )
        c = db.execute( q2 , where_dict )
        db.commit()

    return 0
        
def old_delete( name ) :
    print "NAME",name
    c = db.execute("SELECT min(key_id), max(key_id) FROM result_scalar WHERE test_run = ?",  (name,))
    kmin,kmax = c.fetchone() 
    print kmin, kmax
    print "DELETE ",name
    db.execute("DELETE FROM result_scalar WHERE test_run = ? ", (name,) )
    db.execute("DELETE FROM distinct_test_run WHERE name = ? ",(name,) )
    db.commit()

    clean_key_id("result_log", kmin, kmax, None)
    clean_key_id("result_tda", kmin, kmax, None)
    clean_key_id("result_tra", kmin, kmax, None)
    print "DONE ",name

def new_delete( name ) :
    c = db.execute("INSERT INTO delete_queue SELECT key_id FROM result_scalar WHERE test_run = ? ", (name,))
    c = db.execute("DELETE FROM distinct_test_run WHERE name = ?", (name,))
    db.commit()

def delete_background_step( n = 200 ) :
    start = time.time()
    db.execute("DELETE FROM result_scalar WHERE key_id IN ( SELECT key_id FROM delete_queue ORDER BY key_id ASC LIMIT ? ) ", (n,))
    db.execute("DELETE FROM result_tda    WHERE key_id IN ( SELECT key_id FROM delete_queue ORDER BY key_id ASC LIMIT ? ) ", (n,))
    db.execute("DELETE FROM result_tra    WHERE key_id IN ( SELECT key_id FROM delete_queue ORDER BY key_id ASC LIMIT ? ) ", (n,))
    db.execute("DELETE FROM result_log    WHERE key_id IN ( SELECT key_id FROM delete_queue ORDER BY key_id ASC LIMIT ? ) ", (n,))
    db.execute("DELETE FROM delete_queue  WHERE key_id IN ( SELECT key_id FROM delete_queue ORDER BY key_id ASC LIMIT ? ) ", (n,))
    end1 = time.time()
    db.commit()
    end2 = time.time()
    print "step - ",end1-start, end2-start

def delete_background( args ) :
    n = 20000
    ns = 200
    sleeptime=10
    # max records to delete
    if len(args) > 0 :
        n = int(args[0])
    # number of records in a single step
    if len(args) > 1 :
        ns = int(args[1])
    # sleep time between deleting chunks
    if len(args) > 2 :
        sleeptime=int(args[2])
    while n > 0 :
        db.commit()
        c=db.execute("SELECT count(*) FROM delete_queue")
        print c
        c = c.fetchone()
        print c
        if c is None :
            print "HOW?"
        (remaining,) = c
        print "remaining:",remaining
        if remaining <= 0 :
            return
        print "delete"
        delete_background_step( ns )
        print "sleep"
        n = n - ns
        time.sleep(sleeptime)

