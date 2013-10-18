.. index:: single: runners; minipyt

===============================================================================
Python - minipyt - a simple but reliable test runner, built in to Pandokia
===============================================================================

:abstract:

    minipyt (mini python test) runs tests written in python.
    The tests can be either functions, classes, or simple code
    sequences managed by the "with" statement.  For test classes,
    you can have one instance for each test method or you can
    have a single instance shared by all test methods.

    A major advantage of minipyt is that any test file __always__
    reports a test result of some kind, no matter what kinds of
    errors occur in that file.  Even a python file that fails to
    import because of syntax errors will report at least one record.
    This differs from nose and py.test because the plugin
    architecture of those systems is not able to report certain
    kinds of errors.


.. contents::

Importing the Test File
-------------------------------------------------------------------------------

minipyt runs tests by importing a python file, searching for tests,
then running those tests.

There is a test record for the act of importing the file.  For example,
xyz.py will have a test name of "xyz".  The status value reported is:

    - Pass means that minipyt was able to import the file and
      examine it for tests.  If the file executed any code during
      the import, it succeeded

    - Error means that an exception was raised while importing
      the file or examining it for tests.

    - Fail means that AssertionError was raised during the import.

For pure python, minipyt will always report at least one test record
for each file, no matter how badly the import goes.  ( If the test uses
a C extension that core dumps the python interpreter, there is still a
possibility to lose the test report. )

It is possible to consider a python file to be a single test.  The
simplest minipyt test that passes is::

    assert True

and the simplest test that fails is::

    assert False

In these examples, the name of the test matches the name of the file.

You can report attributes for the module by loading them into the  global
dictionaries module_tda and module_tra.

Recognizing Tests
-------------------------------------------------------------------------------

After the import (which may execute a test directly), these things
in the namespace of the imported module are recognized as tests:

    - functions that have names beginning or ending with "test",
      that are not decorated with ``pandokia.helpers.minipyt.nottest``
      or ``nose.tools.nottest``

    - classes that have names beginning or ending with "test"
      that are not decorated with ``pandokia.helpers.minipyt.nottest``
      or ``nose.tools.nottest``

    - functions decorated with ``pandokia.helpers.minipyt.test``
      or ``nose.tools.istest``

    - classes decorated with ``pandokia.helpers.minipyt.test``
      or ``nose.tools.istest``

By default, tests are executed in order by line number.  If you
want to order the tests by name, set the global variable::

    minipyt_test_order = 'name'

in your test module.  

Sorting by line number is unreliable for decorated functions because
the line number used for the sort may be the line number of some
part of the decorator, not the line number of your code.

Executing Test Functions 
-------------------------------------------------------------------------------

Test functions are executed by calling the function with no parameters.
The test passes if it returns, fails if it raises AssertionError,
and errors if it raises any other exception.

If the function is decorated with a setup function, the setup is called
before the test function.  Any exception from the setup is handled the
same as if it were raised by the function itself.

If the function is decorated with a teardown function, the teardown is
called after the function.  This happens even if the test function
terminated with an exception.  Any exception in the teardown function
will cause the test to report the status Error.


Executing Test Classes
-------------------------------------------------------------------------------

A Test Class defines an object with tests defined as class methods.
A method is a test if the name starts or ends with "test" and has
not been decorated with nottest, or if it has been decorated with
pandokia.helpers.minipyt.test or nose.tools.istest.


single object instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the class has the attribute minipyt_shared=True, only one object instance is
created; all the tests run in that same instance.  This can be helpful
if the class initialization performs some shareable operation, such as
connecting to a database.

::

    - create object

    - call obj.classSetUp()

    - for each test method

        call obj.setUp()
        call test method
        call obj.tearDown()

    - call obj.classTearDown()

obj.class_tda and obj.class_tra are attributes that belong to the class.

obj.tda and obj.tra are attributes that belong the the most recently executed
tests.  The attribute set reported is the union of class_tXa and tXa.


multiple object instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the class has the attribute minipyt_shared=False or if the attribute
is not set, a new instance is created for each test.  This is similar
to other test frameworks such as nose, py.test, and unittest.

::

    - for each test method

        create obj

        call obj.classSetUp()

        call obj.setUp()

        call test method

        call obj.tearDown()

        call obj.classTearDown()


obj.class_tda and obj.class_tra are attributes that belong to the class.

obj.tda and obj.tra are attributes that belong the the most recently executed
tests.  The attribute set reported is the union of class_tXa and tXa.


running the test methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

minipyt will call each method to execute the test.  If the class has
a method named "setUp", it will be called before each test method.
Any exceptions or assertions in the setUp method will have the same
effect as if they happened in the test function.

If the class has a method named "tearDown", it will be called after the
test method.  This happens even if the test method terminated with
an exception.  Any exception in the teardown method will cause the
test to report the status Error.

