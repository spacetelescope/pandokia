#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
# gen_expected - populate the 'expected' table
#
#   gen_expected test_run_type test_run
#       finds all the tests in test_run, makes sure similar values
#       are in the expected table for test_run_type.
#
# Later, you can use:
#    check_expected test_run_type test_run_to_check
#       fills in missing tests in test_run_to_check
#
#

debug = 0

import sys
import pandokia.common as common
import pandokia
import pandokia.helpers.easyargs as easyargs

pdk_db = pandokia.cfg.pdk_db

def run(args) :
    opts, args = easyargs.get( {
        '-c'    : 'list',
        '-p'    : 'list',
        '-h'    : 'list',
	'-cm'    : 'list',
        '--context' : '-c',
        '--project' : '-p',
        '--host'    : '-h',
	'--custom' : '-cm',
         }, args )

    try :
        test_run_type = args[0]
        test_run_pattern = args[1]
    except :
        print "can't get args"
        print "   pdk gen_expected test_run_type test_run_pattern"
        sys.exit(1)

    test_run_pattern = common.find_test_run( test_run_pattern )

    print "test_run_pattern = ",test_run_pattern

    l = [ ('test_run', test_run_pattern ) ]

    if '-c' in opts :
        l = l + [ ('context', x) for x in opts['-c'] ]
    if '-p' in opts :
        l = l + [ ('project', x) for x in opts['-p'] ]
    if '-h' in opts :
        l = l + [ ('host', x) for x in opts['-h'] ]
    if '-cm' in opts :
        l = l + [ ('custom', x) for x in opts['-cm'] ]


    if debug :
        for x in l :
            print "	",x
        print "?"
        sys.stdin.readline()

    where_str, where_dict = pdk_db.where_dict( l )

    sql = "select distinct project, host, context, custom, test_name from result_scalar %s " % where_str
    c = pdk_db.execute( sql, where_dict )

    for ( project, host, context, test_name, custom ) in c :
        if test_name.endswith("nose.failure.Failure.runTest") :
            # Sometimes nose generates this test name.  I don't want it in the database at all, because 
            # the name is not unique, and the record does not contain any useful information about the problem.
            # In any case, we never want to list this test as "expected", even if it leaks into the database.
            continue

        if debug :
            print "expect ",test_run_type, project, host, context, test_name, custom
	a = pdk_db.execute('select * from expected where test_run_type = :1 and project = :2 and host = :3 and context = :4 and custom = :5 and test_name = :6', (test_run_type, project, host, context, custom, test_name))
        y = a.fetchone()
        if y is None:
            try : 
                pdk_db.execute('insert into expected ( test_run_type, project, host, context, custom, test_name ) values ( :1, :2, :3, :4, :5, :6 )', ( test_run_type, project, host, context, custom, test_name ))
            except Exception, e:
                if debug :
                    print "exception", e
                pass
    pdk_db.commit()
