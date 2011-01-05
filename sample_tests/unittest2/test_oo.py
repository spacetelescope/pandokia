import unittest2

def plus2(x):
    return x+2

# The object contains a list of methods named "test_*" that are all
# the tests.  For each one, the object gets instatiated, then it calls
# setUp(), test_whatever(), and tearDown().
#
# In nose, you don't get a test result if the __init__ function raises
# an exception, but you do if setUp() does.

class test_1(unittest2.TestCase) :

    a = plus2(4)

    def __init__( self, arg = '' ) :
        print "TEST1 INIT"
        super(test_1, self).__init__(arg)
        print "ARG=",arg
        self.b = plus2(6)

    def setUp( self ) :
        # called before each test
        print 'test setup'
        self.c = plus2(8)

    # methods named 'test_*' are tests
    def test_a( self ) :
        self.tra['a'] = self.a
        assert self.a == 6

    def test_b( self ) :
        self.tra['b'] = self.b
        assert self.b == 8

    def test_c( self ) :
        self.tra['c'] = self.c
        assert self.c == 10

    def test_d( self ) :
        print "example of a failing test"
        self.tra['c'] = self.c
        assert self.c == 12

    def test_e( self ) :
        raise Exception("yow!")
        i = 10
        self.tda['i'] = i
        x = plus2(i)
        self.tra['answer'] = x
        assert x == 12

    def tearDown( self ) :
        # called after each test
        print 'test teardown'

if __name__ == '__main__' :
    unittest2.main()
