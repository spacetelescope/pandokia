.. index:: single: patterns; parameterized tests

===============================================================================
Python: Parameterized Tests
===============================================================================

:abstract:

    When you have a list and you want to run the same test function
    for each item in the list.

minipyt
-------------------------------------------------------------------------------

::

    import pandokia.helpers.pycode as pycode

    p_list = [ 
         ( 'nameA', 'v1', 'v2' ), 
         ( 'nameB', 'va', 'vc' ), 
         ]

    for name, v1, v2 in p_list :
        with pycode.test(name) :
            assert foo(v1, v2)

The tests will be named ``nameA`` and ``nameB``

py.test
-------------------------------------------------------------------------------

::

    import pytest

    p_list = [ 
         ( 'nameA', 'v1', 'v2' ), 
         ( 'nameB', 'va', 'vc' ), 
         ]

    @pytest.mark.parametrize( ('name', 'v1', 'v2'), p_list)
    def test_thing(name, v1, v2) :
        assert foo(v1,v2)

The tests will be named ``test_thing[nameA-v1-v2]`` and
``test_thing[nameB-va-vc]``

Take notice that the spelling of "parametrize" does not contain an
"e" before the "r".

nose
-------------------------------------------------------------------------------

::

    p_list = [ 
         ( 'nameA', 'v1', 'v2' ), 
         ( 'nameB', 'va', 'vc' ), 
         ]

    def run_it( v1, v2 ) :
        assert foo(v1,v2)

    def test_thing() :
        for name, v1, v2 in p_list :
            yield run_it, v1, v2

The tests will be named ``test_thing('v1',_'v2')`` and
``test_thing('va',_'vc')``
