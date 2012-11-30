import os
import pandokia.lib
import datetime
import traceback

###
### reporter object
###
#
# create one of these objects to append to a PDK_LOG file, then use it to
# append properly formatted log records.
#
# x = reporter( __file__ )
#
# x.start( test_name, tda_dict )
# ...run test...
# x.finish( status, tra_dict, log_string )
#
# x.report( ...everything about the test... )
#
#

class reporter(object) :

    # default to pandokia log format
    report_view = False
    report_view_sep = ( '-' * 79 ) 
    report_view_verbose = False

    def __init__( self, source_file, setdefault=False, filename=None, test_run=None, project=None, host=None, context=None, location=None, test_runner=None, test_prefix=None ) :

        '''pandokia log file object

        source_file 
            The base name of the source file is added to the test prefix.
            May be None if you don't want that.

        setdefault = False
            If true, write a SETDEFAULT block; if pdkrun called you,
            you don't need this.  The default values come from the
            environment or gethostname().

        filename = None
            Name of the file to write the records to; if None, use
            PDK_LOG environment variable.

        test_run = None
        project = None
        host = None
        context = None
            Characteristics of this test run; if None, use related
            pandokia environment variable; if no environment variable,
            use "default"

        location = None
            Characteristics of this test run; if None, figure out
            the location of the tests from the current directory
            and PDK_FILE.  If you can't, don't report a location.

        test_runner = None
            if not None, report this string as the test runner used.

        test_prefix = None
            put this prefix on each test name; if None, use PDK_TESTPREFIX
            environment.  If not in environment, there is no prefix.

'''

        # in all cases, we need to open the output file
        if filename is not None :
            self.filename = filename
            self.report_file=open(filename,"a")
        else :
            if 'PDK_LOG' in os.environ :
                filename = os.environ['PDK_LOG']
                self.filename = filename
                self.report_file=open(filename,"a")
            else :
                self.report_file=sys.stdout
                self.report_view = True

        # select the prefix to insert in front of test names.
        if test_prefix is None :
            if 'PDK_TESTPREFIX' in os.environ :
                self.test_prefix = os.environ['PDK_TESTPREFIX']
            else :
                self.test_prefix = ''
        else :
            self.test_prefix = test_prefix

        # if we have the name of the source file where the tests are,
        # append it to the prefix.  Otherwise, assume the user has given
        # us a complete prefix to use.
        if source_file is not None :
            if source_file.endswith(".py") :
                source_file = source_file[:-3]
            elif source_file.endswith(".pyc") or source_file.endswith(".pyo") :
                source_file = source_file[:-4]
            self.test_prefix = self.test_prefix + source_file

        if setdefault and not self.report_view :
            # If you are running in the context of pdkrun, all of these
            # values will already be set as defaults in the pdk log file.
            #
            # This option exists so that you can use this module outside
            # the context of pdkrun.

            # if we have setdefault set, we are overriding any defaults
            # that may already be in the file.
            self.report_file.write("\n\nSTART\n")

            # test_run - required
            #   what the user provided, else PDK_TESTRUN, else 'default'
            if test_run is None :
                if 'PDK_TESTRUN' in os.environ:
                    test_run = os.environ['PDK_TESTRUN']
                else :
                    test_run = 'default'
            self.write_field('test_run',        test_run )

            # project - required
            #   what the user provided, else PDK_PROJECT, else 'default'
            if project is None :
                if 'PDK_PROJECT' in os.environ :
                    project = os.environ['PDK_PROJECT']
                else :
                    project = 'default'
            self.write_field('project',         project )

            # host - required
            #   what the user provided, else the real host name without the domain
            if host is None :
                if 'PDK_HOST' in os.environ.keys():
                    host = os.environ['PDK_HOST']
                else:
                    host = pandokia.lib.gethostname()
            self.write_field('host',            host )

            # location - optional
            #   what the user provided, else current directory + PDK_FILE
            if location is None :
                if 'PDK_FILE' in os.environ :
                    location = os.getcwd()+"/"+os.environ['PDK_FILE']
                    self.write_field('location',        location )
                else :
                    pass    # no location reported in this case
            else :
                    self.write_field('location',        location )

            # test_runner - optional
            #   what the user provided, else nothing
            if test_runner is not None :
                self.write_field('test_runner',     test_runner )

            # context - currently optional
            #   what the user provided, else PDK_CONTEXT, else nothing
            if context is None :
                if 'PDK_CONTEXT' in os.environ :
                    context = os.environ['PDK_CONTEXT']
            if context is not None :
                self.write_field('context',         context )

            # this saves the default values
            self.report_file.write("SETDEFAULT\n")

        # end if setdefault

        # count how many of each status showed up
        self.status_count = { }

    # end def __init__

    def report( self, test_name, status, start_time=None, end_time=None, tra={ }, tda={ }, log=None, location=None) :

        self.status_count[status] = self.status_count.get(status,0) + 1

        if self.report_view :
            if status == 'P' :
                if not self.report_view_verbose :
                    return
            self.report_file.write(self.report_view_sep)
            self.report_file.write('\n')

        if test_name is None :
            test_name = self.test_prefix
        else :
            if self.test_prefix != '' :
                if self.test_prefix.endswith('.') or self.test_prefix.endswith('/') :
                    test_name = self.test_prefix + test_name
                else :
                    test_name = self.test_prefix + '.' + test_name

        if '\n' in test_name :
            test_name = test_name.replace('\n','-')

        self.write_field('test_name',   test_name)

        self.write_field('status',      status)

        if not self.report_view :
            if location is not None :
                self.write_field('location',  str(location))

            if start_time is not None :
                self.write_field('start_time',  str(start_time))

            if end_time is not None :
                self.write_field('end_time',    str(end_time))

            for name in tda :
                self.write_field('tda_'+name, tda[name])

            for name in tra :
                self.write_field('tra_'+name, tra[name])

            if log is not None :
                self.write_field('log',         log)
            self.report_file.write('END\n')
        else :
            self.report_file.write(log)



        # You would think we don't need this, but in practice sometimes
        # python C extensions will core dump the whole python interpreter.
        # In that case, this gets as much of our output as possible.
        self.report_file.flush()


    # see ticket #51
    def start( self, test_name, tda={ } ) :
        self.test_name = test_name
        self.tda = tda
        self.start_time = datetime.datetime.now()

    def finish( self, status, tra={ }, log=None ) :
        self.report( test_name=self.test_name, status=status, start_time=self.start_time, end_time=datetime.datetime.now(), tda=self.tda, tra=tra, log=log)

    def write_field(self, name, value) :
        value=str(value)
        if '\n' in value :
            if value.endswith('\n') :
                value=value[:-1]
            self.report_file.write('%s:\n'%name)
            for x in value.split('\n') :
                self.report_file.write('.%s\n'%x)
            self.report_file.write('\n')
        else :
            self.report_file.write('%s=%s\n'%(name,value))

    def close(self):
        self.report_file.close()
        self.report_file = None

