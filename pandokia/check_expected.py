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

import pandokia
pdk_db = pandokia.cfg.pdk_db

def run(args) :

    verbose = 0 # bug: I know there is no way to set it

    try :
        test_run_type = args[0]
        test_run = args[1]
    except :
        print "can't get args"
        print "gen_expected test_run_type test_run_to_check"
        print " test_run_to_check is the name of a test run to check"
        sys.exit(1)

    test_run = common.find_test_run( test_run )

    if verbose :
        print "TYPE ",test_run_type
        print "test_run",test_run

    c = pdk_db.execute( "SELECT project, host, test_name, context FROM expected WHERE test_run_type = :1 ", ( test_run_type, ) )

    if verbose :
        print "query done"

    for ( project, host, test_name, context ) in c :
        if verbose :
            print "CHECK",project, host, test_name
        c1 = pdk_db.execute("SELECT status FROM result_scalar WHERE test_run = :1 AND project = :2 AND host = :3 AND test_name = :4 AND context = :5 ", ( test_run, project, host, test_name, context ) )
        if c1.fetchone() is None :
            if verbose :
                print "        MISSING:", project, host, test_name
            pdk_db.execute('INSERT INTO result_scalar ( test_run, project, host, context, test_name, status, attn ) '+ 
                'VALUES ( :1, :2, :3, :4, :5, :6, :7 )', ( test_run, project, host, context, test_name, 'M', 'Y' ) )

    pdk_db.commit()
