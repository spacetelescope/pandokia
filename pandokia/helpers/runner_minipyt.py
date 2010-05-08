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

# set to true if you want dots
dots = False

if 'PDK_DOTS' in os.environ :
    if os.environ['PDK_DOTS'] != 'N' :
        dots = True

# remember where to send dots (sys.stdout will be captured into the log file)
dot_file = sys.stdout

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

def gen_report( rpt, name, status, start_time, end_time, tra, tda, log ) :
    rpt.report( name, status, start_time, end_time, tra, tda, log )
    if dots :
        if status == 'P' :
            dot_file.write('.')
        else :
            if name is None :
                name = rpt.test_prefix
            dot_file.write(' %s: %s\n'%(name,status) )

####
#### actually run a test function
####

def run_test_function(rpt, mod, name, ob) :

    # blank out the tda/tra dictionaries for each test.
    # poke directly into the module to do it.
    mod.tda = { }
    mod.tra = { }

    # start gathering up the stdout/stderr for this test
    pycode.snarf_stdout()

    # run the test
    start_time = time.time()
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
    class_status = 'P'

    try :
        l = [ ]

        have_setup = 0
        have_teardown = 0

        for f_name, f_ob in inspect.getmembers(ob, inspect.ismethod) :

            # magic names to remember.  (The names are ugly
            # because they are copied from nose, which copied
            # them from unittest.)

            if f_name == 'setUp' :
                have_setup = 1
                continue

            if f_name == 'tearDown' :
                have_teardown = 1
                continue

            # if it has __test__, that value is a flag
            # about whether it is a test or not.
            try :
                n = getattr(f_ob,'__test__')
                if n :
                    l.append( ( f_name, f_ob ) )
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
        if not new_object_every_time :
            class_ob = ob()

        # for each test method on the object
        for f_name, f_ob in l :

            save_tda = { }
            save_tra = { }

            try :
                # gather up stdout/stderr for the test
                pycode.snarf_stdout()

                fn_start_time = time.time()

                # make the new object, if necessary
                if new_object_every_time :
                    class_ob = ob()

                # blank out the tda/tra dictionaries for each test.
                class_ob.tda = save_tda
                class_ob.tra = save_tra

                # get a bound function that we can call
                fn = eval('class_ob.'+f_name)

                # call the test method
                try :
                    if have_setup :
                        class_ob.setUp()
                    fn()
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


        # import the module
        module = imp.load_source( module_name, filename )

        print 'import succeeds'

        # look through the module for things that might be tests
        l = [ ]
        for name, ob in inspect.getmembers(module, inspect.isfunction) + inspect.getmembers(module, inspect.isclass) :

            try :
                # if it has minipyt_test, that value is a flag
                # about whether it is a test or not.
                n = getattr(ob,'__test__')
                if n :
                    l.append( (name, ob) )
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

            if type(ob) == function :
                print 'function', name, 'as', rname
                run_test_function( rpt, module, rname, ob )
            else :
                print 'class', name, 'as', rname
                run_test_class( rpt, module, name, ob, test_order )

        print 'tests completed'

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


####
#### an entry point for pdk_python_runner to use
####

def main(argv) :
    for x in argv :
        if dots :
            dot_file.write('File: %s\n'%x)
        process_file( x )
        if dots :
            dot_file.write('\n')


####
#### a main program so we can run this thing for debugging purposes
####

if __name__ == '__main__' :
    main(sys.argv[1:])

