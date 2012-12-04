import pandokia.helpers.cases


class disabled_class(pandokia.helpers.cases.FileTestCase) :
    def test_one(self) :
        assert(False)
    def test_two(self) :
        pass
    def test_three(self) :
        pass

class another_disabled_class(pandokia.helpers.cases.FileTestCase) :
    def test_one(self) :
        assert(False)
    def test_two(self) :
        pass
    def test_three(self) :
        pass
