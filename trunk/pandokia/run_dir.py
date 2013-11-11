import stat
import os
import os.path
import pandokia.run_file
import time
import sys
import traceback
import errno

import pandokia.common as common

def run( dirname, envgetter ) :
    # Run all the tests to be found in directory dirname.
    # This is not recursive into other directories.
    #
    # return 1 if there was an error, 0 otherwise; try to
    # do as much as possible, though.
    #
    printed_dirname = 0

    was_error = 0

    dirname = os.path.abspath(dirname)

    try :
        dir_list = os.listdir( dirname )
    except Exception, e:
        print "Cannot search for tests in ",dirname
        print e
        print ""
        return 1, {}

    dir_list.sort()

    # As we run each file, we will get a count of status values of each type.
    # t_stat keeps a running sum for the current directory.
    t_stat = { }

    for basename in dir_list :

        full_name = os.path.join(dirname,basename)
        try :
            file_stat = os.stat(full_name)
        except OSError, e :
            if e.errno == errno.ENOENT :
                # not an error for somebody to delete a file between when
                # we start the test and end the test.  most commonly,
                # this is a temp file or something, not a test.
                continue
            print "Cannot stat file ",full_name
            print e
            was_error = 1
            continue
        except Exception, e :
            print "Cannot stat file ",full_name
            print e
            was_error = 1
            continue

        if not stat.S_ISREG(file_stat.st_mode) :
            # we skip any thing that is not a file
            continue

        # Decide which test runner this file wants to use.  If the
        # answer is None, this file does not contain tests.
        runner = pandokia.run_file.select_runner(dirname, basename)

        # if runner comes back None, that means that select_runner is
        # saying "this is not a test"
        if runner is None :
            continue

        # Don't print the directory name until it looks like we are
        # actually going to do anything here.  This suppresses all
        # output completely for directories that do not have any tests.
        if not printed_dirname :
            print "directory",dirname
            printed_dirname=1

        # If the file is disabled, skip it
        if file_disabled(dirname, basename) :
            print "Disabled : %s/%s"%(dirname,basename)
            m = pandokia.run_file.get_runner_mod( runner )

            env = { }
            env.update( envgetter.envdir(dirname) )
            env['PDK_TESTPREFIX'] = pandokia.run_file.get_prefix( envgetter, dirname )

            env['PDK_FILE'] = basename

            # ask the runner what disabled tests are in that file.
            save_dir = os.getcwd()
            os.chdir(dirname)

            # flush the output file because m.list() might start a new process.
            # really, m.list() should do that itself, but I don't trust every
            # author of every new runner to do it.
            sys.stdout.flush()
            sys.stderr.flush()
            l = m.list( env )

            os.chdir(save_dir)

            if l is not None :
                # l is a list of the names of tests that were in that file.
                # We will write a status=D record for each disabled test.
                write_disabled_list(env, l, dirname, basename, runner )
            else :
                pass
                # If the function returns None, it means that it does not
                # know how to report the disabled tests.  That's too bad,
                # but we can at least go on.
            continue

        # not disabled - run it
        try :
            ( err, lstat ) = pandokia.run_file.run(dirname, basename, envgetter, runner )
            was_error |= err
            for x in lstat :
                t_stat[x] = t_stat.get(x,0) + lstat[x]
        except Exception, e:
            xstr=traceback.format_exc()
            print "Exception running file %s/%s: %s"%(dirname, basename, e)
            print xstr
            print ''
            was_error = 1

    # print the status summary for the directory.
    print ""
    print "%s:"%dirname
    common.print_stat_dict(t_stat)

    return ( was_error, t_stat )


#
# check for a disable file, indicating that we should not run tests in a file
#
def file_disabled(dirname, basename) :
    # dirname = engine/spider/stis/spec/stellar-ext
    # basename = s_stis_spec_stellar-ext_10759.peng

    n=basename.rfind(".")
    if n >= 0 :
        disable_name = basename[:n]
    else :
        disable_name = basename


    dir_contents = os.listdir(dirname)

    # see if there are any .enable files for this test; if so, only run the test
    # if there is an enable file for the current context
    related_enable_files = []
    for i in dir_contents:
        if i.startswith(disable_name) and i.endswith('.enable'):
            related_enable_files.append(i)

    if len(related_enable_files) > 0:
        # see if enable file for this context exists
        valid_enable = '%s.%s.enable' %(disable_name, os.environ['PDK_CONTEXT'])
        if valid_enable in related_enable_files:
            return False
        else:
            return True
    else:
        f = dirname+'/'+disable_name
        try :
            os.stat(f + '.disable' )
            return True
        except OSError, e:
            #print e.args
            pass
        try :
            os.stat(f+'.'+os.environ['PDK_CONTEXT'] + '.disable' )
            return True
        except OSError, e:
            #print e.args
            pass
        return False

#
# write a test report for a list of disabled tests.
#

def write_disabled_list( env, name_list, dirname, basename, runner ) :
    nowstr=time.time()

    log = pandokia.run_file.pdk_log_name( env )

    f = open(log,"a+")
    f.write("\n\nSTART\n")
    f.write('test_run=%s\n'     %env['PDK_TESTRUN'])
    f.write('context=%s\n'      %env['PDK_CONTEXT'])
    f.write('project=%s\n'      %env['PDK_PROJECT'])
    f.write('test_runner=%s\n'  %runner)
    f.write('location=%s/%s\n'     %(dirname,basename))
    f.write('host=%s\n'         %env['PDK_HOST'])
    f.write('status=D\n')
    f.write('start_time=%s\n'   %nowstr)
    f.write('end_time=%s\n'     %nowstr)
    f.write('duration=0\n')
    f.write('SETDEFAULT\n')
    for x in name_list :
        # we do not use PDK_TESTPREFIX because the list already 
        # contains the full name of the test
        f.write('name=%s\n' % x)
        f.write('END\n')
    f.write("START\n")
    f.close()


