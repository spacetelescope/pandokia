import pandokia.helpers.minipyt as mpt


# notice that an object that does not set minipyt_shared will not get
# instatiated until we try to run one of the tests.  That means if it does
# not have any test methods, it will _never_ get instantiated.

class init_e(object) :
    __test__ = 1
    minipyt_shared=1

    def __init__(self) :
        assert False

class init_p(object) :
    __test__ = 1
    minipyt_shared=1

    def __init__(self) :
        assert True

class init_e(object) :
    minipyt_test = 1
    minipyt_shared=1

    def __init__(self) :
        raise Exception('Bomb')

class base(object) :
    minipyt_test = 0
    def __init__(self) :
        print "__init__",str(self)

    def __del__(self) :
        print "__del__",str(self)

    def setUp(self) :
        print "setUp"

    def tearDown(self) :
        print "tearDown"

    def test_p1(self) :
        assert True

    def test_p2(self) :
        assert True

    def test_p3(self) :
        assert True

    def test_f1(self) :
        assert False

    def test_f2(self) :
        assert False

    def test_e1(self) :
        raise Exception('Bomb')

    def test_e2(self) :
        x = 1.0 / 0.0

class shared(base) :
    minipyt_test = 1
    minipyt_shared=1

class unshared(base) :
    minipyt_test = 1
    minipyt_shared=0

