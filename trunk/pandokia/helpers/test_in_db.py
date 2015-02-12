import os
import re
import pandokia.helpers.dbaccess as dbaccess
import pandokia.helpers.pycode as pycode

query = {
    'test_run' : 'pdkrun_test',
    'project'  : 'default',
    'context'  : 'default',
    'host'     : '*',
    }

if 'RUNHOST' in os.environ:
    query['host'] = os.environ['RUNHOST']

def load_tests( query ) :
    # list of all tests
    l = dbaccess.load_identity( **query )

    # indexed by test name
    all_tests = { }
    for x in l :
        all_tests[ x['test_name'] ] = x

    return all_tests

def perform_db_tests( query, expected_results ) :

    all_tests = load_tests( query )

    # check that the database record for each one has the values we expect
    with pycode.test( 'values' ) :
        for ttt in expected_results :
            if len(ttt) == 2 :
                name, expect = ttt
                log_expect = [ ]
            elif len(ttt) == 3 :
                name, expect, log_expect = ttt
            else :
                raise ValueError('test condition invalid: %s'%str(ttt))

            with pycode.test( name ) as t :
                if not name in all_tests :
                    raise Exception('expected test %s not present'%name)
                data = all_tests[ name ]
                status='P'
                for f in sorted ( [ x for x in expect ] ):
                    if expect[f] is None :
                        if f in data :
                            print "extra field",f
                            status='F'
                            del data[f]
                        continue

                    if not f in data :
                        print "missing field",f
                        status='F'
                        continue

                    c = expect[f]
    
                    if isinstance(c, basestring) :
                        if expect[f] != data[f] :
                            print "expect ",expect[f]
                            print "found  ",data[f]
                            status='F'
                    else :
                        if not expect[f].search(data[f]) :
                            print "expect ",expect[f]
                            print "found  ",data[f]
                            status='F'
                    del data[f]

                for f in data :
                    if f.startswith('tda_') or f.startswith('tra_') :
                        print "Unexpected attribute", f
                        status='F'

                log = data['log']

                for f in log_expect :
                    if re.search( f, log ) :
                        pass
                    else :
                        print "Expect log to have: %s"%f
                        status='F'
                
                del all_tests[name]

                if status == 'F' :
                    assert 0
                
    with pycode.test( 'all' ) :
        if len(all_tests) != 0 :
            print "Not all tests examined:"
            for x in sorted( [ x for x in all_test ] ) :
                print "   ",x
            assert 0