###
### capture stdout/stderr for later
###

# intentionally not using cStringIO
import StringIO
import sys

save_stdout= [ ] 
save_stderr= [ ]
save_tagname = [ ]

def snarf_stdout( tagname=None ) :
    global save_stdout, save_stderr
    save_stdout.append( sys.stdout )
    save_stderr.append( sys.stderr )
    save_tagname.append( tagname )

    sys.stdout = sys.stderr = StringIO.StringIO()

def end_snarf_stdout( tagname=None ) :
    s = sys.stdout.getvalue()

    # we only opened one StringIO so we only need to close it once
    sys.stdout.close()

    sys.stdout = save_stdout.pop()
    sys.stderr = save_stderr.pop()
    old_tagname = save_tagname.pop()
    if old_tagname != tagname :
        f=open("/dev/tty","w")
        f.write("Mismatched snarf_stdout/end_snarf_stdout - expected %s got %s"%(tagname,old_tagname))
        f.close()
        raise ValueError("Mismatched snarf_stdout/end_snarf_stdout")

    return s

def peek_snarfed_stdout() :
    'returns current text of snarfed stdout, non-destructively'
    if isinstance(sys.stdout, StringIO.StringIO ) :
        return sys.stdout.getvalue()
    else :
        return None


###
### context managers to make tests in pycode() functions
###

