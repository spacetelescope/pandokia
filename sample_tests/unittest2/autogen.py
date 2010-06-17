# An example of how to automatically generate tests in unittest2 
import unittest2


#####
#
# Here is the test object.
#
# unittest2 always requires a class that inherits from unittest2.TestCase
# In this example, we have only one such class.
#

class test_alphabet(unittest2.TestCase):

    # The test methods will be automatically generated, but they are
    # just calls to do_tst() which will do the real work.

    def do_tst( self, name, arg ) :
        # self - the object we are running in
        # name - the name the test as provided by the automatic test
        #       generation
        # arg - a parameter, which for many tests will be a list or tuple

        # for the purpose of the example, print what is happening.
        print "test ", name, arg

        # In this example, I am passing in an input value and an expected
        # result value.  You could work this any way you want.
        input, output = arg

        # not a very interesting thing to test -- can python find the
        # ascii value of letter
        x = ord(input)

        # make a regular assert
        self.assertEqual(x, output)

#####
#
# This function adds another test case to your test class.  In principle,
# you could copy this to a library somewhere.  This function works for
# any test class, as long as it has a do_tst(self, name, arg) method.
#

def create_test( test_class, name, arg ):
    '''
    Dynamically create a test in a unittest2.TestCase class

    Call this function to define new tests before you instantiate the test objects.

        test_class is the un-instantiated class

        name is the name of the test.  The prefix 'test_' is automatically
        prepended.

        arg is whatever argument value to pass on to self.do_tst()

    '''

    # test names must begin "test" for unittest2 to recognize them
    name = 'test_'+name

    # define a function - the local variables 
    def do_test(self):
        self.do_tst( name, arg )

    # fix the name of the function object
    do_test.__name__ = name

    # add the function object to the class that should contain the test
    setattr (test_class, do_test.__name__, do_test)


#####
#
# here is where we actually create the tests
#

# a list of data items - this could be dynamically generated too.

testlist = [ 
    ( 'A', 65 ),  
    ( 'B', 66 ),
    ( 'Z', 99 ),    # this is wrong, so one test can fail
    ]

# Loop over the list creating the tests.  For this example, I
# create each test twice, to show two different ways you might
# name your tests.

for k, arg in enumerate ( testlist ) :
    # To use a number for the test name:
    test_method = create_test ( test_alphabet, '%d'%k, arg )

    # To use part of the parameter value for the test name
    test_method = create_test ( test_alphabet, '%s'%(arg[0]), arg )

#####
#
# here is a standard way to invoke unittest2; pandokia doesn't use this,
# but you can.

if __name__ == '__main__':
    unittest2.main()

