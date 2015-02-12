#
# pandokia - a test reporting and execution system
# Copyright 2009, 2011 Association of Universities for Research in Astronomy (AURA) 
#
# Theory behind deletions:
#
# When you delete a set of records, you delete it from the table
# result_scalar and add the key_id to delete_queue.  You did not
# delete the tda/tra/log entries, because of performance issues -- it
# takes a lot longer to find/delete all that stuff, so we leave it
# for now.
#
# Later, you run the command "pdk clean".  It finds key_id in delete_queue
# and removes tda/tra/log entries with that key_id.  This takes longer,
# but nobody is sitting around waiting for it to happen.  (Notably, the
# web server does not time out the CGI for taking too long.)
#
# 
# 

import time
import sys
import os
import pandokia.common

import pandokia

pdk_db = pandokia.cfg.pdk_db

##########
#
# function that does the delete, given a query that identifies the
# records we no longer want.
#

def delete_by_query( where_str, where_dict ) :
    sys.stdout.flush()
    c = pdk_db.execute("INSERT INTO delete_queue SELECT key_id FROM result_scalar %s"%where_str, where_dict)
    c = pdk_db.execute("DELETE FROM result_scalar %s"%where_str, where_dict)
    pdk_db.commit()


# we have to refuse to delete test runs that are valuable; this tool is
# used by the higher levels, but not in delete_by_query.

def check_valuable(test_run) :
    c = pdk_db.execute("SELECT valuable FROM distinct_test_run WHERE test_run = :1",(test_run,))

    # this trick discovers valuable=0 even if it is not in the distinct_test_run table
    valuable = 0
    for x in c :
        valuable, = x

    valuable = int(valuable)
    return valuable


##########
#
# implementation of "pdk clean"
#

def delete_background_step( n = 200, verbose=False ) :
    start = time.time()
    if verbose :
        print "select"
    c = pdk_db.execute("SELECT key_id FROM delete_queue LIMIT :1 ",(n,) )
    keys = tuple( [ x[0] for x in c ] )

    if len(keys) == 0 :
        if verbose :
            print "no more to delete"
        return 0

    # print "delete ",keys
    parm = ', '.join( [ ':%d'%(n+1) for n in range(0, len(keys) ) ] )
    if verbose:
        print parm
    
    if verbose :
        print "result_scalar"
    pdk_db.execute("DELETE FROM result_scalar WHERE key_id IN ( %s )" % parm, keys )
    if verbose :
        print time.time() - start
        print "result_tda"
    pdk_db.execute("DELETE FROM result_tda    WHERE key_id IN ( %s )" % parm, keys )
    if verbose :
        print time.time() - start
        print "result_tra"
    pdk_db.execute("DELETE FROM result_tra    WHERE key_id IN ( %s )" % parm, keys )
    if verbose :
        print time.time() - start
        print "result_log"
    pdk_db.execute("DELETE FROM result_log    WHERE key_id IN ( %s )" % parm, keys )
    if verbose :
        print time.time() - start
        print "delete_queue"
    pdk_db.execute("DELETE FROM delete_queue  WHERE key_id IN ( %s )" % parm, keys )
    if verbose:
        print time.time() - start
        print "commit"

    # commit here because we want to do the operation in little chunks
    # instead of one massive transaction.
    pdk_db.commit()

    return len(keys)

def delete_background( args = [ ], verbose = False ) :
    # defaults

    # max_delete is 2 billion records - lazy way to say "infinite".
    # We have a settable limit so you can run partial deletes,
    # instead of hogging the database access.  e.g. You could
    # use a cron jobs to delete 10k records every hour.
    max_delete = 2000000000

    # max_per_step is how many records to delete in a single step.
    # This is limited by how much your database can tolerate in
    # the WHERE clauses in delete_background_step.  If using
    # sqlite, it can also be an issue because of keeping the
    # database locked during the transaction.
    max_per_step = 200

    # How long to wait between steps of the delete.  In sqlite,
    # this can create windows where other database users can
    # get access in between our transactions.
    sleeptime=0

    # parse args

    # max records to delete
    if len(args) > 0 :
        max_delete = int(args[0])

    # number of records in a single step
    if len(args) > 1 :
        max_per_step = int(args[1])

    # sleep time between deleting chunks
    if len(args) > 2 :
        sleeptime=int(args[2])

    # initialize remaining.  This count takes some substantial time in
    # some databases, so we do it once at the beginning and adjust
    # the value.  (We don't really need it - it is just to show the
    # user how much we have left to do.)
    c=pdk_db.execute("SELECT count(*) FROM delete_queue")
    (remaining,) = c.fetchone()
    print "remaining:",remaining

    # when did we start
    start_time = time.time()

    total_deletes = min( remaining, max_delete )

    total_deleted = 0

    while 1 :
        print "remaining:",remaining

        deleted_count = delete_background_step( max_per_step, verbose )
        if deleted_count == 0 :
            break

        remaining = remaining - deleted_count
        total_deleted = total_deleted + deleted_count

        if total_deleted >= max_delete :
            # we ran out - ok to stop now
            break

        if sleeptime > 0 :
            print "sleep after ",deleted_count
            time.sleep(sleeptime)

        time_so_far = time.time() - start_time
        time_per_record = float(time_so_far) / total_deleted
        print "time so far", time_so_far
        print "time/record", time_per_record
        print "est remain ", remaining * time_per_record

    print "done"
    return 0

