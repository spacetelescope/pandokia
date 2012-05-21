
def test_exception_with_formatted_string() :
    n=2
    print "HELLO"
    raise Exception("ARF %d"% n)

def test_exception_with_multiple_args() :
    n=2
    print "HELLO"
    raise Exception("ARF", n)

def test_fail() :
    print "HELLO"
    assert 0
