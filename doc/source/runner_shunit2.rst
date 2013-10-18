.. index:: single: runners; shunit2

===============================================================================
sh - shunit2 - an xUnit test framework for bourne shell scripts
===============================================================================

Overview
----------------------------------------------------------------------

This runner uses a modified version of shunit2; the modifications implement
support for a plugin architecture.  

The plugin that reports to the Pandokia system is distributed with Pandokia.

(As of this writing, patches to implement this plugin architecture have been
submitted to the shunit2 maintainer, but have not been accepted into the
source code.)


Installing
----------------------------------------------------------------------

You can download the patched shunit2 from http://ssb.stsci.edu/testing/shunit2

Download the file "shunit2" and put it on your PATH somewhere.  No changes
to your installed Pandokia are required.

This copy of shunit2 is identified by SHUNIT_VERSION='2.1.6plugin'

The *unmodified* documentation for shunit2 is available at https://shunit2.googlecode.com/svn/trunk/source/2.1/doc/shunit2.html or http://ssb.stsci.edu/testing/shunit2/shunit2.html


Using shunit2 with Pandokia
----------------------------------------------------------------------

This version of shunit2 can use the command "shunit2 xyz.shunit2"
to run the tests in a file.  Pandokia uses this form exclusively.

The file of tests should NOT use shunit2 as a library.  This has
the odd implication that the tests distributed with shunit2 do
not run unmodified in pdkrun.

With earlier versions of shunit2, it was conventional to write tests
as a program that include shunit2 as a library.  This mode is not
tested with Pandokia.

Basic Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For use with Pandokia, write a shell script that has function
names starting with "test".  For example, ::

    test_one_equals_one()
    {
        echo 'this one passes'
        assertEquals 1 1
    }

    test_two_equals_one()
    {
        echo 'this one fails'
        assertEquals 2 1
    }

Save this test with a file name that ends xyz.shunit2 and run
pandokia on it: ::

    pdkrun xyz.shunit2

Assertions in shunit2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The shunit2 distribution contains documentation of various assertions
in doc/shunit2.rst ; you can read it online at 
http://shunit2.googlecode.com/svn/trunk/source/2.1/doc/shunit2.html
or http://ssb.stsci.edu/testing/shunit2/shunit2.html

There is significant difference of interest to python programmers:
When an assertion fails in shunit, it does NOT abort the rest of
the test function.  It sets a failure flag and continues execution.
This means that you can have arbitrarily many assertions in a single
test function.  The result of that test will be Fail if *any* of
the assertions fail. ::

    test_foo()
    {
        # this test fails because of the second assertion
        assertEqual 1 1
        assertEqual 2 1
        assertEqual 3 3
        echo 'test_foo finished'
    }

You can also explicitly declare a test to
fail with the "fail" function: ::

    test_bar()
    {
        fail "this test always fails"
    }


Erroring Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

shunit2 normally considers a test to have a status of Pass or Fail;
it does not natively have the concept of Error.

If you want to report a status of Error to the Pandokia system, you
can call the special function pdk_error: ::

    test_baz()
    {
        pdk_error "this test errors"
    }


Disabling individual tests 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    test_foo() {
        echo 'in shunit, you can produce output from a skipped test'
        _shunit_assertSkip
        return
        echo pass
    }


Pandokia Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can report tda/tra attributes with the pdk_tda or pdk_tra functions: ::

    test_with_attr()
    {
        pdk_tda one 1
        x=`ls | wc`
        pdk_tra filecount $x
        pdk_tra foo
    }


Using pdk_shell_runner_helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not have reference files: ::

    . pdk_shell_runner_helper

    test_name1() {
        # must init the helper at start of each test
        init

        # declare any tda attributes
        pdk_tda foo 1

        # do something
        thing=`echo X`

        # report a test result
        case "$thing"
        in
        pass)       
                :       # do nothing special to indicate pass
                ;;
        fail)
                fail    # regular shunit2 way of failing a test
                ;;
        *)
                pdk_error # how to declare error to shunit2
                ;;
        esac

        # declare any tra attributes
        pdk_tra bar 2
    }


If you have reference files to compare: ::

    . pdk_shell_runner_helper

    test_name2() {
        # You must init the helper at start of each test; this does all
        # the regular init AND declares the okfile for tracking
        # output/reference files.

        init_okfile ${_shunit_test_}

        # Make some output files.

        echo hello > out/${_shunit_test_}.f1
        echo world > out/${_shunit_test_}.f2

        # Use testfile to compare the output to the reference file.
        # testfile declares the pass/fail/error status to shunit2
        # and pandokia.

        testfile diff out/${_shunit_test_}.f1
        testfile cmp  out/${_shunit_test_}.f2

        # you can declare attributes
        pdk_tda foo 1
        pdk_tra bar 2
    }

shunit2 outside pandokia
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make your shunit2 tests work in or out of pandokia: ::

    . pdk_shell_runner_helper

    test_whatever() {
        ...
    }

    if [ "$SHUNIT_VERSION" = "" ]
    then
        . shunit2
    fi

If you write your tests in this form, you can run them with
any of these commands: ::

    pdkrun foo.shunit2

    shunit2 foo.shunit2

    ./foo.shunit2

installed shunit2 tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can write shunit2 tests that are installed on the users PATH.
The user can then run them by typing the name, but it requires
special handling to have pdkrun find and execute them.  

Use the "run" runner.  Create file.run containing: ::

    #!/bin/sh
    exec shunit2 --plugin pdk installed_name.shunit2

shunit2 extended capabilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This modified shunit2 contains some new features.

You can list all the test names that are defined in a shunit2 file: ::

    shunit2 file.shunit2 --list
    shunit2 file.shunit2 -l

You can specify a list of tests to run, in place of all the tests in the file: ::

    shunit2 file.shunit test_1 test_2

