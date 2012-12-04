import sys
import time
import traceback
import imp
import os.path

no_unittest2 = False

try :
    import unittest2
    from unittest2.main import TestProgram
except ImportError, e :
    no_unittest2 = e


# These are the versions of unittest2 that I expect this code to work
# with.  It might work in other versions, but who knows?
unittest2_versions = ( '0.3.0', '0.4.0', '0.4.2', '0.5.1' )


from pandokia.helpers import pycode

###
### This part of the file provides objects that are instantiated
### and used inside unittest2.
###

# pdk_runner is passed to unittest2.main.TestProgram as the class for
# the testRunner to use.  It must create a TestResult object for
# unittest2 to hand results to.  It turns out that TestResult (here
# provided by pdk_test_result) does all the real work of gathering
# the logs.

# It looks weird that the TEST RUNNER is somehow related to the FORMAT
# that we use to display the results, but that seems to be how
# unittest (and therefore unittest2) do it.

class pdk_runner(object):
    """A test runner class that writes pandokia log files
    """

    # After you tear away all the generalization and format-specific
    # stuff, this is all that is in a test runner.
    def run(self, test):
        "Run the given test case or test suite."
        result = pdk_test_result( fixed_filename = self.fixed_filename )
        try:
            test(result)
        finally:
            result.stopTestRun()
        
        return result


class pdk_test_result(object):
    """A unittest2 test result class that writes PDK log files

    You never use this directly -- use the pdk_runner class for
    your test runner.
    """

    # shouldStop is part of the unittest2 signal handling, which
    # we pretty much ignore.  It still has to be there, so the
    # main body of unittest2 can poll it.
    shouldStop = False

    def __init__(self, fixed_filename):
        # open the pandokia log file. The same open file is used
        # for all tests being run.
        self.pdklog = pycode.reporter( fixed_filename )

    def wasSuccessful(self) :
        # unittest2 main wants this function to return an exit code.
        # By Pandokia standards, success of a test runner means that
        # we could run the tests and create reports.  If we get here
        # at all, we are successful.
        return 0

    # startTestRun() and stopTestRun() bracket running of all the
    # tests that will be reported into this instance of pdk_test_result
    def startTestRun(self):
        pass

    def stopTestRun(self):
        self.pdklog.close()

    # startTest() and stopTest() bracket running of a single test
    def startTest(self, test):
        # initialize all the reportable values about the test.  We can then
        # assume everywhere that they exist.
        self.pdk_test_name = test.__class__.__name__ + '.' + test._testMethodName
        self.pdk_status = 'E'
        self.pdk_start_time = time.time()
        self.pdk_end_time = None

        # tda and tra dictionaries must be initialized to empty arrays,
        # but preserve any values that may have been stashed there by
        # the test object initialization.  Note that in unittest2, every
        # test gets a fresh object, so we do not need to worry about
        # old values hanging around.
        test.tra = getattr( test, 'tra', { } )
        test.tda = getattr( test, 'tda', { } )

        # gather stdout for the whole test run.  This includes
        # setUp() and tearDown().
        pycode.snarf_stdout()

    def stopTest(self, test) :
        #
        # this writes the entire report record for this test, based on:
        # - information that we saved in startTest()
        # - information in the test object
        # - information we have now
        log = pycode.end_snarf_stdout()
        self.pdklog.report( self.pdk_test_name, self.pdk_status, self.pdk_start_time, time.time(),
            test.tra, test.tda, log )

    # Instead of just "reporting a status" for the test, unittest2
    # has a separate function to report each different status that
    # it knows about.

    def addSuccess(self, test):
        # pass
        self.pdk_status = 'P'   
        self.print_status( None )

    def addFailure(self, test, err):
        # fail
        self.pdk_status = 'F'   
        self.print_status( err )

    def addError(self, test, err):
        # error
        self.pdk_status = 'E'   
        self.print_status( err )

    def addSkip(self, test, reason):
        # skip - i.e. we told this test not to run.
        # in pandokia, we call these "disabled".
        self.pdk_status = 'D'
        self.print_status( err )

    def addExpectedFailure(self, test, err):
        # "expected failure" ?  If it did what we expected, it
        # passed, right???
        self.pdk_status = 'P'   
        sys.stdout.write('Expected Failure')
        self.print_status( err )

    def addUnexpectedSuccess(self, test):
        # "unexpected success" ?  It didn't do what we expected, 
        # so it failed, right???
        self.pdk_status = 'F'   
        sys.stdout.write('Unexpected Success')
        self.print_status( None )

    # We print exceptions and stack traces so that they show up in
    # the captured stdout.  In principle, you could print more information
    # here, so we call it from every addXXX method, even when we do not
    # expect to have an exception.
    def print_status( self, e ) :
        if e is not None :
            traceback.print_exception(e[0],e[1],e[2],None,sys.stdout)

