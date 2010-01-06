"""
This plugin provides a --pdk option to generate a log file for the
Pandokia test management system. Additional optional arguments determine
the logfile name, project name, and test run name.

Exception and stdout handling for inclusion in log file were copied
from the pinocchio output_save plugin by Titus Brown."""

import os, time, datetime, sys, re
from nose.plugins.base import Plugin #for the plugin interface
from nose.case import FunctionTestCase, MethodTestCase #for tda/tra stuff
import unittest #for tda/tra stuff
from StringIO import StringIO as p_StringO    #for stdout capturing
from cStringIO import OutputType as c_StringO
import traceback
import platform

def get_stdout():
    if isinstance(sys.stdout, c_StringO) or \
           isinstance(sys.stdout, p_StringO):
        return sys.stdout.getvalue()
    return None
                

def pdktimestamp(tt):
    """Formats the time in the format PDK wants.
    Input is a timestamp from time.time()"""
    x=datetime.datetime.fromtimestamp(tt)
    ans="%s.%03d"%(x.strftime("%Y-%m-%d %H:%M:%S"),
                   (x.microsecond/1000))
    return ans

def cleanname(name):
    """Removes any object id strings from the test name. These
    can occur in the case of a generated test."""
    pat=re.compile(".at.0x\w*>")
    newname=re.sub(pat,'>',name)
    return newname



class Pdk(Plugin):
    """
    Provides --pdk option that causes each test to generate a PDK-
    compatible log file.
    """
    enabled = False
    pdkroot=None
    score = 500 # check this
    name = 'pdk'
    
    def options(self, parser, env=os.environ):
        parser.add_option(
            "--pdk", action="store_true", dest="pdk_enabled",
            default=env.get('PDK', False),
            help="Generate PDK-compatible log file")
        parser.add_option(
            "--pdklog",action="store",dest="pdklog",
            default=env.get('PDK_LOG',None),
            help="Path for PDK-compatible log file [PDK_LOG]")
        parser.add_option(
            "--pdkproject",action="store",dest="pdkproject",
            default=env.get("PDK_PROJECT","Unspecified"),
            help="Project name to write to PDK-compatible log file [PDK_PROJECT]")
        parser.add_option(
            "--pdktestrun",action="store",dest="pdktestrun",
            default=env.get("PDK_TESTRUN",time.asctime()),
            help="Test run name to write to PDK-compatible log file [PDK_TESTRUN]")
        parser.add_option(
            "--pdktestprefix",action="store",dest="pdktestprefix",
            default=env.get("PDK_TESTPREFIX",''),
            help="Prefix to attach to test names in PDK-compatible log file [PDK_TESTPREFIX]")
        
    def configure(self, options, conf):
        self.conf = conf
        self.enabled = options.pdk_enabled
        
        if (options.pdklog is not None):
            self.pdklogfile=options.pdklog
        else:
            self.pdklogfile = os.path.join(os.path.abspath(os.path.curdir),
                              'PDK_DEFAULT.LOG')

        self.pdkproject=options.pdkproject.replace(' ','-')
        self.pdktestrun=options.pdktestrun.replace(' ','-')
        self.pdktestprefix=options.pdktestprefix

        
    def begin(self):
        """Figure out the name of the logfile, open it, &
        initialize it for this test run."""
        
        fname=self.pdklogfile
        hostname,junk=platform.node().split('.',1)
        
        try:
            self.f_pdk=open(self.pdklogfile,'a')

            # If PDK_FILE is in the environment, assume that we are
            # being run by the pandokia meta-runner.  The meta-runner
            # will have entered much of the information into the log
            # file for us.
            #
            # Otherwise, assume we are stand-alone, so we need to write 
            # the complete pdk record for the tests. 
            if not 'PDK_FILE' in os.environ: 
                # \n\nSTART\n because this will cause the file format to
                # be readable even if the last guy crashed while writing
                # a record.
                self.f_pdk.write("\n\nSTART\n")
                self.f_pdk.write("test_run=%s\n"%self.pdktestrun)
                self.f_pdk.write("host=%s\n"%hostname)
                self.f_pdk.write("project=%s\n"%self.pdkproject)
                # bug: location should be file, not directory
                self.f_pdk.write("location=%s\n"%os.path.abspath(os.path.curdir))
                self.f_pdk.write("test_runner=nose\n")
                self.f_pdk.write("SETDEFAULT\n")

        except IOError, e:
            sys.stderr.write("Error opening log file %s: %s\n"%(fname,e.strerror))
            sys.stderr.write("***No Logging Performed***\n")
            return
        
    def finalize(self,result):
        self.f_pdk.close()
        
    def addError(self, test, err):
        exception_text = traceback.format_exception(*err)
        exception_text = "".join(exception_text)
        
        capt = get_stdout()
        if capt is None:
            capt = exception_text
        else:
            capt += exception_text

        try:
            self.pdklog(test.test,'E',log=capt)
        except AttributeError:
            pass #Object is a ContextSuite or something else that has no test

    def addFailure(self, test, err):
        exception_text = traceback.format_exception(*err)
        exception_text = "".join(exception_text)
        
        capt = get_stdout()
        if capt is None:
            capt = exception_text
        else:
            capt += exception_text

        try:
            self.pdklog(test.test,'F',log=capt)
        except AttributeError:
            pass #Object is a context suite or something else that has no test

    def addSuccess(self,test):
        capt=get_stdout()
        try:
            self.pdklog(test.test,'P',log=capt)
        except AttributeError:
            pass #Object is a context suite or something else that has no test

    def startTest(self,test):
        self.pdk_starttime = pdktimestamp(time.time())

    def find_txa(self, test):
        """Find the TDA and TRA dictionaries, which will be in different
        places depending on what kind of a test this is.
        """

