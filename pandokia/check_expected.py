#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
# check_expected - check that expected tests exist in a test run
#
# check_expected test_run_type test_run_to_check
#

import sys
import os
import string
import urllib
import datetime
import pandokia.common as common

def run(args) :

    verbose = 1 # bug: I know there is no way to set it

    try :
        test_run_type = args[0]
        test_run = args[1]
    except :
        print "can't get args"
        print "gen_expected test_run_type test_run_to_check"
        print " test_run_to_check is the name of a test run to check"
        sys.exit(1)

    db = common.open_db()

    test_run = common.find_test_run( test_run )

    if verbose :
        print "TYPE ",test_run_type
        print "test_run",test_run

    c = db.execute( "SELECT project, host, test_name, context FROM expected WHERE test_run_type = ?", ( test_run_type, ) )

    if verbose :
        print "query done"

    for ( project, host, test_name, context ) in c :
        if verbose :
            print "CHECK",project, host, test_name
        c1 = db.execute("SELECT status FROM result_scalar WHERE test_run = ? AND project = ? AND host = ? AND test_name = ? AND context = ?", ( test_run, project, host, test_name, context ) )
        if c1.fetchone() is None :
            if verbose :
                print "        MISSING:", project, host, test_name
            db.execute('INSERT INTO result_scalar ( test_run, project, host, context, test_name, status, attn ) '+ 
                'VALUES ( ?, ?, ?, ?, ?, ?, ? )', ( test_run, project, host, context, test_name, 'M', 'Y' ) )

    db.commit()
