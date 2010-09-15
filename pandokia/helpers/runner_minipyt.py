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

#
if debug :
    debug_fd = open("/dev/tty","w")

# just in case somebody needs to see a lot of dots when they run their tests. :)
default_dots_mode = ''

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
# Her is a sort function to sort the list of tests into the order that
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
        debug_fd.write("sorted test list: ")
        debug_fd.write(str([ name for (name,value) in l]))
        debug_fd.write('\n')

# Generate the report record for a single test.
def gen_report( rpt, name, status, start_time, end_time, tra, tda, log ) :
    rpt.report( name, status, start_time, end_time, tra, tda, log )
    if dots_mode :
        if status == 'P' :
            dots_file.write('.')
        else :
            if dots_mode == 'N' :
                if name is None :
                    name = rpt.test_prefix
                dots_file.write(' %s: %s\n'%(name,status) )
            elif dots_mode == 'S' :
                dots_file.write(status)
            elif dots_mode == 'O' :
                dots_file.write('-'*70)
                dots_file.write('\n%s: %s\n'%(name,status) )
                dots_file.write(log)
                dots_file.write('\n')
        dots_file.flush()

####
#### actually run a test function
####

def run_test_function(rpt, mod, name, ob) :

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
    gen_report( rpt, name, status, start_time, end_time, mod.tra, mod.tda, log )
    

####
#### actually run a test class
####

# There is a test name that corresponds to the whole class.  This gathers any
# result and/or error that comes from the class, but not from an individual
# test method.

def run_test_class( rpt, mod, name, ob, test_order ) :

    pycode.snarf_stdout()
    class_start_time = time.time()

    class_disable = getattr(ob, '__disable__', False )
    if not class_disable :
        class_status = 'P'
    else :
        class_status = 'D'

    try :
        l = [ ]

        have_setup = 0
        have_teardown = 0

        # look through the class for methods that are interesting to us.

        for f_name, f_ob in inspect.getmembers(ob, inspect.ismethod) :

            # magic names to remember.  (The names are ugly
            # because they are copied from nose, which copied
            # them from unittest, which copied them from junit.)

            if f_name == 'setUp' :
                have_setup = 1
                continue

            if f_name == 'tearDown' :
                have_teardown = 1
                continue

            if debug :
                debug_fd.write('function name %s\n'%f_name)

            # if the method has __test__, that value is a flag
            # about whether it is a test or not.  Note there are
            # ** three ** conditions here: true, false, and no attribute
            try :
                n = getattr(f_ob,'__test__')
                if debug :
                    debug_fd.write('__test__ %s\n'%n)
                if n :
                    rname = getattr(f_ob,'__test_name__', f_name)
                    if debug :
                        debug_fd.write('actual name used %s\n'%rname)
                continue
            except AttributeError :
                pass

            # if the method name looks like a test, it is a test
            if f_name.startswith('test') or f_name.endswith('test') :
                l.append( (f_name, f_ob) )

        # have a deterministic order
        sort_test_list(l, test_order)

        # do we need to make a new instance of the object for every test?
        new_object_every_time = not getattr(ob,'minipyt_shared',0)

        # if not, we need to make just one right now
        if not new_object_every_time and not class_disable :
            class_ob = ob()

        # for each test method on the object
        for f_name, f_ob in l :
            if debug :
                debug_fd.write('test method: %s %s\n'%(f_name,str(f_ob)))

            save_tda = { }
            save_tra = { }


            pycode.snarf_stdout()

            fn_start_time = time.time()

            try :

                if ( not class_disable ) and ( not getattr( f_ob, '__disable__', False ) ) :
                    # gather up stdout/stderr for the test

                    # make the new object, if necessary
                    if new_object_every_time :
                        class_ob = ob()

                    # blank out the tda/tra dictionaries for each test.
                    class_ob.tda = save_tda
                    class_ob.tra = save_tra

                    # call the test method
                    try :
                        if have_setup :
                            class_ob.setUp()
                        f_ob(class_ob)
                        fn_status = 'P'
                    except AssertionError :
                        fn_status = 'F'
                        traceback.print_exc()
                    except :
                        fn_status = 'E'
                        traceback.print_exc()

                    # Always run teardown, no matter how the test worked out.
                    try :
                        if have_teardown :
                            class_ob.tearDown()
                    except :
                        fn_status = 'E'
                        traceback.print_exc()

                    # The user may have replaced these
                    # dictionaries, so we need to pick them
                    # out of the object.  ( Copy them out of the object because it may be
                    # gone by the time we need them. )
                    save_tda = class_ob.tda
                    save_tra = class_ob.tra

                    # if we make a new object instance for
                    # every test, dispose the old one now
                    if new_object_every_time :
                        del class_ob

                else :
                    # it was disabled
                    fn_status = 'D'

            except AssertionError :
                fn_status = 'F'
                traceback.print_exc()
            except :
                fn_status = 'E'
                traceback.print_exc()

            fn_end_time = time.time()

            fn_log = pycode.end_snarf_stdout()

            gen_report( rpt, name + '.' + f_name, fn_status, fn_start_time, fn_end_time, save_tda, save_tra, fn_log )

    except AssertionError :
        class_status = 'F'
        traceback.print_exc()
    except :
        class_status = 'E'
        traceback.print_exc()

    # this is the end of everything relating to the class.
    class_end_time = time.time()
    class_log = pycode.end_snarf_stdout() 

    gen_report( rpt, name, class_status, class_start_time, class_end_time, { }, { }, class_log )
    

