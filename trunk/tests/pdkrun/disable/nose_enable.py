import pandokia.helpers.cases


class enabled_class(pandokia.helpers.cases.FileTestCase) :
    def test_one(self) :
        pass
    def test_two(self) :
        pass
    def test_three(self) :
        print "This test is going to fail now"
        assert(False)

class another_enabled_class(pandokia.helpers.cases.FileTestCase) :
    def test_one(self) :
        pass
    def test_two(self) :
        print "This test is going to fail now"
        assert(False)
    def test_three(self) :
        pass