###
### This portion of the file provides the entry point required by pdk_python_runner
###

# main() calls into unittest2, which calls into the pdk_runner and
# pdk_test_result objects above

def main(args) :

    # We want to gather everything that happens into the test report.
    # Individual tests will suck up their own stdout, so it will
    # not end up in the output that belongs to the file.
    pycode.snarf_stdout()

    # status is pass unless something else happens
    file_status = 'P'

    # No arg processing because pandokia left everything we need
    # in the environment.
    filename = os.environ['PDK_FILE'] 

    # The module name is the basename of the file, without the extension.
    module_name = os.path.basename(filename)
    module_name = os.path.splitext(module_name)[0]


    file_start_time = time.time()


    if no_unittest2 :
        print "%s Cannot import unittest2"%__file__
        print e
        for x in sys.path :
            print "    %s",x
        file_status = 'E'

    else :
        # unittest2 is in very early stages of development.  Cry if we
        # don't see the version we expect, because there may be incompatible
        # changes in the future.
        if not unittest2.__version__ in unittest2_versions :
            print 'THIS IS NOT THE VERSION OF unittest2 THAT THE PANDOKIA RUNNER WAS WRITTEN FOR'
            print 'HAVE  ', unittest2.__version__ 
            print 'EXPECT ONE OF ', unittest2_versions
            file_status = 'E'   # to draw attention

        try :

            module = imp.load_source( module_name, filename )

            # This is a trick to pass a value to the initializer
            # pdk_test_result.  It would be hard to go through channels
            # because unittest2 does not have a concept for this particular
            # data.  I happen to know that it only makes a single TestRunner
            # object, so this is ok to do.
            pdk_runner.fixed_filename = module_name

            TestProgram( 
                # module must be a loaded module to run tests from
                module=module, 

                # argv must be a list with at least one element because
                # the TestProgram arg processing will try to read through
                # it whether we need it to or not.
                argv=[ 'nop' ],

                # provide it with our test runner, so it writes pandokia
                # logs instead of the default stuff to stdout
                testRunner = pdk_runner,

                # prevent it trying to exit when it is done
                exit=False,
                )

        # Yes, the whole file can fail or error.  This happens either
        # on import or when instantiating TestCase objects.
        except AssertionError :
            file_status = 'F'
            traceback.print_exc()

        except :
            file_status = 'E'
            traceback.print_exc()

    file_end_time = time.time()

    log = pycode.end_snarf_stdout()

    # We do not create the pandokia log entry object until after
    # everything is done.  Down inside unittest2, our code is going
    # to open the same log file.  It will close it before returning,
    # so we can open it here without conflicting.
    rpt = pycode.reporter( filename )

    # the name for the report on the file as a whole is derived from
    # the file name. the report object is already set up to do this,
    # so we do not need to provide any more parts of the test name.
    rpt.report( None, file_status, file_start_time, file_end_time, { }, { }, log )

    rpt.close()