####
#### run a whole file of tests
####

# There is a test name that corresponds to the file.  This gathers any
# result and/or error that comes from the file, but not from an individual
# test.

def process_file( filename ) :

    if debug :
        debug_fd.write("begin process_file\n")

    global dots_mode

    dots_mode = default_dots_mode

    if dots_mode :
        dots_file.write('File: %s\n'%filename)
        dots_file.flush()

    # pandokia log entry object - writes the pandokia reports
    rpt = pycode.reporter( filename )

    # the module name is the basename of the file, without the extension
    module_name = os.path.basename(filename)
    module_name = os.path.splitext(module_name)[0]

    # gather up the stdout from processing the whole file.    individual
    # tests will suck up their own stdout, so it will not end up in
    # the file.
    pycode.snarf_stdout()

    file_start_time = time.time()
    file_status = 'P'

    # make sure we can import from the directory where the file is
    sys_path_save = copy.copy(sys.path)
    sys.path.insert(0,os.path.dirname(filename))

    try :

        if debug :
            debug_fd.write("process_file: about to import %s %s\n"%(module_name,filename))

        # import the module
        module = imp.load_source( module_name, filename )

        if debug :
            debug_fd.write("process_file: import succeeds\n")

        try :
            dots_mode = module.minipyt_dots_mode
        except :
            pass

        # these are both flags and the function objects for module
        # setup/teardown and pycode function
        setup = None
        teardown = None
        pycode_fn = None

        try :
            setup = module.setUp
        except AttributeError :
            pass

        try :
            teardown = module.tearDown
        except AttributeError :
            pass

        try :
            pycode_fn = module.pycode
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
            test_order = 'alpha'

        sort_test_list(l, test_order)

        for x in l :
            name, ob = x

            # use nose-compatible name, if present
            rname = getattr(ob,'compat_func_name', name)
            rname = getattr(ob,'__test_name__', rname)

            if type(ob) == function :
                print 'function', name, 'as', rname
                run_test_function( rpt, module, rname, ob )
            else :
                print 'class', name, 'as', rname
                run_test_class( rpt, module, name, ob, test_order )

        if pycode_fn :
            print 'pycode test detected'
            pycode_fn(1, rpt=rpt)

        print 'tests completed'

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

    # the name for the report on the file as a whole is derived from
    # the file name. the report object is already set up to do this,
    # so we do not need to provide any more parts of the test name.
    gen_report( rpt, None, file_status, file_start_time, file_end_time, { }, { }, log )

    rpt.close()

    if dots_mode :
        dots_file.write('\n')
        dots_file.flush()

    if debug :
        debug_fd.write("End process_file\n")


####
#### an entry point for pdk_python_runner to use
####

def main(argv) :
    for x in argv :
        process_file( x )


####
#### a main program so we can run this thing for debugging purposes
####

if __name__ == '__main__' :
    main(sys.argv[1:])

