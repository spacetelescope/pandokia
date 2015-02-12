#
# This is an example pandokia pycode test.

import datetime # needed for this example, but not necessarily always

import pandokia.helpers.pycode

# If you accidentally ask nose to run this file, this prevents it from doing anything.
def setup() :
    raise Exception("Yow! DO NOT RUN THESE TESTS IN NOSE - use the pandokia 'pycode' test runner")


# The pdkrun program will execute pycode tests by importing the file
# and then calling 
#   pycode(1)
#
# Use pandokia.helpers.pycode.report to report the result of each test.

def pycode(mode) :

    # mode=1 for running tests; may be another mode later to get a list
    # of test names without running them.  (I'm not sure if that is worth
    # the trouble of doing.)
    if mode != 1 :
        raise AssertionError("Do not know pycode mode %s"%str(mode))

    print "Beginning pycode tests"

    ####
    # initialize for reporting - if pandokia is running your tests
    # through the pycode test runner, you never need to pass any of the
    # other parameters to reporter()
    rpt = pandokia.helpers.pycode.reporter(__file__)

    ####
    # a minimal report
    rpt.report(test_name='arf',  status='P')

    ####
    # a full report, all at once
    rpt.report(
            test_name='narf', 
            status='P', 
            start_time=datetime.datetime.now(),
            end_time = datetime.datetime.now(),
            tda= { 'foo': 1, 'bar': 0 },
            tra= { 'baz': 'yes' },
            log='arf\narf\narf\n'
            )

    ####
    # start/finish reporting
    rpt.start( test_name='plugh',
            tda= { 'foo': 0, 'bar': 0 }
        )
        # start_time will be datetime.datetime.now()

    status='F'

    rpt.finish( status=status, tra= { 'baz': 'no' }, log='did something...\nelse\n' )
        # end_time will be datetime.datetime.now()

    ####
    #
    print "Finished pycode tests"