############
# Debugging print statements
#        print "~~~~ Entering find_txa"
#        print "test is ", type(test)
#        try:
#            print "test.test is ", type(test.test)
#            print "test addr is ",test.address()
#        except AttributeError:
#            print "This is a UnitTest case, it has no .test attr"
############

        if isinstance(test, MethodTestCase):
            try:
                tda = test.test.im_self.tda
            except AttributeError:
                tda = dict()

            try:
                tra = test.test.im_self.tra
            except AttributeError:
                tra = dict()
                
        elif isinstance(test, FunctionTestCase):
            try:
                tda = test.test.func_globals['tda']
            except KeyError:
                tda = dict()
            try:
                tra = test.test.func_globals['tra']
            except KeyError:
                tra = dict()
                
        elif isinstance(test, unittest.TestCase):
            try:
                tda = test.tda
            except AttributeError:
                tda = dict()
            try:
                tra = test.tra
            except AttributeError:
                tra = dict()
                
        else:
            tda = dict()
            tra = {'warning':'Unknown test type: tda/tra not found'}
            raise TypeError("Unknown test type, %s"%type(test.test))
            
#        print "~~~~~~~"
        return tda, tra            
   

    def pdklog(self,test,status,name=None,log=None):
        """Creates a log file containing the test name, status,and timestamp,
        as well as any attributes in the tda and tra dictionaries if present.
        Does not yet support fancy separating of multi-line items."""


        #Catch the time.
        self.pdk_endtime=pdktimestamp(time.time())
        
        if status == 'E':
            #Stash the test error info here before any more errors
            #can be generated.
            testerr=test._exc_info()
            errval=repr(testerr[1])

        #Fix up the name
        if name is None:
            #Most tests have a .name attribute
            try:
                name=cleanname(test.name)
            except AttributeError:
                #But generated tests have the name one level down
                try:
                    name=cleanname(test.test.name)
                except AttributeError:
                    #If we can't find it there either,
                    #construct something reasonable from the id string
                    name=cleanname(test.id().replace(' ','_'))

            if self.pdktestprefix != '':
                # insert the prefix into the test name, but
                # do not include the / separator if it is already there.
                if not self.pdktestprefix.endswith("/") :
                    name="%s/%s"%(self.pdktestprefix,name)
                else :
                    name="%s%s" %(self.pdktestprefix,name)

        print "~~~~~ test name is ",name
        
        #Write the standard info
        self.f_pdk.write("test_name=%s\n"%name)
        self.f_pdk.write("status=%s\n"%status)
        self.f_pdk.write("start_time=%s\n"%self.pdk_starttime)
        self.f_pdk.write("end_time=%s\n"%self.pdk_endtime)


        tda, tra = self.find_txa(test)
        
        #Write the TDAs
        try:
            for k in tda:
                self.f_pdk.write("tda_%s=%s\n"%(str(k),str(tda[k])))
        #if we don't have any, be creative:
        #Use the test type & arguments if any
        except TypeError:
            self.f_pdk.write("tda_testtype=%s\n"%str(type(test)))
            if hasattr(test,'arg'):
                count=0
                for k in test.arg:
                    count+=1
                    try:
                        self.f_pdk.write("tda_arg%d=%s\n"%(count,str(k)))
                    except:
                        pass
            else:
                pass


        #Write the TRAs
        try:
            for k in tra:
                self.f_pdk.write("tra_%s=%s\n"%(str(k),str(tra[k])))
        except (AttributeError, TypeError):
            pass

        #If this is an error, write the exception
        if status == 'E':
            self.f_pdk.write("tra_Exception=%s\n"%(errval))

        #Write the log (typically captured stdout/stderr) if present
        if log is not None and (log.strip() != ''):
            self.f_pdk.write("log:\n")
            loglines=log.split('\n')
            for line in loglines:
                self.f_pdk.write(".%s\n"%line)
            self.f_pdk.write("\n")

        #Mark the end of the record
        self.f_pdk.write("END\n")


