tda=dict()
tra=dict()
def setup():
    tda['a']=1
    tra['b']=2

def testpass():
    # this is a buggy test, not a buggy plugin.  tda is a global, so it
    # is not cleared before the next test.
    tda['c']=3
    print "passing"
    assert True

def testfail():
    tra['d']=4
    print "failing"
    assert False
