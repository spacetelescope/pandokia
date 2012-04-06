'''
This is a module doctest that will fail.
>>> 1
2
'''
# Nope - we don't do doctest anymore

def test_foo() :
    '''This is not a doctest:
    >>> 1
    1
    >>> 2
    3
    '''
    assert 0

def test_bar() :
    '''This is also not a doctest:
    >>> 1
    3
    '''
    assert 1
