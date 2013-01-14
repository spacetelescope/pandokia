#
# This is an example python thing that creates a pandokia log file without running in the context of pdkrun
#
# run it with "python non_pdk.py" to create the file 'z.pdklog' in pandokia format

import datetime # needed for this example, but not necessarily always

import pandokia.helpers.pycode

if __name__ == '__main__' :
    #
    # The reporting is very similar to what you would do in a pycode test runner.
    # The main difference is:
    #
    # There are some fields in the pdk report file that are required for each
    # record, but that are usually the same for every record that you
    # create from a single execution of the test code.  They are:
    #   test_run    name of this test run
    #   project     name of the project that we are testing
    #   context     (not actually used yet)
    #   host        name of the computer we are running this on
    #
    # You can also specify a few other optional fields.  see pycode.py for details.
    #   
    rpt = pandokia.helpers.pycode.reporter(__file__,
        filename='z.pdklog',
                            # output file name
        setdefault=True,    
                            # needed to write our explicit settings to the file
        test_run='my_test_run',
                            # default from PDK_TESTRUN or "default" 
        project='cool_project',
                            # default from PDK_PROJECT or "default" 
        host='myhost.example.com',
                            # default is the hostname, without the domain
        location='/data1/demos/pandokia/tests/pycode/non_pdk.py',
                            # where did the tests come from; default is to not report it
        test_runner='non_pdk',
                            # name of the test runner - not particularly important
                            # default is to not report it
        test_prefix='demos/pycode/',
                            # stuck on the front of every test name, along with the base
                            # name of this file
        )

    ####
    # minimal report
    rpt.report(test_name='arf',  status='P')

    ####
    # full report all at once
    rpt.report(
            test_name='narf', 
            status='N', 
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

    # do test here.
    status='F'

    rpt.finish( status=status, tra= { 'baz': 'no' }, log='did something...\nelse\n' )
        # end_time will be datetime.datetime.now()
