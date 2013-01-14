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
pdk_db = pandokia.cfg.pdk_db

def run(args) :
    try :
        test_run_type = args[0]
        test_run_pattern = args[1]
    except :
        print "can't get args"
        print "   pdk gen_expected test_run_type test_run_pattern"
        sys.exit(1)

    test_run_pattern = common.find_test_run( test_run_pattern )

    print "test_run_pattern = ",test_run_pattern

    c = pdk_db.execute("select distinct project, host, context, test_name from result_scalar where test_run = :1 ", ( test_run_pattern, ) )

    for ( project, host, context, test_name ) in c :
        if test_name.endswith("nose.failure.Failure.runTest") :
            # Sometimes nose generates this test name.  I don't want it in the database at all, because 
            # the name is not unique, and the record does not contain any useful information about the problem.
            # In any case, we never want to list this test as "expected", even if it leaks into the database.
            continue

        if debug :
            print "expect ",test_run_type, project, host, context, test_name
        # insert to the expected table; if the record is already there, it's ok.
        try : 
            pdk_db.execute('insert into expected ( test_run_type, project, host, context, test_name ) values ( :1, :2, :3, :4, :5 )', ( test_run_type, project, host, context, test_name ))
        except pdk_db.db_module.IntegrityError, e:
            if debug :
                print "exception", e
            pass
    pdk_db.commit()
