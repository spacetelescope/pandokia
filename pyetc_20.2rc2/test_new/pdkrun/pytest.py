import os
import pandokia.helpers.test_in_db as test_in_db

test_in_db.query['test_name'] = 'pdkrun_test_data/pytest/*'

expected_results = [
    #  test_name,
    #       dict of values for equivalence
    #
    # remember the db access library automatically converts things that look like numbers to float

    ( 'pdkrun_test_data/pytest/param/test_eval[3+5-8]',
                { 'status' : 'P' } ),

    ( 'pdkrun_test_data/pytest/param/test_eval[2+4-6]',
                { 'status' : 'P' } ),

    ( 'pdkrun_test_data/pytest/param/test_eval[6*9-42]',
                { 'status' : 'F' } ),

    ( 'pdkrun_test_data/pytest/test_classes/FromUnit.testfail',
                { 'status' : 'F', 'tda_a' : 1, 'tra_c' : 3 } ),

    ( 'pdkrun_test_data/pytest/test_classes/FromUnit.testpass',
                { 'status' : 'P', 'tda_a' : 1, 'tra_b' : 2 } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestFromClass.testpass',
                { 'status' : 'P', 'tda_a' : 1, 'tra_b' : 2 } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestFromClass.testfail',
                { 'status' : 'F', 'tda_a' : 1, 'tra_c' : 3 } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestClassSetup.testpass',
                { 'status' : 'P', 'tda_a' : 1, 'tda_b' : 2, 'tra_c' : 3, 'tra_d' : None } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestClassSetup.testfail',
                { 'status' : 'F', 'tda_a' : 1, 'tda_b' : 2, 'tra_c' : None, 'tra_d' : 4 } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestSetupErrors.testpass',
                { 'status' : 'E', 'tra_exception' : 'Exception: Exception from setup' } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestSetupFirstTestErrors.test1',
                { 'status' : 'E', 'tra_exception' : 'Exception: Exception from test1' } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestSetupFirstTestErrors.test2',
                { 'status' : 'P', 'tra_exception' : None } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestSetupSecondTestErrors.test1',
                { 'status' : 'P', 'tra_exception' : None } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestSetupSecondTestErrors.test2',
                { 'status' : 'E', 'tra_exception' : 'Exception: Exception from test2' } ),

    ( 'pdkrun_test_data/pytest/test_classes/TestTeardownErrors.testpass',
                { 'status' : 'E', 'tra_exception' : 'Exception: Exception from teardown' } ),

    ( 'pdkrun_test_data/pytest/test_funcs/testfail',
                { 'status' : 'F', 'tda_a' : 1, 'tra_b' : 2 } ),

    ( 'pdkrun_test_data/pytest/test_funcs/testpass',
                { 'status' : 'P', 'tda_a' : 11, 'tra_b' : 12 } ),

    ( 'pdkrun_test_data/pytest/test_funcs/testerror',
                { 'status' : 'E', 'tda_a' : 99, 'tra_b' : 99,
                  'tra_exception' : 'ValueError: this test has an error' } ),

    ( 'pdkrun_test_data/pytest/testgen/testgen[0]',
                { 'status' : 'P', 'tda_a' : 0, 'tda_b' : 1, 'tra_c' : 2 } ),

    ( 'pdkrun_test_data/pytest/testgen/testgen[1]',
                { 'status' : 'P', 'tda_a' : 1, 'tda_b' : 2, 'tra_c' : 3 } ),

    ( 'pdkrun_test_data/pytest/testgen/testgen[2]',
                { 'status' : 'P', 'tda_a' : 2, 'tda_b' : 3, 'tra_c' : 4 } ),

    ( 'pdkrun_test_data/pytest/testmod/testpass',
                { 'status' : 'P', 'tda_a' : 1, 'tra_b' : 2, 'tda_c' : 3, 'tda_d' : None } ),

    ( 'pdkrun_test_data/pytest/testmod/testfail',
                { 'status' : 'F', 'tda_a' : 1, 'tra_b' : 2, 'tda_c' : 3, 'tra_d' : 4 } ),

    ( 'pdkrun_test_data/pytest/tf1/test1',
                { 'status' : 'P' } ),

    ( 'pdkrun_test_data/pytest/tf2/test1',
                { 'status' : 'P', 'tda_answer' : 42 } ),

    ( 'pdkrun_test_data/pytest/tf3/test1',
                { 'status' : 'P', 'tra_xxx' : 1 } ),

    ( 'pdkrun_test_data/pytest/tf4/test_very_slow1',
                { 'status' : 'E' } ),

    ( 'pdkrun_test_data/pytest/tf4/test_not_slow1',
                { 'status' : 'P' } ),

    ( 'pdkrun_test_data/pytest/tf4/test_fast',
                { 'status' : 'P' } ),

    ( 'pdkrun_test_data/pytest/tf5/test_foo',
                { 'status' : 'F' } ),

    ( 'pdkrun_test_data/pytest/tf5/test_bar',
                { 'status' : 'P' } ),

    ( 'pdkrun_test_data/pytest/tf6/test_foo',
                { 'status' : 'F' } ),

    ( 'pdkrun_test_data/pytest/tf6/test_bar',
                { 'status' : 'F' } ),

]

test_in_db.perform_db_tests( test_in_db.query , expected_results )

