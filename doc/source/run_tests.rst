.. index::
    single: running tests

================================================================================
Using Pandokia To Run Tests
================================================================================

:abstract:

        This describes how to use the Pandokia Meta-Runner to
        execute your tests.

        The Meta-Runner identifies tests, sets up an appropriate execution
        environment, and invokes a Test-Runner to actually performs
        the tests.  If parallelism is appropriate for your tests, you
        can direct it to run multiple tests concurrently.

        The Meta-Runner has provisions for enabling/disabling tests and
        for setting environment variables before the test is executed.

        A Test-Runner is a Pandokia component that implements a
        standard interface between the Meta-Runner and some specific
        test execution software.  There are several test runners
        available.  For example, the "pytest" Test-Runner uses
        py.test 2.2.1 (along with a plugin) to run tests.

        See adding_runners.rst for documentation on implementing your
        own Test-Runner for whatever testing systems you have.

.. contents::

.. index::
    single: running tests; overview

Simple Overview
--------------------------------------------------------------------------------

Typical usage is to create a directory tree that contains all the
tests.  Every test has a unique name, and the path from the top of
the directory tree to the file containing the test will be part of
the name.

There are three ways to run tests with the Pandokia Meta-Runner:

 - You can recursively run all the tests discovered in a directory tree ::

        pdk run -r directory

        pdk run --recursive directory

 - If you want to run all the tests in a specific directory, you can give a list of specific directory names ::

        pdk run /where/your/tests/are

 - You can give the name(s) of specific files that contain your tests ::

        pdk run xyz*.py

All of these cases create or append to a Pandokia log file, which contains the results from
all the tests.

There is also a command "pdkrun" that you can use in place of "pdk run".  It exists principally so that I can type::

        !pdkrun

to repeat the last pdkrun command.


pdk run --recursive *directory*
--------------------------------------------------------------------------------

When you give ``--recursive``, pandokia recursively descends into the
directory tree that you specify.  In each directory, pandokia finds
and runs tests by executing the command "pdk run *directory*".  If no
tests are found in a directory, zero test results are reported from
that directory.

The configuration variable ``exclude_dirs`` contains a list of directory
names to skip.  (see pandokia/default_config.py)

You can specifiy multiple processes with the option ``--parallel N``
or the environment variable ``PDK_PARALLEL``.  It will execute tests
in that many directories concurrently.  It will not execute multiple
concurrent processes in a single directory because we have found that
the tests often interfere with each other. (This may be a
characteristic of our test environment, which depends heavily on input
and output files.)


pdk run *directory*
--------------------------------------------------------------------------------

When you give the name of a directory, it compares the name of each
regular file (not directories or device files) in that directory with
a set of glob patterns that identify tests.

The file is disabled if the same base file name exists with the
extension ".disable" or ".$PDK_CONTEXT.disable".

For example, if your test is test_xyz.py, it will be disabled if

- there is a file test_xyz.disable

- there is a file test_xyz.foo.disable and the currently running context is "foo"

- there is a file test_xyz.default.disable and the currently running context is "default"

If the Test-Runner knows how to report disabled tests, report will
contains status=D (for disabled) for each test in that file.

Some Test-Runners do not know how to report the names of disabled
tests.  The *nose* and *py.test* Test-Runners included in the
Pandokia distribution do.

If the file name looks like a test and it is not disabled, the test is
executed by the same code that implements ``pdk run *filename*``.


pdk run *filename*
--------------------------------------------------------------------------------

When you explicitly give the name of a specific file, pdk run executes the
tests in that file.  It runs the tests even if the .disable file
exists.

.. index::
    single: running tests; environment variables

pdk run arguments and environment variables
--------------------------------------------------------------------------------

``pdk run`` can take parameters as environment variables and as command line
arguments.  Arguments always override the value in an environment variable.

Except as noted, all of the options can be used with any of the variations of
``pdk run``.

--log      or PDK_LOG

   The series of test results will be written into this file, for
   subsequent import into the database. 
   Default value is "PDK_DEFAULT.LOG."+test_run

.. index:: single: running tests; parallel

--parallel or PDK_PARALLEL 

   Run up to this number of tests concurrently (but it will run at
   most one test at a time in any given directory).
   Only used with the -r (recursive) flag.
   Default value is 1.

--project  or PDK_PROJECT

   Use this as the project name.
   Default value is "default".

