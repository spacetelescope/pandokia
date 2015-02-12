import unittest
import os
import uptree

class testup(unittest.TestCase):
    def setUp(self):
        #find our root directory
        here=os.path.abspath(os.path.dirname(__file__))
        cols=here.split(os.path.sep)
        root=os.path.sep.join(cols[0:-3])

        self.local=['pdk_environment',
                    'b/pdk_environment',
                    'b/c/d/pdk_environment']
        self.ref=['%s%s%s'%(root,os.path.sep,x) for x in self.local]

    def testupenv(self):
        flist=uptree.find('pdk_environment')
        self.assert_(self.ref == flist,'Expected %s, Got %s'%(self.ref,flist))
        
