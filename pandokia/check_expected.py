#
# pandokia - a test reporting and execution system
# Copyright 2009, 2011, Association of Universities for Research in Astronomy (AURA) 
#
#
# check_expected - check that expected tests exist in a test run
#

##80############################################################################
'''
pdk check_expected [ -p project ] [ -h host ] 
    [ -c context ] test_run_type test_run_to_check

    check that all expected tests from test_run_type are present 
    in test_run_to_check

    -p pname
    --project pname
        check only expectations for project pname
        
    -h hname
    --host hname
        check only expectations for host hname

    -c cname
    --context cname
        check only expectations for context cname

    -v
    --verbose
        verbose, use 2 or 3 for more

    --help
        this message

    you may list multiple instances of -p, -h, and -c to get the OR of
    all of the listed values.

    see also 'pdk gen_expected'

'''
################################################################################

import sys
import os
import string
import urllib
import datetime
import pandokia.common as common

import pandokia
pdk_db = pandokia.cfg.pdk_db

import pandokia.helpers.easyargs as easyargs

##80############################################################################
def run(args) :

    spec = {
        '-v' : '', 
        '-h' : '=+',
        '-p' : '=+',
        '-c' : '=+',

        '--help' : '',

        '--host'    : '-h',
        '--project' : '-p',
        '--context' : '-c',
        '--verbose' : '-v',     # arg is an alias for some other arg
        '-help'     : '--help',
    }

    opt, args = easyargs.get( spec, args )

    if opt['--help'] :
        print __doc__
        return

    verbose = opt['-v']

    try :
        test_run_type = args[0]
        test_run = args[1]
    except :
        print "\ncan't get args, try:\n    pdk check_expected --help\n"
        return 1

    # normalize the test run, so they can say stuff like "daily_latest"
    test_run = common.find_test_run( test_run )

    print "TYPE ",test_run_type
    print "test_run",test_run

    if test_run.endswith('latest') :
        print "this test run name is probably a mistake"
        return 1

    # construct the query for the set of tests that we are expecting

    select_args = [ ( 'test_run_type', test_run_type ) ]

    if '-h' in opt :
        select_args.append( ('host',    opt['-h']) )
    if '-p' in opt :
        select_args.append( ('project', opt['-p']) )
    if '-c' in opt :
        select_args.append( ('context', opt['-c']) )

    where_text, where_dict = pdk_db.where_dict( select_args )

    s = "SELECT project, host, test_name, context FROM expected %s " % where_text

    if verbose > 1 :
        print s
        print where_dict

    # perform the query

    c = pdk_db.execute( s, where_dict )

    if verbose > 1 :
        print "query done"

    # check each test reported in the query result

    detected = 0

    for ( project, host, test_name, context ) in c :
        if verbose > 2 :
            print "CHECK",project, host, test_name

        c1 = pdk_db.execute("""SELECT status FROM result_scalar 
                WHERE test_run = :1 AND project = :2 AND host = :3 AND 
                test_name = :4 AND context = :5 """, 
                ( test_run, project, host, test_name, context ) 
            )

        if c1.fetchone() is None :
            # it wasn't there
            if verbose :
                print "        MISSING:", project, host, test_name
            pdk_db.execute("""INSERT INTO result_scalar 
                ( test_run, project, host, context, test_name, status, attn ) 
                VALUES ( :1, :2, :3, :4, :5, :6, :7 )""",
                 ( test_run, project, host, context, test_name, 'M', 'Y' ) 
                )
            detected = detected + 1

            # do some commits from time to time to avoid lock timeouts
            if detected % 10000 == 0 :
                pdk_db.commit()

    # must commit after db updates

    pdk_db.commit()


    print "detected ",detected
