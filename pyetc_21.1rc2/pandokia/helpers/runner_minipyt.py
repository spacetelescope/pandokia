#! python
#

import sys
import inspect
import traceback
import imp
import os.path
import time
import gc
import copy

# In python 2.6 and later, this prevents writing the .pyc files on import.
# I normally don't want the .pyc files cluttering up the test directories.
# Before python 2.6, this doesn't do anything, but nothing breaks either.
sys.dont_write_bytecode = True

# local debug flag
debug = False

# stack of currently running test names (because they nest)
# pandokia.helpers.runner_minipyt.currently_running_test_name[-1] is the
# test that is currently running.  minipyt does not run tests in multiple
# threads, so use of this global is safe.

currently_running_test_name = [ None ]

# scalar for the current file name
currently_running_file_name = None

#
if debug :
    debug_fd = open("/dev/tty","w")
    debug_fd.write("HELLO - minipyt debug!\n")

# just in case somebody needs to see a lot of dots when they run their tests. :)
default_dots_mode = ''
default_dots_mode = 'N'

if 'PDK_DOTS' in os.environ :
    default_dots_mode = os.environ['PDK_DOTS']

dots_mode = default_dots_mode

# where to send dots: sys.stdout will be captured into the log file;
# I can't think of any other useful place to send them, but we have a
# special var for the file just in case.
dots_file = sys.stdout

# the pycode helper contains an object that writes pandokia report files
import pandokia.helpers.pycode as pycode

# there has to be a better way than this to get the type
# of a function.
def function ( ) :
    pass
function = type(function)

####
#### utility functions
####

#
# Here is a sort function to sort the list of tests into the order that
# they are defined in the file, at least for things that are statically
# defined.
# 
# the list is [ (name, ob), ... ]
#
# I got the method for doing this from
# http://lists.idyll.org/pipermail/testing-in-python/2010-January/002596.html
#
# b.t.w.  This is a FAIL if you use certain decorators on the function.  It
# use the line number of the decorator, instead of the line number of your function.

def _sort_fn(a) :
    (name,ob) = a
    code = getattr( ob, 'func_code', None )
    line = getattr( code, 'co_firstlineno', 0 )
    if debug :
        debug_fd.write("sort: %s %s\n"%(str(a), line))
    return line

# sort the tests into the order we want to do them
def sort_test_list(l, test_order) :
    if test_order == 'alpha' :
        l.sort()
    elif test_order == 'line' :
        l.sort(key=_sort_fn)
    else :
        l.sort()
    if debug:
        debug_fd.write("sorted test list: %s\n" % str([ name for (name,value) in l]))

def show_dot(status, name, log) :
    if status == 'P' :
        dots_file.write('.')
    else :
        if dots_mode == 'N' :
            dots_file.write(' %s: %s\n'%(name,status) )
        elif dots_mode == 'S' :
            dots_file.write(status)
        elif dots_mode == 'O' :
            dots_file.write('-'*70)
            dots_file.write('\n%s: %s\n'%(name,status) )
            dots_file.write(log)
            dots_file.write('\n')
    dots_file.flush()

# Generate the report record for a single test.
def gen_report( rpt, name, status, start_time, end_time, tda, tra, log ) :

    # write the report (yes, tra first)
    rpt.report( name, status, start_time, end_time, tra, tda, log )

    # we only generate the report at the end of running the test
    popped = currently_running_test_name.pop()
    # print "POPPED",popped
    if name != popped :
        raise Exception('Ending the wrong test - internal error %s != %s'%(name,popped))

    # do they need rows of dots on their screen?
    if dots_mode :
        if name is None :
            name = rpt.test_prefix
        show_dot(status, name, log)

####
#### actually run a test function
####

