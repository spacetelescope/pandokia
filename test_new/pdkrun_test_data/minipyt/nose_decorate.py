import nose.tools

@nose.tools.raises(IOError)
def test_2() :
        raise IOError('arf')

@nose.tools.raises(IOError)
def test_1() :
        pass

def setup() :
        print "setup"

def teardown() :
        print "teardown"

def broken_teardown() :
        raise IOError('broken teardown')

@nose.tools.with_setup(setup)
def test_s1() :
        print "test_s1"
        pass

@nose.tools.with_setup(teardown=teardown)
def test_s2() :
        print "test_s2"
        pass

@nose.tools.with_setup(setup=setup,teardown=teardown)
def test_s3() :
        print "test_s3"
        pass

@nose.tools.with_setup(setup=setup,teardown=broken_teardown)
def test_s4() :
        print "test_s4"
        pass

@nose.tools.with_setup(setup=setup,teardown=broken_teardown)
def test_s5() :
        print "test_s5"
        assert False

@nose.tools.with_setup(setup=setup,teardown=broken_teardown)
def test_s6() :
        print "test_s6"
        raise IOError('broken s6')

@nose.tools.with_setup(setup=setup,teardown=teardown)
def test_s7() :
        print "test_s7"
        raise IOError('broken s7')

@nose.tools.with_setup(setup=setup,teardown=teardown)
def test_s8() :
        print "test_s8"
        assert False

