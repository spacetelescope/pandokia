import pytest
import time

@pytest.mark.timeout(3)
def test_very_slow1():
    print "START"
    time.sleep(10)
    print "END"

@pytest.mark.timeout(5)
def test_not_slow1():
    print "START"
    time.sleep(3)
    print "END"

def test_fast() :
    pass

