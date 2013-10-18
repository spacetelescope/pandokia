.. index:: single: patterns; .test() function

===============================================================================
Python: Implementing foo.test() for your package
===============================================================================

:abstract:

    This is an example of how to make a test() function in your
    package.  This test function can be called directly by a user,
    or it can be used as part of a pandokia test run.


This section describes various patterns for tests that are installed with your package
and called with a function named test().  For example: ::

    % python
    Python 2.7.1 (r271:86832, Jan  7 2011, 09:41:02) 
    [GCC 4.2.1 (Apple Inc. build 5664)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import xxx
    >>> xxx.test()
    >>> xxx.test(verbose=True)

To run it from the shell, you can use the command: ::

    python -c 'import sys, xxx; sys.exit(xxx.test())'

All of the patterns described here provide the same interface, but not all of them
do anything different for verbose=True.

The test() function can be used in a pandokia test run by executing the test()
function from some file that pandokia runs.

Using the "run" runner:

    In pdk_runners, add the line: ::

        mytest.py   run

    In mytest.py, use: ::

        #!/usr/bin/env python
        import xxx
        xxx.test()


    pdkrun will see mytest.py, recognize it as a "run"-type file,
    and execute the python in that file.  It just runs the file,
    not using py.test/nose/whatever, but your test() function will
    use one of these test frameworks, and therefore will be able
    to report results into the pandokia system.

using py.test
-------------------------------------------------------------------------------

In your package, create a subsidiary package named "tests" (note
the 's' in the name).  The tests package should contain python files
that will be recognized by py.test.

In your __init__.py:  ::

    def test( verbose=False ) :
        #
        import os, pytest

        # find the directory where the test package lives
        from . import tests
        dir = os.path.dirname( tests.__file__ )

        # assemble the py.test args
        args = [ dir ]

        # run py.test
        try :
            return pytest.main( args )
        except SystemExit as e :
            return e.code


Install your tests in xxx.tests with file names that py.test will recognize.

using nose
-------------------------------------------------------------------------------

In your package, create a subsidiary package named "tests" (note
the 's' in the name).  The tests package should contain python files
that will be recognized by nose.

In your __init__.py:  ::

    def test( verbose=False ) :
        import os, nose

        # find the directory where the test package lives
        from . import tests
        dir = os.path.dirname( tests.__file__ )

        # get the name of the test package
        argv = [ 'nosetests', '--exe', dir ]

        # run nose
        try :
            return nose.main( argv = argv )
        except SystemExit as e :
            return e.code


Install your tests in xxx.tests with file names that nose will recognize.


using pycode
-------------------------------------------------------------------------------

In your package, create a subsidiary package named "tests" (note
the 's' in the name).  The tests package should contain modules that
implement your tests.

Here is a sample package has tests in packagename.tests.test_a and packagename.tests.test_b .

Place this in __init__.py:  ::

    def test( verbose=False ) :
        import pandokia.helpers.pycode as pycode

        return pycode.package_test( 
            parent = __name__, 
            test_package = 'tests', 
            test_modules = [ 'test_a', 'test_b' ],
            verbose = verbose,
        )


Write your tests in packagename/tests/test_a.py as: ::

    import pandokia.helpers.pycode as pycode

    with pycode.test('some_thing') as t :
        assert some_thing

    with pycode.test('it_works') as t :
        assert it_works

When writing pycode tests using the with-statement, you can nest tests: ::

    with pycode.test('top') as tt :
        setup()

        with pycode.test('mid') as tm :
            more_setup()

            assert something
            # this assert reports a test named "top.mid"

            with pycode.test('bottom') as tb :
                assert something_else
                # this test is named "top.mid.bottom"

See ... for details.


using multiple runners
-------------------------------------------------------------------------------

If you have tests written for multiple test frameworks, you can have your
test function invoke each of the frameworks separately.  For example: ::

    def test_pytest( verbose=False ) :
        # ... as in examples above, 
        # ... but using tests.pytest for the test package

    def test_nose( verbose=False ) :
        # ... as above
        # ... but using tests.nose for the test package

    def test_pycode( verbose=False ) :
        # ... as above
        # ... but using tests.pycode for the test package

    def test( verbose=False ) :
        pt = test_pytest(verbose) 
        no = test_nose(verbose) 
        pc = test_pycode(verbose)
        return pt | no | pc

Of course, this means that you need more than one test framework
installed to run all the tests.  This is an incovenience to the
user, who may have to install all three of pandokia, py.test and
nose to run all the tests.

It could be useful during a transition period, especially if you structure
the various test functions to be aware of whether they can run or not: ::

    def test_pytest( verbose=False ) :
        try :
            import pytest
        except ImportError :
            print "Cannot import pytest - pytest tests are skipped"
            return
        ...

There is an example of this usage in test_new/pdkrun_test_data/test_fn in the
pandokia source code (
https://svn.stsci.edu/svn/ssb/etal/pandokia/trunk/test_new/pdkrun_test_data/test_fn ).

