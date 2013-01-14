import unittest 
import os, shutil
import pprint
import pandokia.envgetter as envgetter
import sys


class FakeTree(unittest.TestCase):
    def setUp(self):
        """Set up a nice fake tree and experiment with it"""
        os.mkdir('faketree')
        open('faketree/pandokia_top','w').close()
        os.mkdir('faketree/a')
        os.mkdir('faketree/b')
        os.mkdir('faketree/a/c')
        os.mkdir('faketree/a/d')
        os.mkdir('faketree/b/e')
        os.mkdir('faketree/a/d/f')
        self.base=dict(sky='blue',grass='green',name='NoBody')
        self.x=envgetter.EnvGetter(defdict=self.base,mock=True)


    def tearDown(self):
        shutil.rmtree('faketree')

 

    def testtop(self):
        tst=self.x.envdir('faketree')
        ref=dict(self.base,name='faketree/pdk_environment')
        ref[0]=0
        self.assertEqual(ref,tst)

    def testbottom(self):
        tst=self.x.envdir('faketree/a/d/f')
        ref=dict(self.base,name='faketree/a/d/f/pdk_environment')
        for k in [0,1,2,3]:
            ref[k]=k
        self.assertEqual(ref,tst)

    def testmiddle(self):
        tst=self.x.envdir('faketree/b')
        ref=dict(self.base,name='faketree/b/pdk_environment')
        for k in [0,1]:
            ref[k]=k
        self.assertEqual(ref,tst)


#------------------------------------------------------------

class EnvTree(unittest.TestCase):

    root='testtree/pdkenv/'
    
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={})
        self.dirname='testtree/pdkenv/a/'
        self.ansfile='testtree/pdkenv/a/dict.irafdev'
        self.setref()

    def setref(self):
        self.ref={}
        f=open(self.ansfile)
        for line in f:
            try:
                key,val=line.strip().split('=')
                self.ref[key]=val
            except ValueError:
                pass #blank line
        f.close()

    def testdict(self):
        tst=self.x.envdir(self.dirname)
        klist=set(self.ref.keys())
        klist.update(set(tst.keys()))
        bad={}
        for k in klist:
            try:
                if self.ref[k]!=tst[k]:
                    bad[k]=(self.ref[k],tst[k])
            except KeyError:
                bad[k]=self.ref.get(k),tst.get(k)
        msg="""\nDirname: %s -- Context: %s
        Mismatches:\n%s"""%(self.dirname,
                          self.x.context,
                          pprint.pformat(bad))
        self.assertEqual(self.ref,tst,msg)

    def testrecip(self):
        tmp=self.x.envdir(self.dirname)
        node = self.x.nodes[self.dirname]
        if node.parent is not None:
            self.assert_(node.parent.name in self.x.nodes)
        else:
            self.assert_(node.istop)

    def testrecip2(self):
        self.x.populate(self.dirname)
        node = self.x.nodes[self.dirname]
        if node.parent is not None:
            self.assert_(node.parent.name in self.x.nodes)
        else:
            self.assert_(node.istop)

    def testexport(self):
        #Braindead test: just check the length of the emitted file
        self.outname=os.path.join(self.dirname,'export.env')
        self.x.export(self.dirname,format='env',fh=open(self.outname,'w'))
        self.ref=envgetter.parsefile(self.outname)
        os.unlink(self.outname)
        self.assertEqual(len(self.ref),
                         len(self.x.nodes[self.dirname].final) - len(self.x.defdict))
    def testexportfull(self):
        #Braindead test: just check the length of the emitted file
        self.outname=os.path.join(self.dirname,'export.env')
        self.x.export(self.dirname,format='env',fh=open(self.outname,'w'),
                      full=True)
        self.ref=envgetter.parsefile(self.outname)
        os.unlink(self.outname)
        self.assertEqual(len(self.ref),
                         len(self.x.nodes[self.dirname].final))
               
class Envaa(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={})
        self.dirname=self.root+'a/a/'
        self.ansfile=self.dirname+'dict.irafdev'
        self.setref()

class Envaa_x(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={},context='irafx')
        self.dirname=self.root+'a/a/'
        self.ansfile=self.dirname+'dict.irafx.gaudete'
        self.setref()



class Envab(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={})
        self.dirname=self.root+'a/b/'
        self.ansfile=self.dirname+'dict.irafdev'
        self.setref()


class Envab_x(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={},context='irafx')
        self.dirname=self.root+'a/b/'
        self.ansfile=self.dirname+'dict.irafx.gaudete'
        self.setref()

class Enva_x(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={},context='irafx')
        self.dirname=self.root+'a/'
        self.ansfile=self.dirname+'dict.irafx.gaudete'
        self.setref()

class Envb(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={'PATH':'/your/other/path'})
        self.dirname=self.root+'b/'
        self.ansfile=self.dirname+'dict.irafdev'
        self.setref()

