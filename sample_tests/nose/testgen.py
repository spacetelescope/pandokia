tda=dict()
tra=dict()

def testgen():
    for i in range(3):
        def go(a,b,c):
            tda['a']=a
            tda['b']=b
            tra['c']=c
        yield go, i,i+1,i+2
