.. index:: single: runners; fctx

===============================================================================
C - fctx - unit tests in C and languages callable from C
===============================================================================

Overview
-------------------------------------------------------------------------------

FCTX is a C unit test framework.  Everything you need to compile
and run tests is included with Pandokia.  It used to come from
http://fctx.wildbearsoftware.com/ , but that site has been down for
some time, so we have documentation at http://ssb.stsci.edu/testing/fctx .
The github repository is at https://github.com/imb/fctx .

In FCTX terms, the Pandokia interface is implemented as a "custom
logger".  To make your tests Pandokia-capable, you need to include
pandokia_fct.h instead of fct.h, which causes the custom logger
to be installed.

Here is a simple example: ::

    #include "pandokia_fct.h"

    FCT_BGN()
    {
        FCT_QTEST_BGN(test_name_1)
        {
            printf("This test will pass\n");
            fct_chk(1);    // pass
        }
        FCT_QTEST_END();

        FCT_QTEST_BGN(test_name_2)
        {
            printf("This test will fail\n");
            fct_chk(0);    // fail
        }
         FCT_QTEST_END();

    }
    FCT_END()

This example is minimal, though it is adequate for many purposes.
In principle, you can also use the more advanced features of FCTX
such as fixtures, suites, conditional tests, and advanced checks,
though those features are not heavily tested with Pandokia.  See
the FCTX documentation for details.

Compiling the test program
-----------------------------------------------------------------------------

The files fct.h (the fctx test framework) and pandokia_fct.h (the
pandokia logger) are included in the pandokia distribution.  The
command ::

    pdk maker

will say the name of the directory where you can find the files.
So, for example, if you paste the example code above into mytest.c,
you can compile it with: ::

    cc -o mytest -I`pdk maker` mytest.c 

Running the test program outside Pandokia
-----------------------------------------------------------------------------

A compiled test program is a normal FCTX test.  You can just run
it to see output in the FCTX format. ::

    ./mytest

If the test program sees the environment variable PDK_FILE, the
Pandokia logger will assume it is being run by pandokia and take
over the logging function.

You can explicitly ask it to make pandokia output by specifying
"--logger pdk". ::

    ./mytest --logger pdk

The pandokia plugin does not accept any command line parameters;
it takes values from the environment, or it uses defaults.  The
default pandokia log file is named "PDK_LOG".

Using with the "run" test runner, option A
-----------------------------------------------------------------------------

The "run" test runner just runs an external program that is pdk-aware.  You
would have your normal build system compile/install the test somewhere
and then define the test as a shell script something like this:

pdk_runners: ::

    *.fctx    run

xyzzy.fctx: ::

    #!/bin/sh
    # This file must be here and executable for pandokia to know about
    # the test, but it just runs the actual test program.
    /install/dir/mytest

The names of the tests will be prefixed with the base name of the
file that pandokia finds, not the name of the executable that
contains the tests.  In this example, there are two tests found:
xyzzy/test_name_1 and xyzzy/test_name_2.

Using with the "run" test runner, option B
-----------------------------------------------------------------------------

You could have your build system compile the tests directly in the
directory of tests, so that you might run the commands ::

    make all
    pdkrun .

To do this, list each file in pdk_runners: ::

    test_one    run
    test_two    run

and use a makefile like this: ::

    all: test_one test_two

    test_one: test_one.c
        cc -o test_one -I `pdk maker` test_one.c

    test_two: test_two.c
        cc -o test_two -I `pdk maker` test_two.c


Using with the "maker" test runner
-----------------------------------------------------------------------------

If you use the "maker" test runner, you may be able to include your C
source code directly in the test directory.  Pandokia can compile and run it
for you.

pdk_runners: ::

    *.c    maker

mytest.c: ::

    /*
    * $ cc -o mytest -I`pdk maker` mytest.c
    * $ ./mytest
    */
    ... rest of the C code for your test ...


Capture of stdout/stderr
-----------------------------------------------------------------------------

This test runner will capture stdout/stderr of your tests, but the 
underlying fctx implementation has a bug.  It directs stdout/stderr
into a pipe, then reads the pipe back *in the same process* to 
collect the output for logging.  If your test prints more output
that fits in a pipe, the test will deadlock writing to the pipe.

