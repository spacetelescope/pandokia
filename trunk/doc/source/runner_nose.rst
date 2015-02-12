.. index:: single: runners; nose

===============================================================================
Python - nose - run tests with nose
===============================================================================

:abstract:

    Pandokia can use nose 0.11.1 or 1.0 to run tests.  It uses
    a nose plugin to gather the test results.  There are some
    limitations.

.. contents::

Overview
-------------------------------------------------------------------------------

TODO: Write this section.

Really, you just write nose tests in a python file, then use "pdkrun
file.py" or "pdkrun -r ." or something to run them.  Each file of
tests runs is a different process.  There is no good way to pass
advanced nose options through pandokia, but we typically find that
we don't need to.  If you want to debug a test, you can do that
outside pandokia with something like "nosetests --pdb file.py"

Disabling individual tests in nose
-------------------------------------------------------------------------------

It is hard to find this in the nose documentation: ::

    from nose.exc import SkipTest 

    def test_foo() :
        raise SkipTest('busted')


