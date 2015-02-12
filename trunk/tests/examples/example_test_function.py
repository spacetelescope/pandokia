"""Sample tests showing how to use TDAs and TRAs with test functions.

For a test function to report TDAs and TRAs, your function should create
global variables named 'tda' and 'tra' that are dictionaries containing
the TDA and TRA values.  When your test function returns, the nose plugin
will report the the content of these global dictionaries as the tda_*
and tra_* values.

The nose plugin will clear the dictionaries after each use, so it is
not necessary for you to clear them.

Within each test function, the dictionaries can be updated using any
legal dictionary syntax:

  tda['cat']=43

  tda.update(some_other_dict)

  global tda
  tda = { 'arf' : 'narf' }

"""

tda={}
tra={}

def setUp():
    print "You can define a setup function that is run once, before any tests"

def test1():
    tda.update(dict(cat=2,mouse=1))
    print "tda_cat=2, tda_mouse=1, no tras"
    assert tda['cat'] > tda['mouse']

def test2():
    ans=5-3
    tra['ans']=ans
    print "tra_ans=2, no tdas"
    assert ans > 0

def test3():
    tda['dog']=0
    tra['plant']=43
    print "tda_dog=0, tra_plant=43"
    assert True

def test_just_set_it():
    # remember to say global if you plan to assign to tda or tra
    global tda              
    tda = { 'dog': 101, 'mice': 3 }
    print "tda_dog = 101, tda_mice = 3"
    assert True

