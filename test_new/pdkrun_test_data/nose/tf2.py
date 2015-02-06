#Check that the plugin works if tda is present but not tra
from __future__ import print_function

tda=dict()

def test1():
    tda['answer']=42
    print("tda_answer=42")
    assert True