def run_test_function(rpt, mod, name, ob) :

    currently_running_test_name.append(name)
    # print "PUSHED",name

    if debug :
        debug_fd.write("run_test_function: %s\n"% ( name ) )

    # blank out the tda/tra dictionaries for each test.
    # poke directly into the module to do it.
    mod.tda = { }
    mod.tra = { }

    # start gathering up the stdout/stderr for this test
    pycode.snarf_stdout()

    # run the test
    start_time = time.time()

    #
    disable = getattr(ob, '__disable__', False)

    if not disable :
        try :
            setup = getattr(ob, 'setup', None)
            if setup is not None :
                setup()
            ob()
            status = 'P'
        except AssertionError :
            status = 'F'
            traceback.print_exc()
        except :
            status = 'E'
            traceback.print_exc()

        teardown = getattr(ob, 'teardown', None)
        if teardown is not None :
            try :
                teardown()
            except :
                print "Exception in teardown()"
                status = 'E'
                traceback.print_exc()
    else :
        # is disabled
        status = 'D'

    end_time = time.time()

    # collect the gathered stdout/stderr
    log = pycode.end_snarf_stdout()

    # write a report the the pandokia log file
    gen_report( rpt, name, status, start_time, end_time, mod.tda, mod.tra, log )
    

####
####
####


def get_exception_str() :
    type, value, tb = sys.exc_info()

    # where was the exception ?
    lineno = tb.tb_lineno
    co = tb.tb_frame.f_code
    filename = co.co_filename
    name = co.co_name

    #
    del tb

    # the line number above is incorrect sometimes - don't return it until we get it consistently right
    return repr(value)


    # we might include more information here
    return '%s in "%s", line %d, in %s' % (repr(value),filename,lineno,name)


####
#### actually run a test class
####


def locate_test_methods( ob, test_order ) :
    l = [ ]

    # look through the class for methods that are interesting to us.

    for f_name, f_ob in inspect.getmembers(ob, inspect.ismethod) :

        # if the method has __test__, that value is a flag
        # about whether it is a test or not.  Note there are
        # ** three ** conditions here: true, false, and no attribute
        try :
            n = getattr(f_ob,'__test__')
            if debug :
                debug_fd.write('run_test_class: __test__ %s\n'%n)
            if n :
                rname = getattr(f_ob,'run_test_class: __test_name__', f_name)
                if debug :
                    debug_fd.write('run_test_class: actual name used %s\n'%rname)
            l.append( (rname, f_ob) )
            continue
        except AttributeError :
            pass

        # if the method name looks like a test, it is a test
        if f_name.startswith('test') or f_name.endswith('test') :
            l.append( (f_name, f_ob) )

    sort_test_list(l, test_order)

    return l


#### TEST METHOD

def run_test_method( name, class_ob, f_name, f_ob, rpt ) :

    full_test_name = name + '.' + f_name

    currently_running_test_name.append(full_test_name)
    # print "PUSHED X",full_test_name

    pycode.snarf_stdout()

    fn_start_time = time.time()

    # clear the test attributes
    class_ob.tda = { }
    class_ob.tra = { }

    exception_str = None

    if getattr( f_ob, '__disable__', False ) :
        fn_status = 'D'

    else :
        # call the test method
        try :

            # call setUp if it is there
            setup = getattr( class_ob, 'setUp', None)
            if setup :
                setup()

            # call the test method
            f_ob(class_ob)

            # pass if we managed to return
            fn_status = 'P'

        except AssertionError :
            fn_status = 'F'
            traceback.print_exc()

        except :
            exception_str = get_exception_str()
            fn_status = 'E'
            traceback.print_exc()

        try :
            # call tearDown if it is there
            teardown = getattr( class_ob, 'tearDown', None)
            if teardown :
                teardown()

        except :
            print 'exception in teardown'
            exception_str = get_exception_str()
            fn_status = 'E'
            traceback.print_exc()

    fn_end_time = time.time()

    fn_log = pycode.end_snarf_stdout()

    tda = getattr(class_ob,'class_tda',{}).copy()
    tda.update( getattr(class_ob,'tda',{}) )

    tra = getattr(class_ob,'class_tra',{}).copy()
    tra.update( getattr(class_ob,'tra',{}) )

    if exception_str is not None :
        tra['exception'] = exception_str

    gen_report( rpt, full_test_name, fn_status, fn_start_time, fn_end_time, tda, tra, fn_log )