# I copied the idea of using the "with" statement to track the
# test hierarchy and collect the test status from Sclara by
# John MacKenzie (john at nineteeneightd dot com).  Sclara
# is at http://github.com/198d/sclara
#
# At the time Sclara was announced, it did not have any documentation,
# so I'm not entierly sure what it is for, but I think the principal
# difference is that I intend this for dynamically generated tests.
# That is, something like:
#    for x in list :
#       with test( name=str(x) ) :
#           assert f(x)
#
# The test names nest into a hierarchy if you start a second test
# within a test that is already running:
#   with test( name="foo" ) :
#       assert a
#       with test(name="bar" ) :
#           assert b
#       assert c
# creates two tests named "foo" and "foo.bar" (assuming you survive
# the assert a).
#

# This variable is here so we don't have to pass our report object
# all around.  Typically, there is only one report object that we
# are using, so we let the user just stash it.  (If they screw it
# up, that's their problem.)
cached_rpt = None


# A generic class, for reasons explained below.
class _pycode_with(object) :
    """
    with test( name, rpt, tda= {}, tra = {} ) as t :
        t.tra['name'] = some_value
        t.tda['name'] = some_value
        print "stuff"
        assert some_expression
        raise some_error()

    name is the name of the test.

    rpt is the pycode object to report to

    tda and tra are optional initial values of the tda/tra
    dicts.  A COPY of each will be attached to the context
    manager object.

    
    """


    #
    def __init__(self, *l, **kw) :
        raise Exception('Do not instantiate me directly.  Use pycode.test or pycode.setup')

    # This is used by the init of the subclasses.
    def fmt(self, name, rpt, tda, tra, location ) :

        # importing runner_minipyt here to break an import loop.
        # runner_minipyt imports pycode, so we only do the import here when
        # we really need it.  This is after the pycode import is finished.
        global runner_minipyt
        try :
            runner_minipyt
        except NameError :
            import runner_minipyt as m
            runner_minipyt = m

        # name is just our base name.  
        self.name = name

        # Remember the report object we were created with.
        if rpt is None :
            global cached_rpt
            if not cached_rpt :
                # this happens if we are running without a test runner
                cached_rpt = reporter( None ) 
            self.rpt = cached_rpt
        else :
            self.rpt = rpt

        # tda/tra are copies so we don't smash the parent test's
        # attributes
        self.tda = tda.copy()
        self.tra = tra.copy()

        # This object is not reusable.  It is initialized with
        # test-specific data, so we flag it if somebody tries to use
        # it twice.
        self.expired = False

        # remember in case the user gave a location for the test
        self.location = location

        # if they did not give us a location, figure it out.  We
        # are in a context manager that was invoked from a with-statement.
        # If we do not know where we are, walk up the stack frame until
        # we find the location where the test was invoked.  That is
        # either the first frame that is not in this source file, or
        # it is the function package_test() in this file.
        if location is None :
            import inspect
            l = inspect.stack()
            this_file = l[0][1]
            for x in l :
                if x[1] != this_file or x[3] == 'package_test' :
                    self.location = x[1]
                    break
            if '__init__' in self.location :
                open("/dev/tty","w").write(str(l))

    # 
    def __enter__(self) :
        # do not allow the user to reuse this object; they have to
        # make a new one with a new test name.
        if self.expired :
            raise Exception("Object not reusable")
        self.expired = True

        # Constructing our name.  It will be stacked on the minipyt
        # name stack to obtain a more full test name -- even
        # if we are not running in minipyt, that is where we store
        # the name.  In turn, that name will be appended to
        # PDK_PREFIX.
        runner_minipyt.currently_running_test_name.append(self.name)

        # This takes a little explaining:  We might be running in
        # the context of minipyt.  (In fact, we probably are, but I
        # don't mean to exclude other possibilities.)
        #
        # If we are, the "with" statement might be inside a minipyt
        # test function or test method.  If that happens, we want to
        # stack the name tree generated by the "with" statements on
        # the name tree generated by minipyt.
        #
        # minipyt sometimes has None values in it's stack, so we
        # have to exclude them before we assemble the test name.
        #
        # If we are not running in the context of minipyt, then
        # there are no non-None values in the minipyt name stack.
        self.full_name = '.'.join( 
            [ x for x in runner_minipyt.currently_running_test_name if x ] 
        )

        # When we started.
        self.start_time = datetime.datetime.now()

        # capture stdout
        snarf_stdout()

        # __enter__ returns the value to stuff into the "as xxx"
        # of the with statement.  We want the user to have access to
        # this object.
        return self

    #
    def __exit__(self, extype, exvalue, extraceback) :

        # take our name off the stack
        if runner_minipyt.currently_running_test_name.pop() != self.name :
            raise Exception("Internal inconsistency in pycode context manager - name stack is messed up")

        # If there is no exception, the test passes
        if extype is None :
            status = self.pass_status

        # If there is an AssertionError, the test fails.
        # failing tests do not get tra_exception
        elif isinstance( exvalue, AssertionError ) :
            status = 'F'

        # If there is another Exception, we have an error
        else :
            status = 'E'
            if not 'exception' in self.tra :
                self.tra['exception'] = str(exvalue)
                self.tra['exception_type'] = str(extype)

        # If there was a fail/error, show the exception and the
        # stack trace in the log
        if status != 'P' :
            print str(exvalue)
            traceback.print_tb( extraceback )

        # capture the log
        log = end_snarf_stdout()

        # stupid dots...
        if runner_minipyt.dots_mode :
            runner_minipyt.show_dot( status, self.full_name, log)

        # write the report.
        self.rpt.report( test_name=self.full_name, 
                status=status, 
                start_time=self.start_time,
                end_time=datetime.datetime.now(),
                tra=self.tra,
                tda=self.tda,
                log=log,
                location=self.location )

        # Return true means to ignore the exception, instead of
        # re-raising it outside the with statement.
        return True

