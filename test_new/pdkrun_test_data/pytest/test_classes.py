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
    @classmethod 
    def setup_class(self):
        self.tda=dict(a=1)

    def testpass(self):
        self.tra=dict(b=2)
        assert True

    def testfail(self):
        self.tra=dict(c=3)
        assert False

class TestClassSetup(object):

    @classmethod
    def setup_class(cls):
        cls.setup2()

    @classmethod
    def setup2(cls):
        cls.tda=dict(a=1,b=2)
        cls.tra=dict()

    def testpass(self):
        self.tra['c']=3
        assert True

    def testfail(self):
        # tra_c is getting reported in this test; I do not know if this is a bug or not.
        self.tra['d']=4
        assert False

class TestSetupErrors(object):

    @classmethod
    def setup_class(cls):
        raise Exception("Exception from setup")

    def testpass(self):
        self.tra['c']=3
        assert True

class TestSetupFirstTestErrors(object):

    @classmethod
    def setup_class(cls):
        pass

    def test1(self) :
        raise Exception("Exception from test1")

    def test2(self):
        pass


class TestSetupSecondTestErrors(object):

    @classmethod
    def setup_class(cls):
        pass

    def test1(self) :
        pass

    def test2(self):
        raise Exception("Exception from test2")

class TestTeardownErrors(object):

    @classmethod
    def setup_class(cls):
        pass

    def testpass(self):
        pass

    @classmethod
    def teardown_class(cls):
        raise Exception("Exception from teardown")

