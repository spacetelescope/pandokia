import unittest

class FromUnit(unittest.TestCase):
    def setUp(self):
        self.tda=dict(a=1)

    def testpass(self):
        self.tra=dict(b=2)
        self.failIf(False)

    def testfail(self):
        self.tra=dict(c=3)
        self.failIf(True)

class TestFromClass(object):
    def setUp(self):
        self.tda=dict(a=1)

    def testpass(self):
        self.tra=dict(b=2)
        assert True

    def testfail(self):
        self.tra=dict(c=3)
        assert False


class TestClassSetup(object):

    @classmethod
    def setUpClass(cls):
        """Always overridden by the child cases, but let's put some
        real values in here to test with"""
        cls.setup2()
        
    @classmethod
    def setup2(cls):
        #Do the common setup here.
        cls.tda=dict(a=1,b=2)
        cls.tra=dict()
        
    def testpass(self):
        self.tra['c']=3
        assert True

    def testfail(self):
        self.tra['d']=4
        assert False