##########
#

def block_last_record() :

    # This is preserving the integer primary key on the result_scalar table.  If you 
    # delete the last record, then insert a new one, the same primary key might get used again.
    # We can't allow that because the primary key is used to join across tables, so we
    # never allow the last record to be deleted.  
    #
    # We do this by always inserting a record that we are not going to delete.  We only
    # need one, though, at the end of the table.
    pdk_db.execute("DELETE FROM result_scalar where test_run IS NULL AND project IS NULL AND host IS NULL AND context IS NULL AND test_name IS NULL ")
    pdk_db.execute("INSERT INTO result_scalar ( test_run, project, host, context, test_name ) VALUES (NULL,NULL,NULL,NULL,NULL)")


##########
#
# a qid identifies an arbitrarily chosen group of test results.  The CGI
# creates them in response to some queries, but we need some way to get
# rid of them.
#
def clean_queries() :

    now = time.time()
    print "start delete old queries", now

    # placeholder so we don't re-use any of the deleted sequence numbers
    pdk_db.execute("INSERT INTO query_id ( time, expires, username, notes ) values ( :1, :2, 'nobody', 'placeholder for cleaner' )", (now,now+1000))

    c = pdk_db.execute("SELECT MIN(time) FROM query_id")
    mt, = c.fetchone()
    mt = int(mt)

    # do the delete in reasonably large chunks, rather than one at a
    # time or one giant transaction
    while mt < now :

        # get a bunch of records
        c = pdk_db.execute("SELECT qid FROM query_id WHERE  expires > 0 AND expires < :1 LIMIT 400", (mt,) )
        l = [ ]

        # make a list of the qids
        for x, in c:
            l.append(str(int(x)))

        # if none, move on to the next time interval
        if len(l) == 0 :
            mt = mt + 43200 # half day
            continue
        
        # make a list for the IN (...) clause
        l = ','.join(l)
        
        # delete both and commit together
        c = pdk_db.execute("DELETE FROM query    WHERE qid IN ( %s )" % l)
        c = pdk_db.execute("DELETE FROM query_id WHERE qid IN ( %s ) " % l )
        pdk_db.commit()


##########
# 
# This is the old delete code.  It deletes tda/tra/logs that do not have
# a primary record in result_scalar.  We don't use this any more because
# it is really slow, but it is still here because you can use the function
# clean_db() to get rid of junk tda/tra/logs if you ever manage to get
# the tables inconsistent somehow.
#
# (Yes, I know about constraints, but the point is to improve performance
# by delaying some of the deletes.)
#

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
        c = pdk_db.execute("SELECT MIN(key_id) FROM "+which)
        (min_key_id,) = c.fetchone()

    if max_key_id is None :
        c = pdk_db.execute("SELECT MAX(key_id) FROM "+which)
        (max_key_id,) = c.fetchone()

    print "max record number",max_key_id

    inc = 100000
    max_kills = 400

    kill  = [ 1 ] 

    if 1 :

        # sql is safe - 'which' is a parameter I passed in as one of a few constants
        c = pdk_db.execute("SELECT DISTINCT key_id FROM "+which + " WHERE key_id >= :1 ", (min_key_id, ) )

        # set the min key number to the next value to use, in case we don't find anything
        # in this query
        min_key_id = min_key_id + inc

        tyme = time.time()

        n = 0
        d = 0

        # This is a loop over the key_id's that are greater than the minimum key_id
        # that we are looking at.  The key_id's are chosen from the attribute table
        # that we are cleaning.
        for (key_id,) in c :
            # For each key_id, see if there is a result_scalar entry for that key_id.  If
            # there is, leave it.  If not, delete the attribute entries.
            c1 = pdk_db.execute("SELECT count(*) FROM result_scalar WHERE key_id = :1",(key_id,))
            (count,) = c1.fetchone()
            if count == 0 :
                pdk_db.execute("DELETE FROM "+which+" WHERE key_id = :1",(key_id,))
                d = d + 1
                if d > 100 :
                    print "deleted",key_id

            n = n + 1

            if n > 10000 :
                # Commit!  The whole point of deleting in chunks is so that a specific transaction
                # does not grow too large.  Also, we don't keep the database locked for so long.    
                # (sqlite only locks the entire database, not tables or rows.)
                pdk_db.commit()

                n = 0
                print "        ",time.time()-tyme, "  key_id", key_id

    print "done"
    print "end   clean key_id", which, time.time()


