import stat
import os
import os.path
import pandokia.run_file
import time
import sys
import traceback

def run( dirname, envgetter ) :
    # Run all the tests to be found in directory dirname.
    # This is not recursive into other directories.
    #
    print "run directory ",dirname
    dirname = os.path.abspath(dirname)

    dir_list = os.listdir( dirname )
    dir_list.sort()

    for basename in dir_list :

        full_name = os.path.join(dirname,basename)
        try :
            file_stat = os.stat(full_name)
        except Exception, e :
            print full_name, e
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

        # If the file is disabled, skip it
        if file_disabled(dirname, basename, runner) :
            print "##### DISABLED : %s/%s"%(dirname,basename)
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
            pandokia.run_file.run(dirname, basename, envgetter, runner )
        except Exception, e:
            xstr=traceback.format_exc()
            print "Exception running file %s/%s: %s"%(dirname, basename, e)
            print xstr

            

def file_disabled(dirname, basename, runner ) :
    n=basename.rfind(".")
    if n >= 0 :
        disable_name = basename[:n]
    else :
        disable_name = basename
    f = dirname+"/"+disable_name+".disable"
    try :
        os.stat(f)
        return True
    except OSError :
        return False

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
    f.write('host=%s\n'         %pandokia.run_file.gethostname() )
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

