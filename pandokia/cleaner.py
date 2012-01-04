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

def delete_background_step( n = 200 ) :
    start = time.time()
    c = pdk_db.execute("SELECT key_id FROM delete_queue LIMIT :1 ",(n,) )
    keys = tuple( [ x[0] for x in c ] )
    # print "delete ",keys
    parm = ', '.join( [ ':%d'%(n+1) for n in range(0, len(keys) ) ] )
    # print parm
    
    pdk_db.execute("DELETE FROM result_scalar WHERE key_id IN ( %s )" % parm, keys )
    pdk_db.execute("DELETE FROM result_tda    WHERE key_id IN ( %s )" % parm, keys )
    pdk_db.execute("DELETE FROM result_tra    WHERE key_id IN ( %s )" % parm, keys )
    pdk_db.execute("DELETE FROM result_log    WHERE key_id IN ( %s )" % parm, keys )
    pdk_db.execute("DELETE FROM delete_queue  WHERE key_id IN ( %s )" % parm, keys )

    end1 = time.time()
    pdk_db.commit()

    end2 = time.time()
    print "step - ",end1-start, end2-start
    return len(keys)

def delete_background( args = [ ] ) :
    # defaults
    n = 1000000000 # 1 billion records; lazy way to say "infinite"
    ns = 200
    sleeptime=0

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
        c=pdk_db.execute("SELECT count(*) FROM delete_queue")
        # print c
        c = c.fetchone()
        # print c
        if c is None :
            print "HOW?"
        (remaining,) = c
        print "remaining:",remaining
        if remaining <= 0 :
            return
        deleted_count = delete_background_step( ns )
        n = n - ns
        if deleted_count < ns :
            # we ran out - ok to stop now
            break
        if sleeptime > 0 :
            print "sleep after ",deleted_count
            time.sleep(sleeptime)
        # commit each time through the loop
        pdk_db.commit()

    pdk_db.commit()

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
    pdk_db.execute("INSERT INTO query_id ( time, expires, username, notes ) values ( :1, :2, 'nobody', 'placeholder for cleaner' )", (now,now+10))

    # delete the records related to the query
    pdk_db.execute("DELETE FROM query WHERE qid IN ( SELECT qid FROM query_id WHERE expires > 0 AND expires < :1 ) ", (now,))

    # delete 
    pdk_db.execute("DELETE FROM query_id WHERE expires > 0 AND expires < :1 ", ( now, ) )

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
    while min_key_id < max_key_id :
        print "search",min_key_id
        kill = [ ]

        # sql is safe - 'which' is a parameter I passed in as one of a few constants
        c = pdk_db.execute("SELECT DISTINCT key_id FROM "+which + " WHERE key_id >= :1 and key_id <= :2", (min_key_id,min_key_id+inc))

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
            c1 = pdk_db.execute("SELECT count(*) FROM result_scalar WHERE key_id = :1",(key_id,))
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
                    pdk_db.execute("DELETE FROM "+which+" WHERE key_id = :1",(key_id,))

            # Commit!  The whole point of deleting in chunks is so that a specific transaction
            # does not grow too large.  Also, we don't keep the database locked for so long.    
            # (sqlite only locks the entire database, not tables or rows.)
            pdk_db.commit()

        print "        ",time.time()-tyme

        if sleep is not None :
            print "sleep"
            time.sleep(sleep)

    print "done"
    print "end   clean key_id", which, time.time()


# This is the old cleaner.  You give a min/max key_id.  For each key_id
# in that range, it deletes any tda/tra/log records that do not have a
# match in result_scalar.  This is still here because it is a basic "make
# it right" function, but it is very slow.
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
        print 'pdk delete does not take any non-flag arguments - you must have typed the command wrong'
        return 1

    wild = opt['-wild']
    del opt['-wild']

    count = opt['-count'] | opt['-c']
    del opt['-count']
    del opt['-c']

    if not '-test_run' in opt :
        print "You really have to specify -test_run"
        return 1

    opt['-test_run'] = [ common.find_test_run(x) for x in opt['-test_run'] ]
    print "TEST RUN", opt['-test_run']

    for x in opt['-test_run'] :
        if check_valuable(x) :
            print "test run %s is marked valuable - cannot delete" % s
            dont=1

    lll = [ ]
    for x in sorted(opt.keys()) :
        v = opt[x]
        lll.append( ( x[1:], v ) )
        if not wild :
            print x,v
            if ( '*' in v ) or ( '?' in v ) :
                print '\nError: must use -wild for ',x,v,'\n'
                dont=1

    if dont :
        return

    where_str, where_dict = pdk_db.where_dict( lll )

    if count :
        c = pdk_db.execute("SELECT count(*) FROM result_scalar %s" % (where_str,) , where_dict )
        print "total records",c.fetchone()[0]
        return

    delete_by_query( where_str, where_dict )

    return 0
