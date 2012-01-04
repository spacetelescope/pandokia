tda=dict()
tra=dict()
def setup():
    tda['a']=1
    tra['b']=2

def testpass():
    tda['c']=3
    print "passing"
    assert True

def testfail():
    tra['d']=4
    print "failing"
    assert False