# This is the old cleaner.  You give a min/max key_id.  For each key_id
# in that range, it deletes any tda/tra/log records that do not have a
# match in result_scalar.  This is still here because it is a basic "make
# it right" function, but it is very slow.
def clean_db(args) :

    if len(args) > 0 and args[0] == '--help' :
        print '''
pdk clean_db [ min_keyid [ max_keyid [ sleep_interval ] ] ]
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


##########
#
# command line delete
#

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

        -wild   allow wildcards; some queries are dramatically
                inefficient when you use wildcards, so you have to
                actively ask to use them.  if you use * or ?, you
                must specify -wild

        -count  do not delete the records - just show how many are
                affected

'''
    import pandokia.helpers.easyargs as easyargs
    import pandokia.common as common
    opt, args = easyargs.get( 
        {
        '-test_run' : '=+',
        '-project' : '=+',
        '-context' : '=+',
        '-host' : '=+',
        '-status' : '=+',
        '-wild' : '',
        '-count' : '',
        '-c' : '',
        }, 
        args 
    )

    dont = 0

    if len(args) != 0 :
        if not '-test_run' in opt :
            opt['-test_run'] = args
        else :
            print "error: -test_run and non-option args used together"

    wild = opt['-wild']
    del opt['-wild']

    count = opt['-count'] | opt['-c']
    del opt['-count']
    del opt['-c']

    if not '-test_run' in opt :
        print "You really have to specify -test_run"
        return 1

    # expand wild cards in test run
    lll = [ ]
    for x in opt['-test_run'] :
        lll = lll + common.expand_test_run(x)
    opt['-test_run'] = lll

    # 
    if not count :
        lll = [ ]
        for x in opt['-test_run'] :
            if check_valuable(x) :
                print "test run %s is marked valuable - cannot delete" % x
            else :
                lll.append(x)

    #
    opt['-test_run'] = lll

    if len(lll) == 0 :
        # print "No deleteable test runs found"
        dont = 1

    lll = [ ]
    for x in sorted(opt.keys()) :
        if x == '-test_run' :
            continue

        v = opt[x]
        lll.append( ( x[1:], v ) )
        if not wild :
            if ( '*' in v ) or ( '?' in v ) or ( '%' in v ) :
                print '\nError: must use -wild for ',x,v,'\n'
                dont=1

    if dont :
        return

    for x in opt['-test_run'] :
        where_str, where_dict = pdk_db.where_dict( lll + [ ( 'test_run', x ) ] )
    
        if count :
            c = pdk_db.execute("SELECT count(*) FROM result_scalar %s" % (where_str,) , where_dict )
            print x, c.fetchone()[0]

        else :
            print x
            delete_by_query( where_str, where_dict )

        recount( [ x ] , verbose=0 )

    return 0

##########
#
# count the number of records in each test run
#

def recount( args, verbose=1 ) :
    if len(args) == 0 :
        args = [ '*' ]
    elif args[0] == '-z' :
        args = [ ]
        c = pdk_db.execute("SELECT test_run FROM distinct_test_run WHERE record_count = 0 OR record_count is NULL")
        for x, in c :
            args.append(x)

    for test_run in args :
        print "counting",test_run
        test_run = pandokia.common.find_test_run( test_run )
        where_text, where_dict = pdk_db.where_dict( [ ( 'test_run', test_run ) ] )
        c = pdk_db.execute("SELECT test_run FROM distinct_test_run " + where_text, where_dict )
        found = 0
        for test_run, in c :
            found = 1
            if verbose :
                print test_run, 
            n = recount_test_run( test_run )
            if verbose :
                print n
        if not found :
            if verbose :
                print "no test run found matching",test_run

def recount_test_run( test_run ) :
    c = pdk_db.execute("SELECT COUNT(*), MIN(start_time), MAX(end_time) FROM result_scalar WHERE test_run = :1",(test_run,))
    x = c.fetchone()
    count = x[0]
    if count == 0 :
        pdk_db.execute("DELETE FROM distinct_test_run WHERE test_run = :1",(test_run,))
    else :
        pdk_db.execute("UPDATE distinct_test_run SET record_count = :1, min_time = :2, max_time = :3 WHERE test_run = :4 ", 
            (count, x[1], x[2], test_run) )
    pdk_db.commit()
    return count

