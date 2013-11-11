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

def testerror():
    tda['a']=99
    tra['b']=99
    raise ValueError('this test has an error')
