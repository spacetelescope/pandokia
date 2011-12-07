'''
stupid doctest
'''
import pytest
import time

@pytest.mark.timeout(30)
def test_foo() :
    time.sleep(10)
    assert 0

def test_bar() :
    assert 0