The names setUp and tearDown are compatible with nose.  The
nose.tools.with_setup decorator has no effect on class methods.


Linear Execution in Sequential Code ("with" statement)
-------------------------------------------------------------------------------

When python imports a file, the code in that file is executed.
minipyt can report that as a single test, or you can use "with"
statements to divide it into multiple tests.

This file contains two tests named "foo" and "bar":

::

    import pandokia.helpers.pycode as pycode

    with pycode.test( 'foo' ) as t:
        pass

    with pycode.test( 'bar' ) as t:
        assert False

You can set attributes on the test by assigning to the tda or tra
dicts in the context manager:

::

    with pycode.test( 'baz' ) as t:
        t.tda['yes'] = 1
        t.tra['no']  = 0 
        assert 2 + 2 = 4

Tests that are defined in "with" statements can be nested:

::

    with pycode.test( 'foo' ) :
        # this test is named "foo"
        print "set up in foo"
        with pycode.test( 'bar' ) :
            # this test is named "foo.bar"
            print "bar"
            assert 2 + 2 = 5
            print "if we got here, not in room 101"
        print "more output in test foo"

Tests that are defined in "with" statements may be used inside test functions:

::

    def test_plover() :
        # this test is named "plover"
        print "just a plover"
        with pycode.test( 'egg' ) :
        # this test is named "plover.egg"
            print "An emerald the size of a plover's egg"
            with pycode.test( 'hatch' ) :
                # this test is named "plover.egg.hatch"
                assert 1
        print "that laid an egg"


You can use this feature to dynamically define tests:

::

    for x, y  in some_list :
        with pycode.test( str(x) ) :
            assert f(x,y)

This example is similar to the parameterized tests in py.test, but
you do not need to have the entire list of tests before the tests
start running.


why not py.test parameterized test or nose generators?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If those methods are more convenient, you should use them.  Here are some
features that can be an advantage of this approach:

 - the simplicity of linearly executing procedural code:  There are
   no callbacks, no implicit ordering, no separate setup/teardown
   functions to keep track of.  

 - you choose the test name; in a parameterized test or a generator,
   all the parameters to the test function are included in the test
   name, even when they are not all relevant.  The pandokia plugins
   for pytest/nose cannot know which parameter values may be excluded
   from the name, so they include them all.

 - easy setup/teardown

   ::

    with test('group') :
        db = sqlite3.connect('test.db')
        with test('first') :
            ...
        with test('second') :
            ...
        db.close()

 - arbitrarily deep nesting:  By nesting "with test()" statements, you
   can build aribitrarily deep test hierarchies, if it is suitable for your
   application.


Special Features
-------------------------------------------------------------------------------

dots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

minipyt is normally silent when it runs tests.  If you want it to print dots,
you can

    - set the environment variable PDK_DOTS

    - set the module variable minipyt_dots_mode

to one of these values:

    - a zero-length string gives the default behaviour

    - 'S' shows a dot for each passing test and the status for any
      non-passing test
      
    - 'N' shows a dot for each passing test and the test name and
      status for any non-passing test

    - 'O show a dot for each passing test and the test name, status, and
      output for any non-passing test

If you specify both the environment variable and the module variable, the
module variable takes precedence.::

    # no dots
    minipyt.dots_mode = None

    # show dots and the name+status of the non-passing test
    minipyt.dots_mode = 'N'


prevent using nose by mistake
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

nose should recognize and execute many minipyt tests, but you can explicitly
prevent using a test file with nose by::

    import pandokia.helpers.minipyt as mph
    mph.noseguard()

``noseguard()`` raises an exception if 'nose' is in sys.modules.

This prevents importing the file if nose is also loaded.  If pandokia
is using minipyt as the test runner, nose will not have been imported.
If nose is in sys.modules, we assume that is because the test file
was mistakenly run using nose.

Presumably, this may cause you problems if you are trying to import the
test into an interactive python.  If so, disable this function with::

        import pandokia.helpers.minipyt as mph
        mph.disable_noseguard = True



Decorators
-------------------------------------------------------------------------------

minipyt
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These decorators are available in pandokia.helpers.minipyt:

    - ``test``

        marks a function or class as a test, even if the name
        does not otherwise look like a test

    - ``nottest``

        marks a function or class as not a test, even if the
        name looks like it should be a test

All work on both functions, classes, and methods.

nose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many nose decorators work in minipyt tests.::

    import nose.tools

    @nose.tools.raises(IOError)
    def test_mine() :
        ...

These decorators are known to work:

    - ``nose.tools.raises``

    - ``nose.tools.timed``

    - ``nose.tools.with_setup`` (on test functions only, not class
      methods)

    - ``nose.tools.nottest``

    - ``nose.tools.istest``

