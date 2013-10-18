.. index:: single: runners; py.test

===============================================================================
Python - pytest - run tests with py.test 
===============================================================================

.. contents::

Overview
-------------------------------------------------------------------------------

Pandokia supplies a py.test plugin.  It is automatically enabled
when you use Pandokia to run a test with py.test.  

With this plugin, py.test can also write a Pandokia log file on its own, so you can
run it outside Pandokia.: ::

    py.test --pdk foo.py


Installing
-------------------------------------------------------------------------------

Documentation for installing py.test is available at http://pytest.org/
.  The py.test documentation includes quite a nice Installation and
Getting Started section.  If you are not already familiar with
py.test, it is a good introduction.


Enabling py.test
-------------------------------------------------------------------------------

Any file matching the pattern `*.pytest` will be executed with py.test.

The default runner for `*.py` is nose, but you can override this
per-directory by creating a `pdk_runners` file.

The most convenient way to do it is to declare that all python files
should be run with py.test::

    *.py	pytest

You can also mix py.test, nose, and other test runners::

    a.py	pytest
    b*.py	nose
    c*.py	minipyt
    d*.py	pytest


.. index:: single: timeout; py.test

Test timeouts
-------------------------------------------------------------------------------

You can define timeouts for individual tests like this::

    @pytest.mark.timeout(3)
    def test_foo() :
        # this test always times out
        time.sleep(6)

The timeout is always specified in seconds.  If the test runs longer
than that, the plugin will trigger SIGALRM that will raise an exception.

The plugin attempts to detect the application program setting a signal
handler for SIGALRM.  If a signal handler already exists for SIGALRM
when the test starts, or if the test ends with a signal handler
that is not the one that the plugin installed, the test will report
an error.  The exception will identify the signal handling function.

Timeouts are not implemented on Windows.

If the Pandokia plugin is not enabled, the timeout markup has no effect.

This feature is independent of PDK_TIMEOUT.

Knowing your test name
------------------------------------------------------------------------------

You can tell your test function the name that Pandokia knows it by
like this::

    def test_foo(pdk_test_name) :
        print "My pandokia test name is: ", pdk_test_name

You could use this in data that is reported outside the Pandokia system.
For example, when we test a web app, we sometimes include the test name
in the browser string so that we can later identify the actions of
specific tests in the httpd server logs.

If the pandokia plugin is present but not enabled, the value of
pdk_test_name is None.

If the pandokia plugin is not present, pdk_test_name is an unrecognized
funcarg and therefore it is an error to use it.


Capture of stdout/stderr
------------------------------------------------------------------------------

The plugin captures stdout/stderr by replacing sys.stdout and sys.stderr
with StringIO.  

More work is needed on this feature.  Currently, it disables the
capsys/capfd capability that is normally present in py.test.

If the pandokia plugin is not enabled, capsys/capfd work as normal for
py.test.


Disabling individual tests in py.test
-------------------------------------------------------------------------------

::

    @pytest.mark.skipif("True")
    def test_me() :
        pass

Bug: As of pandokia 1.2rc6, this causes the test to be reported as "Pass"
instead of "Disabled".

