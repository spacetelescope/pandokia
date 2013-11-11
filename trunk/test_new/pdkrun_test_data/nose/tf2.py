#Check that the plugin works if tda is present but not tra
tda=dict()

def test1():
    tda['answer']=42
    print "tda_answer=42"
    assert True
