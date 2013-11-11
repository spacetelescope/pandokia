.. index:: single: runners; run

===============================================================================
any - run - run an external program, for testing compiled code
===============================================================================

:abstract:

    Test frameworks for compiled languages usually require you
    to compile a special test program.  To use one of these,
    you can have your build system (make, Ant, whatever) compile
    and install some number of test programs, then use this
    pandokia runner to execute them.

    Your test framework must write Pandokia-formatted results to
    the PDK_LOG file.  (If you have a program that returns an
    exit code for pass/fail, see the shell_runner runner.)

.. contents::


Running plain programs
-------------------------------------------------------------------------------

The "run" test runner just executes a program.  It assumes that the
program knows how to make a pandokia report.  You can use this for
special cases and for installed test programs that were compiled
as part of some external build process.

Compiled Separately
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The build process for your system under test can compile and install
test programs that are pandokia aware.  You can then use the "run"
runner to execute those external programs.

It may be helpful to place a shell script in your test directory: ::

    #!/bin/sh
    exec my_test_program

where my_test_program could be somewhere on PATH.


Special Shell Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to implement tests procedureally instead of through
a test framework (such as shell_runner or shunit2), you can write
a shell script that performs the test.

For shell scripts, there is a library named "pdk_run_helper.sh".  The basic
outline is: ::

    . pdk_run_helper.sh

    # begin a test named "P".
    test_start P
        # do some stuff here
        echo this is test P
        # report a test status - you can do this as many times as
        # you like; the resulting status will be the worst case that
        # was reported
        test_status P
    # end of test
    test_end

    test_start this_one_fails
        # how to set an attribute
        test_attr tda_this yes
        test_attr tra_that no
        # determine test status
        if false
        then
            test_status P
        else
            test_status F
        fi
    test_end

    # call this at the end to remove temp files
    cleanup


