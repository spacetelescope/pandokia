tda=dict(a=1)
tra=dict()

def testfail():
    tda['a']=1
    tra['b']=2
    raise AssertionError('test fails')

def testpass():
    tda['a']=11
    tra['b']=12
    assert True
