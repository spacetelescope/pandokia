from pandokia.helpers.minipyt import *

print "minipyt disables test"

@test
def function_active() :
    print "test"

@test
@disable
def function_disable() :
    print "test"

class class_active(object) :
    # can't decorate classes in py2.5, so do this:
    __test__ = 1

    def setUp(self) :
        print "test"

    def test1(self) :
        print "test"

    def test2(self) :
        print "test"

    def test3(self) :
        print "test"

class class_disable(object) :
    # can't decorate classes in py2.5, so do this:
    __test__ = 1
    __disable__ = 1

    def setUp(self) :
        print "test"

    def test1(self) :
        print "test"

    def test2(self) :
        print "test"

    def test3(self) :
        print "test"


class class_partial(object) :
    # can't decorate classes in py2.5, so do this:
    __test__ = 1

    def setUp(self) :
        print "test"

    @disable
    def test1(self) :
        print "test"

    @disable
    def test2(self) :
        print "test"

    def test3(self) :
        print "test"