class Envcaa(EnvTree):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={})
        self.dirname=self.root+'c/a/a/'
        self.ansfile=self.dirname+'dict.irafdev'
        self.setref()

#Still tbd: Enva_x_thor, Envab_x_thor

#----------------------------------------------------
class TestTca(unittest.TestCase):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict=dict(os.environ,
                                                cat='sienna',
                                                grass='green'))
        self.dirname='testtree/pdkenv/b/f'
        self.outname=os.path.join(self.dirname,'test.tca')
        self.refname=os.path.join(self.dirname,'export.tca')
        self.ref=open(self.refname).readlines()

    def tearDown(self):
        os.unlink(self.outname)
        
    def testexport(self):
        self.x.export(self.dirname,format='tca',
                 fh=open(self.outname,'w'))
        tst=open(self.outname).readlines()
        self.ref.sort()
        tst.sort()
        self.assertEqual(self.ref,tst,msg=ppmsg(self.ref,tst))
                         
#----------------------------------------------------

class TestSub(unittest.TestCase):
    def setUp(self):
        self.x=envgetter.DirLevel('a',empty=True)
        self.x.final=dict(sky='blue',
                          grass='$sky/green',
                          roses='red',
                          violets='$sky')
        self.ref=dict(sky='blue',
                      grass='blue/green',
                      roses='red',
                      violets='blue')

    def testsub(self):
        self.x.substitute()
        self.assertEqual(self.ref,self.x.final)

class TestPathsub(unittest.TestCase):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={'PATH':'/some/default/path/'})
        self.y=envgetter.DirLevel('a',container=self.x,empty=True)
        self.y.leveldict={'PATH':'/my/special/path:$PATH'}
        self.ref='/my/special/path:/some/default/path/'
        self.path='PATH'
        
    def testpath(self):
        self.y.merge()
        self.y.substitute()
        tst=self.y.final
        self.assertEqual(self.ref,tst[self.path])
                                   
class PS2(TestPathsub):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={'PYTHONPATH':'/ref/python/place/'})
        self.y=envgetter.DirLevel('a',container=self.x,empty=True)
        self.y.leveldict={'PYTHONPATH':'/foo/bar:${PYTHONPATH}:/bar'}
        self.ref='/foo/bar:/ref/python/place/:/bar'
        self.path='PYTHONPATH'

class PS3(TestPathsub):
    def setUp(self):
        self.x=envgetter.EnvGetter(defdict={'PYTHONPATH':'/ref/python/place/'})
        self.y=envgetter.DirLevel('a',container=self.x,empty=True)
        self.y.leveldict={'PYTHONPATH':'/foo/bar:${PYTHONPATH}'}
        self.ref='/foo/bar:/ref/python/place/'
        self.path='PYTHONPATH'

class TestUnsub(unittest.TestCase):
    def setUp(self):
        self.dirname='testtree/pdkenv/a/e'
        self.x=envgetter.EnvGetter(defdict={})
        self.outname='testtree/pdkenv/a/e/test_export.dat'
        self.ref=envgetter.parsefile('testtree/pdkenv/a/e/exported_env')

    def testexport(self):
        self.x.populate(self.dirname)
        self.x.export(self.dirname,format='env',fh=open(self.outname,'w'))
        tst=envgetter.parsefile(self.outname)
        os.unlink(self.outname)
        self.assertEqual(self.ref,tst)

    def testenv(self):
        try:
            tmp=self.x.envdir(self.dirname)
            self.fail()
        except KeyError:
            pass


        
def dict_compare(ref, tst, title='', full=False ) :
    '''
    dict_compare( reference_dictionary, test_dictionary,
        title='', full=False )

    Compare reference_dictionary to test_dictionary.  Returns true if
    they match, false otherwise.  If they do not match, the differences
    are pretty-printed to standard output.

    title is displayed at the start of the output.

    set full=True to display all dictionary values, even the ones that
    were the same.  But there is still no output if the dictionaries
    match.

    '''
    if ref == tst :
        return True
    sys.stdout.write("dict_compare: %s\n"%title)
    l = [ x for x in ref ]
    for x in tst :
        if not x in l :
            l.append(x)
    l.sort()
    for x in l :
        if not x in ref :
            sys.stdout.write( "\t%s missing from ref\n"%x)
        elif not x in tst :
            sys.stdout.write( "\t%s missing from tst\n"%x)
        else :
            if ref[x] != tst[x] :
                sys.stdout.write( "\t%s\n"%x)
                sys.stdout.write( "\t\tref: %s\n"%ref[x])
                sys.stdout.write( "\t\ttst: %s\n"%tst[x])
            elif full :
                sys.stdout.write( "\t%s\n"%x)
                sys.stdout.write( "\t\teq : %s\n"%tst[x])
    return False

def ppmsg(ref,tst):
    msg="\nRef:\n %s \nTst: \n %s"%(pprint.pformat(ref),
                                    pprint.pformat(tst))
    return msg