## with test(  name='x' )
## with setup( name='x' )
##      Both do the same thing now, but someday the setup() result
##      will distinguish itself from a test() result.  This is
##      because Vicki finds it misleading to say that a setup passed
##      ("because it is not a test").

class test(_pycode_with) :
    pass_status = 'P'

    def __init__(self, name, rpt=None, tda = { }, tra = { }, location=None ) :
        self.fmt( name, rpt, tda, tra, location )

class setup(_pycode_with) :
    # Someday, change this to 'R' so vicki can see setup different
    # from test in the report
    pass_status = 'P'

    def __init__(self, name, rpt=None, tda = { }, tra = { }, location=None ) :
        self.fmt( name, rpt, tda, tra, location )
 
#####
##### a tool for running with-type tests from the packagename.test() function
#####

def package_test( parent, test_package, test_modules, verbose=False ) :

    import pandokia.helpers.runner_minipyt as runner_minipyt
    runner_minipyt.dots_mode = ''

    global cached_rpt
    cached_rpt = reporter( None ) 
    cached_rpt.report_view_verbose = verbose

    for x in test_modules :
        x = parent + '.' +  test_package + '.' + x
        with test(x) as t :
            exec "import %s" % x
    passed = cached_rpt.status_count.get('P',0)
    failed = cached_rpt.status_count.get('F',0)
    error  = cached_rpt.status_count.get('E',0)

    print cached_rpt.report_view_sep
    print "Pass: %d  Fail: %d  Error: %d"%( passed, failed, error )

    if ( failed == 0 ) and ( error == 0 ) :
        return 0
    else :
        return 1
