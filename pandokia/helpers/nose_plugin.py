"""
This plugin provides a --pdk option to generate a log file for the
Pandokia test management system. Additional optional arguments determine
the logfile name, project name, and test run name.

Exception and stdout handling for inclusion in log file were copied
from the pinocchio output_save plugin by Titus Brown."""

import os, time, datetime, sys, re

import nose.plugins.base # for the plugin interface
import nose.case

import unittest #for tda/tra stuff
from StringIO import StringIO as p_StringO    #for stdout capturing
from cStringIO import OutputType as c_StringO
import traceback
import platform

# pycode contains an object that writes properly formatted pdk log records
import pandokia.helpers.pycode


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


#
# This is the object that implements the plugin
#

class Pdk(nose.plugins.base.Plugin):
    """
    Provides --pdk option that causes each test to generate a PDK-
    compatible log file.
    """
    enabled = False
    pdkroot=None
    score = 500 # check this
    name = 'pdk'

    # nose calls options() very early, so we can add our own command line options
    # before the command line is parsed
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
            default=env.get("PDK_PROJECT","default"),
            help="Project name to write to PDK-compatible log file [PDK_PROJECT]")
        parser.add_option(
            "--pdktestrun",action="store",dest="pdktestrun",
            default=env.get("PDK_TESTRUN",time.asctime()),
            help="Test run name to write to PDK-compatible log file [PDK_TESTRUN]")
        parser.add_option(
            "--pdktestprefix",action="store",dest="pdktestprefix",
            default=env.get("PDK_TESTPREFIX",''),
            help="Prefix to attach to test names in PDK-compatible log file [PDK_TESTPREFIX]")
        parser.add_option(
            "--pdkcontext",action="store",dest="pdkcontext",
            default=env.get("PDK_CONTEXT","default"),
            help="Context name to write to PDK-compatible log file [PDK_CONTEXT]")

    # nose calls configure() after it has parsed all the command line options
    def configure(self, options, conf):
        self.conf = conf
        self.enabled = options.pdk_enabled

        if (options.pdklog is not None):
            self.enabled = True
            self.pdklogfile=options.pdklog
        elif 'PDK_LOG' in os.environ :
            self.enabled = True
            self.pdklogfile = os.environ['PDK_LOG']
        else:
            self.pdklogfile = os.path.join(os.path.abspath(os.path.curdir),
                              'PDK_DEFAULT.LOG')

        self.pdkproject=options.pdkproject.replace(' ','-')
        self.pdktestrun=options.pdktestrun.replace(' ','-')
        self.pdktestprefix=options.pdktestprefix
        self.pdkcontext=options.pdkcontext.replace(' ','-')

    # nose calls begin() after it called configure() but before it starts to run any tests
    def begin(self):
        """Figure out the name of the logfile, open it, &
        initialize it for this test run."""

        # no report by default.  maybe we make one, maybe we don't.
        self.rpt = None

        fname=self.pdklogfile
        
        hostname = platform.node()
        if '.' in hostname :
            hostname = hostname.split('.',1)[0]
        if 'PDK_HOST' in os.environ.keys():
            hostname = os.environ['PDK_HOST']

        try:
            # find the location of the file
            if 'PDK_FILE' in os.environ :
                if 'PDK_DIRECTORY' in os.environ :
                    d = os.environ['PDK_DIRECTORY']
                else :
                    d = os.path.abspath(os.path.curdir) 
                default_location = os.path.join( d, os.environ['PDK_FILE'] )
            else :
                # wrong, but better than nothing.  We would actually
                # like to report the file that each test is in, but
                # it appears that nose has lost that information by
                # the time it gets to us.
                default_location = os.path.abspath(os.path.curdir) 

            #
            self.rpt = pandokia.helpers.pycode.reporter(
                source_file = None,
                setdefault = True,
                    # force it to write all the values, even if
                    # pdkrun may have written a setdefault block.  If
                    # the "run" runner runs a shell script that says
                    # "pdknose modulename", we at least get some
                    # sort of location

                filename = self.pdklogfile,
                test_run = self.pdktestrun,
                project = self.pdkproject,
                host = hostname,
                context = self.pdkcontext,
                location = default_location,
                test_runner = 'nose',
                test_prefix = '',
                )

        except IOError, e:
            sys.stderr.write("Error opening log file %s: %s\n"%(fname,e.strerror))
            sys.stderr.write("***No Logging Performed***\n")
            return

    # nose calls startTest() just before it starts each test.
    def startTest(self,test):
        self.pdk_starttime = time.time()

    # nose calls stopTest() just after it finishes each test -- except when it doesn't !
    # DON'T USE THIS!
    def stopTest(self,test): 
        pass

    # nose calls addError(), addFailure(), or addSuccess() to report the status of a test
    #
    # status E and F both show a traceback, but NOT the exception because it does not
    # display properly if we report it from err[0]; in write_report(), we pick up a
    # better copy that displays nicely.

    def addError(self, test, err):
        self.write_report( test, 'E', trace= ''.join( traceback.format_tb(err[2]) ) )

    def addFailure(self, test, err):
        self.write_report( test, 'F', trace= ''.join( traceback.format_tb(err[2]) ) )

    def addSuccess(self,test):
        self.write_report( test, 'P' )

    # our function to implement the features common to all the add* functions
    def write_report(self, test, status, trace = '' ) :

        # record the end time here, because nose does not always call stopTest()
        self.pdk_endtime = time.time()

        # collect the saved stdout
        capt = get_stdout()
        if capt is None:
            capt = trace
        else:
            capt = capt + trace

        # For error status, remember the exception - we have to get it now before it
        # is lost due to another exception happening somewhere
        if ( status == 'E' ) or ( status == 'F' ) :
            try :
                # this works in python 2.7 with updated unittest and
                # recent versions of nose
                exc = repr(test.exc_info()[1])
            except AttributeError:
                try:
                    # Older versions had this marked as private method
                    exc = repr(test._exc_info()[1])
                except AttributeError :
                    # Here's a fallback.
                    exc = 'test._exc_info not available'

            # We have the stack trace in capt already, but we also
            # need the exception that caused it.  Now we have it, so
            # we can show it in the captured output.
            capt = capt + ( str(exc) + '\n' )

            # suppress the tra_Exception when status=F
            if status == 'F' :
                exc = None

        else :
            exc = None

        # actually write the record to the log file
        self.pdklog(test.test,status,log=capt, exc=exc)


    # our function to pick out the TDA and TRA dictionaries.  Depending what kind
    # of test is is, there are many places we may need to look.
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

        if isinstance(test, nose.case.MethodTestCase):
            try:
                tda = test.test.im_self.tda
            except AttributeError:
                tda = dict()

            try:
                tra = test.test.im_self.tra
            except AttributeError:
                tra = dict()

        elif isinstance(test, nose.case.FunctionTestCase):
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


    def pdklog(self,test,status,log=None, exc=None):
        """Write a record of a single test result to the PDK log file.
        This includes everything that we know how to report about this particular
        test.  (Information common to all tests was written as a SETDEFAULT
        block when we opened the log file.)
        """

        # Fix up the test name
        name = None
        if name is None:
            # Most tests have a .name attribute
            try:
                name=cleanname(test.name)
            except AttributeError:
                # But generated tests have the name one level down
                try:
                    name=cleanname(test.test.name)
                except AttributeError:
                    # If we can't find it there either,
                    # construct something reasonable from the id string
                    name=cleanname(test.id().replace(' ','_'))

            if self.pdktestprefix != '':
                # insert the prefix into the test name, but
                # do not include the / separator if it is already there.
                if not self.pdktestprefix.endswith("/") :
                    name="%s/%s"%(self.pdktestprefix,name)
                else :
                    name="%s%s" %(self.pdktestprefix,name)

        # collect the attributes from this test - separate function because
        # there are so many places you might have to look
        tda, tra = self.find_txa(test)

        if not isinstance( tda, dict ) :
            # if we don't have any, be creative:
            # Use the test type & arguments if any
            tda = { }
            tda['testtype'] = str(type(test))
            if hasattr(test,'arg'):
                count=0
                for k in test.arg:
                    count+=1
                    try:
                        tda["tda_arg%ds"%count] = str(k)
                    except:
                        pass

        # report an attribute that contains the exception that caused
        # the test to error.
        if exc is not None :
            tra['Exception'] = exc

        # write the log record - the pycode log object writes the log
        # entry and flushes the output file in case we crash later
        #
        # (Someday, it might be nice to use the start()/finish() interface
        # to the pycode reporter.  A crashed test run would leave just a
        # little more information in the pdk log.)

        if name == "nose.failure.Failure.runTest" :
            # this is an error - it does not represent an identifiable test,
            # so there is no point in reporting it.  The error will just
            # become an expected result. If somebody contrives to
            # get their test named this, I don't have a lot of sympathy.
            pass
        elif name.endswith("/nose.failure.Failure.runTest") :
            # same thing, with a file/directory name in front of it
            pass
        elif self.rpt :
            # we have a rpt object, so make the report.  (If we
            # don't, we are in something like "nosetests --pdk" but
            # without the log file specified.)
            self.rpt.report(
                test_name = name,
                status = status,
                start_time = pdktimestamp(self.pdk_starttime),
                end_time   = pdktimestamp(self.pdk_endtime),
                tda = tda,
                tra = tra,
                log = log,
                )
        else :
            # no rpt object, so no report
            pass


    # nose calls finalize() after everything is finished
    def finalize(self,result):
        if self.rpt :
            self.rpt.close()

