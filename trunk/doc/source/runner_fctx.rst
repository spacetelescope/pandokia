.. index:: single: runners; fctx

===============================================================================
C - fctx - unit tests in C and languages callable from C
===============================================================================

Overview
-------------------------------------------------------------------------------

FCTX is a C unit test framework.  Everything you need to compile and run tests is included with Pandokia.
See http://fctx.wildbearsoftware.com/ or http://ssb.stsci.edu/testing/fctx for FCTX documentation.

In FCTX terms, the Pandokia interface is implemented as a "custom
logger".  To make your tests Pandokia-capable, you need to include
pandokia_fct.h and use CL_FCT_BGN and CL_FCT_END to bracket your
program instead of FCT_BGN and FCT_END.

Here is a simple example: ::

    #include "pandokia_fct.h"

    CL_FCT_BGN()
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
    CL_FCT_END()

This example is minimal.  You can also use the more advanced features, such
as fixtures, suites, conditional tests, and advanced checks.  See the FCTX
documentation for details.


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

Using with the "run" test runner
-----------------------------------------------------------------------------

The "run" test runner just runs an external program that is pdk-aware.  You
would have your normal build system compile the test (as shown above),
then define the test something like this:

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


Using with the "maker" test runner
-----------------------------------------------------------------------------

If you use the "maker" test runner, you may be able to include your C
code directly in the test directory.  Pandokia can compile and run it
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

