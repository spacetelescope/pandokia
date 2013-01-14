import os
import re
import pandokia.helpers.test_in_db as test_in_db

test_in_db.query['test_name'] = 'pdkrun_test_data/regtest/*'

anything = re.compile('.*')

expected_results = [
    #  test_name,
    #       dict of values for equivalence
    #
    # remember the db access library automatically converts things that look like numbers to float

    ( 'pdkrun_test_data/regtest/3',
        { 'status' : 'P', 'tda_title' : 'testfiles 3', 'tda__okfile' : anything },
            [ 'testfiles 3 ok',
               '[.] Test title: testfiles 3',
               ' ascii comparison passed for test_3.ref and test_3.out' 
            ]
    ),


    ( 'pdkrun_test_data/regtest/4',
        { 'status' : 'F', 'tda_title' : 'testfiles 4', 'tda__okfile' : anything },
            [ 'testfiles 4 ok',
               '[.] Test title: testfiles 4',
                'ascii comparison FAILED',
            ]
    ),

]

test_in_db.perform_db_tests( test_in_db.query , expected_results )

