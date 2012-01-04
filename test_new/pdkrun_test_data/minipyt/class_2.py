
class init_f_s(object) :
    minipyt_test = 1
    shared_instance = 1
    def __init__(self) :
        print "init"
        assert False

class init_f_u(object) :
    minipyt_test = 1
    shared_instance = 0
    def __init__(self) :
        print "init"
        assert False
    def test_(self) :
        print "test"

class init_f_u2(object) :
    minipyt_test = 1
    def __init__(self) :
        print "init"
        assert False
    def test_(self) :
        print "test"