--test_run or PDK_TEST_RUN

  Use this as the name of the test run.
  Default value is a generated string including the user name and the
  time to the nearest minute. 


.. index:: single: timeout

PDK_TIMEOUT

  This environment variable sets the max number of seconds that a
  test runner can run.  If set, individual test processes will be
  killed when they exceed this age.  

  This timeout applies to all the tests in a single file, not the
  individual tests.  If you need timeouts for specific tests, you
  must use a test runner that implements per-test timeouts (such
  as py.test with the Pandokia plugin) or implement a timeout feature
  in your test code (possibly using a library such as *fixtures*).

  Our normal use is to set PDK_TIMEOUT in a pdk_environment file.
  We have different timeouts in different directories.

All other environment variables with names beginning PDK\_ are reserved
for internal use by pandokia.

Monitoring the running tests
--------------------------------------------------------------------------------

pdkrun can run multiple processes concurrently.  To see a report
of what is currently running, you can enter this command in the
directory where you started the tests ::

    pdk runstatus

This clears the screen and shows three columns of information ::

  - the process "slot"
  - date/time of last update to that process slot
  - file name of tests executing in that process slot

The information is recorded in a file named `pdk_statusfile`.

If you set PDK_STATUSFILE to 'none', pdkrun will not record the
status and the runstatus command will not work.  (Later, this will
be a way to say the name of the file to use.)

**not implemented on Windows**

Creating a Test Tree
--------------------------------------------------------------------------------

Pandokia will preserve the hierarchy of your test tree as part of the
test name. You can populate the directory tree with files containing
tests in any organization that makes sense for your project. 

The test running concurrency operates at directory granularity; so do
the environment and contact files. You may wish to take this into
account when creating the tree.

Place an empty file named pandokia_top at the top of the directory
tree.

.. index:: single: files

Overhead files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pandokia_top
  This is an empty file marking the top of the directory tree.

.. index:: single: environment

pdk_environment
  This is an INI-style file that may be used to customize the environment
  for the tests in this directory. It should contain named
  sections. The [default] section will apply to all tests; additional
  sections based on operating system ([os=foo] or [osver=foo]),
  machine architecture ([cpu=foo]), or hostname ([hostname=foo]) may
  also be included, and are applied hierarchically in that order.

  Specifications of OS, version, or architecture are
  expected to be site-specific. We implemented a mapping that makes
  sense in our system; you may wish to examine and/or customize the
  env_platforms.py file.

  The resulting environment will be merged with os.environ prior to
  running tests; in particular, any PATH environment variable is handled
  specially, and appended to (rather than overriding) existing values at
  a higher level.

pdk_contacts
  This file may be used to specify the username or email address of
  individuals (one per line) who should be notified about anomalous
  results for tests contained in this directory. The run command does
  not read this file; see database.rst, "Importing Contacts" for more
  detail. 

Writing a nose test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: move this into the runners_nose section

TODO: refer to a directory of sample tests


Pandokia will support any type of test that nose supports: unittests,
doctests, and arbitrary test functions that raise assertion errors if
they fail.

unittest/testcase style
.......................

# This example shows how to add attributes to a unittest-style test.::

   class BasicTest(unittest.TestCase):
       def setUp(self):
           self.tda={}
           self.tra={}
           self.tda['foo']='bar'

       def test1(self):
           self.tda['func']='add'
           self.tra['sum']=4+2

           # If the assertion fails, the test fails.
           self.assert_(4+2==6)


Any old function
................

Test functions can be written as follows::

   #TDAs and TRAs are supported via global variables. The
   #plugin takes care of clearing them so there is no crosstalk
   #between tests.

   tda = dict()
   tra = dict()

   def testxyz() :
        tda['cat']='tortoiseshell'
        # If the assertion fails, the test fails
        assert True

   def testabc():
        tda['func']='add'
        sum=4+2
        tra['sum']=sum
        assert sum == 6

   def testglobal():
        global tda
        tda = {'cat':'lion'}
        #The global statement is necessary in order to avoid rebinding
        #rebinds the name to a local variable, which will not be seen
        #by Pandokia
        assert True


doctest
.......

#TDAs and TRAs are not supported in doctests. 
"""
>>> print 1+1
2

>>> print 7-3
4
"""



Using file comparators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBD, but see :download:`example_filetest.py <example_filetest.py>`.



