class test:
    minipyt_shared = 1

    tda = { }
    tra = { }

    def __init__( self ) :
        self.tda['arf'] = 'arf'
        self.tra['narf'] = 'narf'

    def test_1( self ) :
        self.tra['foo'] = 'foo'
        self.tra['narf'] = 'NARF'