#### run the tests in a single instance of a test object

def run_test_class_single( rpt, mod, name, ob, test_order ) :

    currently_running_test_name.append(name)
    # print "PUSHED",name

    pycode.snarf_stdout()
    class_start_time = time.time()

    class_status = 'P'
    exception_str = None

    # find the test methods on the class object
    l = locate_test_methods( ob, test_order )

    # instantiate the object; bail out early if we can't
    try :
        class_ob = ob()
    except :
        exception_str = get_exception_str()
        traceback.print_exc()
        # really nothing more we can do...
        gen_report( rpt, name, 'E', class_start_time, time.time(), { }, { 'exception' : exception_str }, pycode.end_snarf_stdout() )
        return

    # make sure the class attribute dictionaries exist
    class_ob.class_tda = getattr(class_ob, 'class_tda', {} )
    class_ob.class_tra = getattr(class_ob, 'class_tra', {} )

    try :
        # class setup is run once after the object init
        class_setup = getattr(class_ob, 'classSetUp', None )
        if class_setup :
            class_setup()

        # for each test method on the object
        for f_name, f_ob in l :
            if debug :
                debug_fd.write('run_test_class: test method: %s %s\n'%(f_name,str(f_ob)))

            # run the test method
            run_test_method( name, class_ob, f_name, f_ob, rpt ) 

    # exceptions that came out of handling the class, but not one of the test methods
    except AssertionError :
        class_status = 'F'
        traceback.print_exc()

    except :
        exception_str = get_exception_str()
        class_status = 'E'
        traceback.print_exc()

    try :
        # optional teardown
        class_teardown = getattr(class_ob, 'classTearDown', None )
        if class_teardown :
            class_teardown()
    except :
        exception_str = get_exception_str()
        class_status = 'E'
        traceback.print_exc()

    # this is the end of everything relating to the class.
    class_end_time = time.time()
    class_log = pycode.end_snarf_stdout() 

    tda = getattr(class_ob,'class_tda',{})

    tra = getattr(class_ob,'class_tra',{})

    if exception_str is not None :
        tra['exception'] = exception_str

    gen_report( rpt, name, class_status, class_start_time, class_end_time, tda, tra, class_log )

#### run tests, fresh object for each test

def run_test_class_multiple( rpt, mod, name, ob, test_order ) :

    currently_running_test_name.append(name)
    # print "PUSHED",name

    pycode.snarf_stdout()
    class_start_time = time.time()

    print "MULTIPLE"
    class_status = 'P'
    exception_str = None

    # find the test methods on the class object
    l = locate_test_methods( ob, test_order )

    # for each test method on the object
    for f_name, f_ob in l :

        if debug :
            debug_fd.write('run_test_class: test method: %s %s\n'%(f_name,str(f_ob)))

        try :

            # bug: stdout and exceptions go to the class, not the test 
            class_ob = ob()

            # we have them so it is easy to convert tests back/forth
            class_ob.class_tda = { }
            class_ob.class_tra = { }

            # class setup is run once after the object init
            class_setup = getattr(class_ob, 'classSetUp', None )
            if class_setup :
                class_setup()

            # run the test method
            run_test_method( name, class_ob, f_name, f_ob, rpt ) 

        # exceptions that came out of handling the class, but not one of the test methods
        except AssertionError :
            class_status = 'F'
            traceback.print_exc()

        except :
            exception_str = get_exception_str()
            class_status = 'E'
            traceback.print_exc()

        try :
            # bug: stdout and exceptions go to the class, not the test 

            # optional teardown
            class_teardown = getattr(class_ob, 'classTearDown', None )
            if class_teardown :
                class_teardown()
        except :
            exception_str = get_exception_str()
            class_status = 'E'
            traceback.print_exc()

    # this is the end of everything relating to the class.
    class_end_time = time.time()
    class_log = pycode.end_snarf_stdout() 

    # it really doesn't make sense to say there is an attribute for
    # the class, when we have made many class objects, each with separate
    # attributes
    tda = { }
    tra = { }

    if exception_str is not None :
        tra['exception'] = exception_str

    gen_report( rpt, name, class_status, class_start_time, class_end_time, tda, tra, class_log )


