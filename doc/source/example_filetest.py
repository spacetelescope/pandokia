"""This file contains examples of how to subcless from and use the
FileTestCase class provided by pandokia."""

#Import the file containing the base class
from pandokia import classes


#Subclass from the FileTestCase
class SimpleTest(classes.FileTestCase):
    """The simplest case defines only test methods, and uses
    the builtin setUp() and tearDown() methods."""
    
    def test1(self):
        #Run a command that generates some data.
        #The command string and the return status of the command
        #are saved in tda and tra, respectively.
        self.command("echo Hello World > hw1.txt")
        
        #Compare the file to a pre-existing reference file of the
        #same name except with the prefix "ref.". For example, this
        #test compares against "ref.hw1.txt". The name of the file
        #is saved as a tda.
        self.check_file("hw1.txt","binary")

    def test2(self):
        #You can run multiple commands and/or multiple file
        #comparisons within a given test, and pass a suffix
        #to the method to distinguish the files. Suffixes may
        #be integers or strings; they're used as str(suffix).
        self.command("echo Goodbye World > hw1.txt", suffix=1)
        self.command("pwd",suffix='status')
        self.check_file("hw1.txt","binary",suffix='header')
        self.check_file("hw2.txt",'binary',suffix='data')

    def test3(self):
        #Same as test1, but shows the use of additional tdas
        self.tda['x']=42
        self.command("cat %s > answer.txt"%self.tda['x'])
        self.check_file("answer.txt","binary")

    def test4(self):
        #Of course you can write the usual sort of test method
        #in these classes, which may also use tda and tra.
        self.tda['x']=1
        self.tda['y']=3
        ans=1+3
        self.tra['ans']=ans
        self.assertEqual(5,ans)
 
#Example with an expensive setup & multiple tests
from pandokia.helpers import filecomp

class ExpensiveTest(classes.FileTestCase):
    """This class shows an example of using a class setup method to run
    an expensive command, such as a program that produces many files,
    only once, while placing each file comparison as its own test.

    Each file that passes its comparison will be deleted by the builtin
    tearDown. To suppress this behavior, just define your own tearDown"""


    #You must use the builtin classmethod decorator for this.
    @classmethod
    def setUpClass(cls):
        #You can't use the built-in .command() method here, because
        #there is no instance yet. But you can use the standalone
        #command function .
        filecomp.command('run myprog > myprog.stdout')

        #Similarly, you cannot set any tdas/tras at this point because
        #they are bound to the instance.

    def test1(self):
        self.check_file('myprog.stdout','binary')

    def test2(self):
        self.check_file('tabresult.fits','fits')

    def test3(self):
        self.check_file('otherfile.txt','text')

## #Example with your own setUp or tearDown methods
class SetupTest(classes.FileTestCase):
    """This shows an example of using the FileTestCase in a case where you
    also need to do some of your own setup and teardown. In this case,
    you must be sure to explicitly call the parent routines."""

    def setUp(self):
        self.a=42
        self.do_more_setup()
        #You must call the parent setUp
        classes.FileTestCase.setUp(self)

    def test1(self):
        self.command('some command > cmd.out')
        self.check_file('cmd.out','binary')

    def tearDown(self):
        self.do_some_cleanup()
        #You must call the parent tearDown
        classes.FileTestCase.tearDown(self)

    def do_some_cleanup(self):
        pass
    
    def do_more_setup(self):
        self.input='input'
