.. index:: single: runners; custom

================================================================================
Adding Test Runners to Pandokia
================================================================================

:abstract:

    When Pandokia executes tests, it uses a test runner to execute
    the set of tests in a specific file.  You can add interfaces
    to your own test runners, as long as they can report their results
    in pandokia format.

    This document describes how to support a new test runner.

.. contents::


Pick a name
--------------------------------------------------------------------------------

Your test runner needs a name that pandokia can use internally.  In the examples,
I will add a test runner named *shell_runner*.


Describe file names for that kind of test
--------------------------------------------------------------------------------

Pandokia uses a wild card pattern to recognize all the files that belong to a
particular test_runner.  

If you are adding a new runner to the pandokia source tree, change the value of runner_glob
in pandokia/runners/__init__.py

If you are adding your own runner, change the value of runner_glob in the installed module
pandokia.config

Choose your wildcard and add it to the list of patterns: ::

    runner_glob = [
    #   ( 'not_a_test*.py',     None        ),
        ( '*.py',               'nose'      ),
        ( '*.xml',              'regtest'   ),
        ( 'test*.sh',           'shell_runner' ),
    ]


Define the python code to interface with your runner
--------------------------------------------------------------------------------

For a runner named XYZ, you must create either the module *pandokia.runners.XYZ*
(to build your runner into pandokia) or *pandokia_runner_XYZ* (to create your
runner as a separately installable python module).

For example, for *shell_runner*, you would create the file
*pandokia/runners/shell_runner.py*.

In this file, you define the functions that Pandokia will call to locate your runner.

The functions are:

 - def command( env )

    The function *command* returns a command that pandokia should use to execute a test.  The parameters are all in
    the dictionary *env*, along with other environment variables.  The returned command is used roughly like this::

        p = subprocess.Popen(cmd, shell=True, env = env )

    (for exact details, see the function run() in pandokia/run_file.py)

    Normally, we expect that you will want to run your testing system in a separate process.  This allows
    the test system to keep operating, even if something about a particular test or test_runner causes a crash.

    Instead of a single command, this function can return a list of commands to be executed in order.

 - def list( env )

    The function *list* returns a list of the test names that
    are in the file, but does not execute any of the tests.
    When a test file is disabled, this feature is used to find
    a list of disabled tests to include in the pandokia log
    file.

    It is not always convenient to implement this feature.  If
    it is not, return None.

The parameter *env* is a dictionary of environment variables that
would be used to execute the test.  Everything you need to know is
stored in this environment.

The specific variables of interest are:

 - PDK_DIRECTORY

    The name of the directory that the test is in.  Pandokia
    always runs the test from the directory where the test is
    found, so this value is the same as os.getcwd()

 - PDK_FILE

    The name of the file that contains the tests.  The file is in the
    current working directory.

 - PDK_LOG

    Your test runner should append test results to this file.

 - PDK_TESTRUN

    The name of the test run that this test execution is part of.

 - PDK_PROJECT

    The name of the project that this test execution is part of.

 - PDK_CONTEXT

    The name of the context that this test is running in.  

 - PDK_TESTPREFIX

    This prefix represents the directories at higher levels in the directory
    tree.  If the prefix is not '', you should insert the prefix and a '/'
    in front of the test name.

 - PDK_PARALLEL
 - PDK_PROCESS_SLOT

    Internal tracking values used when executing tests in parallel.  These values
    are not directly useful to a test_runner, but the system does not remove
    them from the environment.

Other environment variables are also present, either from the
environment inherited from your shell or from the pdk_environment
files.


Implement the command that runs your tests
--------------------------------------------------------------------------------
You must provide a program that actually runs the tests.  It should
use arguments and/or environment variables to know what to do.

You should APPEND data in pandokia log format to the file named in $PDK_LOG.

See doc/file_format.txt and doc/report_fields.txt for details of the report format.

Before starting your program, pdkrun wrote some default values to
the log file.  These are::

    test_run
    project
    host
    location
    test_runner
    context

At a minimum, you must add::

    test_name
    status
    END

You may report values that override the defaults, and you may add
other fields as described in doc/report_fields.txt.

Using pycode.report in your python-base test runner
----------------------------------------------------------------------

If you are writing in python, you can use the "reporter" object in
pandokia.helpers.pycode to write properly formatted records to
$PDK_LOG : ::

    import pandokia.helpers.pycode as pycode

    # initialize one instance of the pycode reporter; if you are
    # running in pandokia, you don't need any parameters except
    # the None.
    rpt = pycode.reporter( None )

    # declare your test name and a dict for the attributes.
    test_name = 'some_test'
    tda = { }
    tra = { }

    # start the test.  tda will not be used until the call to finish()
    # so more tdas can still be added by the test code.
    # this call remembers what time the test started.
    rpt.start( test_name, tda )

    # cause python to redirect sys.stdout and sys.stderr into a StringIO
    pycode.snarf_stdout()

    # perform the test.  It should fill in attributes in tda[]
    # and tra[] and set the value of status.
    foo()

    # capture the redirected stdout
    log = pycode.end_snarf_stdout()

    # report the result of the currently running test.  This call
    # knows what time the test finished.
    rpt.finish( status, tra, log )

    rpt.close()


You can also report the test all at once instead of splitting into
start()/finish() : ::


    import pandokia.helpers.pycode as pycode

    # initialize one instance of the pycode reporter; if you are
    # running in pandokia, you don't need any parameters except
    # the None.
    rpt = pycode.reporter( None )

    # declare your test name and a dict for the attributes.
    test_name = 'some_test'
    tda = { }
    tra = { }

    start_time = time.time(0)

    # cause python to redirect sys.stdout and sys.stderr into a StringIO
    pycode.snarf_stdout()

    # perform the test.  It should fill in attributes in tda[]
    # and tra[] and set the value of status.
    foo()

    # capture the redirected stdout
    log = pycode.end_snarf_stdout()

    # report the result of the test.  Leave out optional args
    # if you don't want to report them.
    rpt.report( test_name, status, start_time = start_time,
        end_time = time.time(0), tra = tra, tda = tda, log = log )

    rpt.close()

This is a primitive tool for writing log files.  Calls to rpt.start()
and rpt.finish() do not nest, and attempts to write to the same file
with more than one rpt object are likely to end badly.