# There is a test name that corresponds to the whole class.  This gathers any
# result and/or error that comes from the class, but not from an individual
# test method.

def run_test_class( rpt, mod, name, ob, test_order ) :

    if getattr(ob, '__disable__', False ) :
        # have to push the name so we can pop it in gen_report()
        currently_running_test_name.append(name)
        # print "PUSHED",name
        gen_report( rpt, name, 'D', None, None, { }, { }, None )
        return  # bug: find the test names and report status=D

    new_object_every_time = not getattr(ob,'minipyt_shared',0)

    # the difference between making a new object for every test and
    # using the same object over and over is just enough to make it worth
    # separating into two functions.
    if new_object_every_time :
        run_test_class_multiple( rpt, mod, name, ob, test_order )
    else :
        run_test_class_single( rpt, mod, name, ob, test_order )


####
#### run a whole file of tests
####

# There is a test name that corresponds to the file.  This gathers any
# result and/or error that comes from the file, but not from an individual
# test.
#
# filename is the name of a file of python code that contains the tests
#
# test_name is the name to use for all tests in this file; default is
#   derived from the file name of the python code
#
# test_args is additional information passed in for the test code to use
#   as parameters
#

def process_file( filename, test_name = None, test_args = None ) :

    global currently_running_file_name
    currently_running_file_name = filename

    if debug :
        debug_fd.write("begin process_file\n")
        debug_fd.write("file: %s\n" % filename)
        debug_fd.write("args: %s\n" % test_args)

    global dots_mode

    dots_mode = default_dots_mode

    if dots_mode :
        dots_file.write('File: %s\n'%filename)
        dots_file.flush()

    # the module name is the basename of the file, without the extension
    module_name = os.path.basename(filename)
    module_name = os.path.splitext(module_name)[0]

    # pandokia log entry object - writes the pandokia reports
    if debug :
        debug_fd.write( "test_args %s\n"%test_args)

    # we have no name for the top level of the file - bummer
    currently_running_test_name.append(None)
    # print "PUSHED",None

    if test_name is not None :
        rpt = pycode.reporter( test_name )
    else :
        rpt = pycode.reporter( filename )

    # the pycode context managers can make use of this.
    pycode.cached_rpt = rpt

    # gather up the stdout from processing the whole file.    individual
    # tests will suck up their own stdout, so it will not end up in
    # this log.
    pycode.snarf_stdout()

    #
    file_start_time = time.time()
    file_status = 'P'

    # make sure we can import from the directory where the file is
    sys_path_save = copy.copy(sys.path)
    sys.path.insert(0,os.path.dirname(filename))

    exception_str = None

    try :

        if debug :
            debug_fd.write("process_file: about to import %s %s\n"%(module_name,filename))

        # import the module
        module = imp.load_source( module_name, filename )

        if debug :
            debug_fd.write("process_file: import succeeds\n")

        if test_args :
            if debug :
                debug_fd.write("entering minipyt_external_args into module\n")
            module.minipyt_external_args = test_args

        try :
            dots_mode = module.minipyt_dots_mode
        except :
            pass

        # these are both flags and the function objects for module
        # setup/teardown and pycode function
        setup = None

        try :
            setup = module.setUp
        except AttributeError :
            pass

        if setup is not None :
            if debug :
                debug_fd.write("process_file: running setUp")
            print "setUp"
            setup()

        # look through the module for things that might be tests
        if debug :
            debug_fd.write("process_file: inspect module namespace\n")
        l = [ ]
        for name, ob in inspect.getmembers(module, inspect.isfunction) + inspect.getmembers(module, inspect.isclass) :
            if debug :
                debug_fd.write("process_file: inspect name %s\n"%name)

            try :
                # if it has minipyt_test, that value is a flag
                # about whether it is a test or not.
                n = getattr(ob,'__test__')
                if n :
                    rname = getattr(ob,'__test_name__', name)
                    l.append( (rname, ob) )
                continue
            except AttributeError :
                # if it does not have __test__, we consider
                # other criteria that may make it count as a test.
                pass

            # if the name looks like a test, it is a test
            if name.startswith('test') or name.endswith('test') :
                l.append( (name, ob) )

        # now we have a list of all the tests in the file

        # we have an opportunity to get them in the order they were
        # defined in the file, instead of alpha.  Just need to
        # figure out how.

        try :
            test_order = module.minipyt_test_order
        except :
            test_order = 'line'

        sort_test_list(l, test_order)

        for x in l :
            name, ob = x

            # default name is the object name

            # but use nose-compatible name, if present
            rname = getattr(ob,'compat_func_name', name)

            # but use our explicitly defined name, if present
            rname = getattr(ob,'__test_name__', rname)

            # call the appropriate runner
            if type(ob) == function :
                print 'function', name, 'as', rname
                run_test_function( rpt, module, rname, ob )
            else :
                print 'class', name, 'as', rname
                run_test_class( rpt, module, name, ob, test_order )

        # look for a pycode function - call it if necessary
        #
        # pycode functions are obsolete, but we're keeping this until 
        # we get rid of a few more tests that still use it.
        pycode_fn = None
        try :
            pycode_fn = module.pycode
        except AttributeError :
            pass

        if callable(pycode_fn) :
            print 'old-style pycode test detected'
            pycode_fn(1, rpt=rpt)

        print 'tests completed'

        # look for a teardown function - call it if necessary
        teardown = None

        try :
            teardown = module.tearDown
        except AttributeError :
            pass

        if teardown :
            print "tearDown"
            teardown()

    except AssertionError :
        file_status = 'F'
        traceback.print_exc()
    except :
        file_status = 'E'
        traceback.print_exc()

    # restore sys.path
    sys.path = sys_path_save

    log = pycode.end_snarf_stdout()
    file_end_time = time.time()

    tda = { }
    tra = { }

    try :
        tda = module.module_tda
    except :
        pass

    try :
        tra = module.module_tra
    except :
        pass

    if exception_str is not None :
        tra['exception'] = exception_str

    # the name for the report on the file as a whole is derived from
    # the file name. the report object is already set up to do this,
    # so we do not need to provide any more parts of the test name.
    gen_report( rpt, None, file_status, file_start_time, file_end_time, tda, tra, log )

    rpt.close()

    # now that we have closed it, we can't allow anyone else to use it.
    pycode.cached_rpt = None

    if dots_mode :
        dots_file.write('\n')
        dots_file.flush()

    if debug :
        debug_fd.write("End process_file\n")


####
#### an entry point for pdk_python_runner to use
####

def main(arg) :
    if debug :
        print len(arg)
        for x in arg :
            print "arg: ",x
        print 'PDK_FILE = ',os.environ['PDK_FILE']

    if len(arg) > 1 :
        # if there are multiple args then:
        #   arg[0] is the name of a python file with test definitions in it
        #   arg[1] is the name to use for this test
        #   the remaining args are parameters for the test code to use
        process_file( arg[0], arg[1], arg[2:] )
    else :
        process_file( arg[0] )


####
#### a main program so we can run this thing for debugging purposes
####

if __name__ == '__main__' :
    main(sys.argv[1:])

