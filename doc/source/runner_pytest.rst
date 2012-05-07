.. index:: single: runners; py.test

===============================================================================
pytest (Python) - py.test
===============================================================================

:abstract:

	Pandokia can use py.test 2.2 to run tests.

.. contents::

Overview
-------------------------------------------------------------------------------

Pandokia supplies a py.test plugin.  It is automatically enabled when
you use Pandokia to run a test with py.test.

You can run py.test with the Pandokia plugin by using the special program pdkpytest::

	pdkpytest foo.py

You can declare the plugin by one of the methods known to py.test, but you
must say --pdk to enable it::

	setenv PYTEST_PLUGINS pandokia.helpers.pytest_plugin
	py.test --pdk foo.py

	py.test -p pandokia.helpers.pytest_plugin --pdk foo.py

Enabling the plugin always cause a PDK_LOG file to be created, but you
can ignore it.

Bug:  the plugin does not yet correctly restore stdout when using --pdb


Enabling py.test
-------------------------------------------------------------------------------

The default test runner for python files is currently nose.  To direct
pandokia to use py.test, create a file named `pdk_runners` that 
declares that some files should be run with the runner `pytest`.

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
handler for SIGALRM.  If a signal handler already exists for SIGALRM,
or if the test ends with a signal handler that is not the one that the
plugin installed, the test will report an error.  The exception will
identify the signal handling function.

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
