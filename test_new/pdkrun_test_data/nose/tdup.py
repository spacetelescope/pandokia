# This is a bug:  The doctest is a test named "test_foo", then the
# function is also a test named "test_foo".
def test_foo() :
    """
>>> print 'foo'
foo
>>>
"""
    pass
