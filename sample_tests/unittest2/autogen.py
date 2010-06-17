import unittest2

class test_class(unittest2.TestCase):

    def setUp(self):
        pass

    def do_tst( self, name, arg ) :
        print "test ", name, arg
        input, output = arg
        x = ord(input) - 32
        print 'x=',x
        assert x == output

# http://stackoverflow.com/questions/2798956/python-unittest-generate-multiple-tests-programmatically

def create_test( test_obj, name, arg ):
    def do_test(self):
        self.do_tst( name, arg )
    do_test.__name__ = name
    setattr (test_obj, do_test.__name__, do_test)

testlist = [ 
    ( 'a', 65 ),  
    ( 'b', 66 ),
    ( 'z', 99 ),
    ]

for k, arg in enumerate ( testlist ) :
    test_method = create_test ( test_class, 'test_%d'%k, arg )

if __name__ == '__main__':
    unittest2.main()

