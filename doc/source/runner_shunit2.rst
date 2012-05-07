.. index:: single: runners; shunit2

===============================================================================
shunit2 (bourne shell) - an xUnit test framework for shell scripts
===============================================================================

Overview
----------------------------------------------------------------------

This runner uses a modified version of shunit2; the modifications implement
support for a plugin architecture.  

As of this writing, patches to implement this plugin architecture have been
submitted to the shunit2 maintainer, but have not been accepted into the
source code.

The plugin that reports to the Pandokia system is distributed with Pandokia.

Installing
----------------------------------------------------------------------

You can download the patched shunit2 from http://stsdas.stsci.edu/shunit/

Download the file "shunit2" and put it on your PATH somewhere.  No changes
to your installed Pandokia are required.

This copy of shunit2 is identified by SHUNIT_VERSION='2.1.6plugin'

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
in doc/shunit2.rst and at 
http://shunit2.googlecode.com/svn/trunk/source/2.1/doc/shunit2.html

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
