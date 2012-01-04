minipyt_test_order = 'line'

module_tda = { 'module' : 'this is a module tda' }

class shared(object) :

    __test__ = True

    minipyt_shared = True

    def __init__( self ) :
        print "init works"

    def classSetUp( self ): 
        print "classSetUp"
        self.class_tda['classSetUp'] = 'class setup'
        
    def setUp( self ) :
        print "setUp"
        self.class_tda['setUp'] = 'setup'

    def test_1( self ) :
        print "test_1"
        self.tda['test'] = 'test_1'
        self.tra['test'] = 'test_1'

    def test_2( self ) :
        print "test_2"
        self.tda['test'] = 'test_2'
        self.tra['test'] = 'test_2'

    def tearDown( self ):
        print "tearDown"
        self.class_tda['tearDown'] = 'teardown'

    def classTearDown( self ):
        print "class tearDown"
        self.class_tda['classTearDown'] = 'class teardown'


class not_shared(object) :

    __test__ = True

    minipyt_shared = False

    def __init__( self ) :
        print "init works"

    def classSetUp( self ): 
        print "classSetUp"
        self.class_tda['classSetUp'] = 'class setup'
        
    def setUp( self ) :
        print "setUp"
        self.class_tda['setUp'] = 'setup'

    def test_1( self ) :
        print "test_1"
        self.tda['test'] = 'test_1'
        self.tra['test'] = 'test_1'

    def test_2( self ) :
        print "test_2"
        self.tda['test'] = 'test_2'
        self.tra['test'] = 'test_2'

    def tearDown( self ):
        print "tearDown"
        self.class_tda['tearDown'] = 'teardown'

    def classTearDown( self ):
        print "class tearDown"
        self.class_tda['classTearDown'] = 'class teardown'

class class_setup_exception(object) :

    __test__ = True

    minipyt_shared = True

    def __init__( self ) :
        print "init class_setup_exception"

    def classSetUp( self ): 
        print "classSetUp"
        self.class_tda['classSetUp'] = 'class setup'
        raise Exception('ARF')
        
    def setUp( self ) :
        print "setUp"
        self.class_tda['setUp'] = 'setup'

    def test_1( self ) :
        print "test_1"
        self.tda['test'] = 'test_1'
        self.tra['test'] = 'test_1'

    def test_2( self ) :
        print "test_2"
        self.tda['test'] = 'test_2'
        self.tra['test'] = 'test_2'

    def tearDown( self ):
        print "tearDown"
        self.class_tda['tearDown'] = 'teardown'

    def classTearDown( self ):
        print "class tearDown"
        self.class_tda['classTearDown'] = 'class teardown'


class setup_exception(object) :

    __test__ = True

    minipyt_shared = True

    def __init__( self ) :
        print "init setup_exception"

    def classSetUp( self ): 
        print "classSetUp"
        self.class_tda['classSetUp'] = 'class setup'
        
    def setUp( self ) :
        print "setUp"
        self.class_tda['setUp'] = 'setup'
        raise Exception('ARF')

    def test_1( self ) :
        print "test_1"
        self.tda['test'] = 'test_1'
        self.tra['test'] = 'test_1'

    def test_2( self ) :
        print "test_2"
        self.tda['test'] = 'test_2'
        self.tra['test'] = 'test_2'

    def tearDown( self ):
        print "tearDown"
        self.class_tda['tearDown'] = 'teardown'

    def classTearDown( self ):
        print "class tearDown"
        self.class_tda['classTearDown'] = 'class teardown'

