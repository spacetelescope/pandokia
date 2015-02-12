import os
import os.path
import sys
import fnmatch
import datetime
import signal
import errno

import pandokia

import platform
windows = platform.system() == 'Windows'


# subprocess is the interface du jour for starting a new process
import subprocess

import pandokia.common as common

from pandokia.run_status import pdkrun_status

import pandokia.runners

#
# find the file name patterns that associate a file name with a test runner
#


# There is a default list of runners in the runners package
runner_glob = pandokia.runners.runner_glob

# you can override the default set of runners in the config file
try :
    runner_glob = pandokia.cfg.runner_glob + runner_glob
except AttributeError :
    pass

# here is a cache of the runner specifications we found for each directory
runner_glob_cache = { }

def read_runner_glob ( dirname ) :
    # Find the list of file patterns and test runners that apply
    # in a specific directory.
    #
    # return value is a list of ( file_pattern, test_runner )
    # 
    dirname = os.path.abspath(dirname)

    # maybe we already know the answer
    if dirname in runner_glob_cache :
        return runner_glob_cache[dirname]

    # we don't know, so we have to go looking.

    # find the parent
    parent = os.path.abspath( dirname + '/..' )

    # work around a bug in os.path.abspath
    parent = parent.replace('//','/')

    if parent == dirname :
        # if the parent is the same, we are at the top of the
        # filesystem.  On linux, this looks like '/'.  On
        # windows, this looks like 'Z:\'
        parent_list = runner_glob

    elif os.path.exists( dirname + '/pandokia_top' ):
        # if we see pandokia_top, we are at the top of the test
        # tree.
        parent_list = runner_glob

    else :
        # otherwise, we need to get the list of runners from the
        # parent directory
        parent_list = read_runner_glob( parent )

    # now we have the list from the higher directories; try to 
    # read the pdk_runners from the directory we are interested in.
    try :
        f=open(dirname+"/pdk_runners","r")
    except IOError, e :
        if e.errno == errno.ENOENT :
            return parent_list
        raise

    # read pairs from file
    # bug: no real error handling here
    here_list = [ ]
    for line in f :
        line = line.strip()
        if line.startswith("#"):
            continue
        line = line.split()
        if len(line) == 2 :
            here_list.append( (line[0],line[1]) )

    # explicit close
    f.close()

    # the list we find in the file goes in front of the defaults from the config
    l = here_list + parent_list
    runner_glob_cache[dirname] = l

    return l


#
# Choose the actual runner to use for a specific file.
#
def select_runner(dirname, basename) :

    runner_glob = read_runner_glob( dirname )

    for pat, runner in runner_glob :
        if fnmatch.fnmatch(basename,pat) :
            if runner == 'none' :
                return None
            return runner

    return None


#
# find the python module that implements the interface to a specific
# test runner.
#
runner_modules = { }

def get_runner_mod(runner) :
    if runner in runner_modules :
        runner_mod = runner_modules[runner]
    else :
        try :
            n = "pandokia_runner_" + runner
            __import__(n)
        except ImportError :
            n = "pandokia.runners."+runner
            __import__(n)
        runner_mod = sys.modules[n]
        runner_modules[runner] = runner_mod
    return runner_mod

#
# Identify the prefix that should be inserted in front of the
# test name.
#
def get_prefix( envgetter, dirname ) :
    top = envgetter.gettop()
    assert ( dirname.startswith(top) )

    prefix = dirname[len(top):]+"/"
    if prefix.startswith("/") or prefix.startswith("\\") :
        prefix = prefix[1:]

    if 'PDK_TESTPREFIX' in os.environ :
        e = os.environ['PDK_TESTPREFIX'] 
        if not ( e.endswith('/') or e.endswith('.') ) :
            e += '/'
        prefix = e + prefix

    return prefix

# 
# find the name of the pdk log file to use with the current environment.
# This is mostly simple, but if we are running multiple tests in parallel,
# then we need to avoid two processes writing the same file at the same
# time.  We do this by adding a suffix -- we know that only one process
# will be using a specific value for PDK_PROCESS_SLOT at any time, so 
# that is our suffix.
#
def pdk_log_name( env ) :
    log = env['PDK_LOG']
    if 'PDK_PROCESS_SLOT' in env :
        log += '.' + env['PDK_PROCESS_SLOT']
    return log

#
# actually run the tests in a specific file
#
def run( dirname, basename, envgetter, runner ) :

    return_status = 0

    dirname = os.path.abspath(dirname)

    save_dir = os.getcwd()
    os.chdir(dirname)

    if runner is None :
        runner = select_runner(dirname, basename )

    if runner is not None :
        # copy of the environment because we will mess with it
        env = dict( envgetter.envdir(dirname) )

        env['PDK_TESTPREFIX'] = get_prefix( envgetter, dirname )

        env['PDK_TOP'] = envgetter.gettop()

        runner_mod = get_runner_mod(runner)

        env['PDK_FILE'] = basename

        env['PDK_LOG'] = pdk_log_name(env) 

        # We will write a count of statuses to a summary file.  But where?
        # If no PDK_PROCESS_SLOT, we do not need a summary -- we just return
        # it to our caller.  Otherwise, we use a file based on the log file name.
        if 'PDK_PROCESS_SLOT' in env :
            summary_file = env['PDK_LOG'] + '.summary'
            slot_id = env['PDK_PROCESS_SLOT']
        else :
            summary_file = None
            slot_id = '0'

        f=open(env['PDK_LOG'],'a+')
        # 2 == os.SEEK_END, but not in python 2.4
        f.seek(0,2)
        end_of_log = f.tell()
        f.close()

        env['PDK_DIRECTORY'] = dirname

        #
        # A test runner that only works within pandokia can assume
        # that we made all of these log entries for it.

        full_filename = dirname+"/"+env['PDK_FILE']

        pdkrun_status( full_filename )

        f = open(env['PDK_LOG'],"a")
        f.write("\n\nSTART\n")
        f.write('test_run=%s\n'     % env['PDK_TESTRUN'])
        f.write('project=%s\n'      % env['PDK_PROJECT'])
        f.write('host=%s\n'         % env['PDK_HOST'] )
        f.write('location=%s\n'     % full_filename )
        f.write('test_runner=%s\n'  % runner)
        f.write('context=%s\n'      %env['PDK_CONTEXT'])
        f.write("SETDEFAULT\n")
        f.close()

        # fetch the command that executes the tests
        cmd = runner_mod.command(env)

        if cmd is not None :
            # run the command -- To understand how we do it, see
            # "Replacing os.system()" in the docs for the subprocess module,
            # then consider the source code for subprocess.call()
            if not isinstance(cmd, list ) :
                cmd = [ cmd ]
            for thiscmd in cmd :
                print 'COMMAND :', repr(thiscmd), '(for file %s)'% full_filename, datetime.datetime.now()
                sys.stdout.flush()
                sys.stderr.flush()
                if windows :
                    # on Windows, we dare not let the child process have access to the stdout/stderr
                    # that we are using.  Apparently, the child process closes stderr and it somehow
                    # ends up closed for us too.  So, stuff it into a temp file and then copy the
                    # temp file to our stdout/stderr.
                    f = open("stdout.%s.tmp"%slot_id,"w")
                    p = subprocess.Popen( thiscmd, stdout=f, stderr=f, shell=True, env = env, creationflags = subprocess.CREATE_NEW_PROCESS_GROUP )
                    # bug: implement timeouts
                    status = p.wait()
                    f.close()
                    f = open("stdout.%s.tmp"%slot_id,"r")
                    while 1 :
                        buffer = f.read()
                        if buffer == '' :
                            break
                        sys.stdout.write(buffer)
                    f.close()
                    os.unlink("stdout.%s.tmp"%slot_id)
                else :
                    # on unix, just do it
                    p = subprocess.Popen( "exec " + thiscmd, shell=True, env = env, preexec_fn = unix_preexec )
                    if 'PDK_TIMEOUT' in env :
                        proc_timeout_start(env['PDK_TIMEOUT'], p)
                        status = p.wait()
                        print "return from wait, status=",status
                        proc_timeout_terminate()
                        if timeout_proc_kills > 0 :
                            # we tried to kill it for taking too long -
                            # report an error even if it managed to exit 0
                            return_status = 1
                    else :
                        status = p.wait()

                # subprocess gives you weird status values
                if status > 0 :
                    status="exit %d"%(status >> 8)
                    if status != 0 :
                        return_status = 1
                else :
                    return_status = 1
                    status="signal %d" % ( - status )
                    # subprocess does not tell you if there was a core
                    # dump, but there is nothing we can do about it.

                print "COMMAND EXIT:",status,datetime.datetime.now()

        else :
            # BUG: no timeout! - fortunately, this is a minor issue
            # because we don't currently have anything that uses
            # run_internally() except to cough out errors about
            # unsupported runners on Windows

            # There is no command, so we run it by calling a function.
            # This runs the test in the same python interpreter that 
            # this file is executing in, which is normally not
            # preferred because a problem in the test runner, or even
            # in the test, could potentially kill the pandokia meta-runner.
            print "RUNNING INTERNALLY (for file %s)"%full_filename
            runner_mod.run_internally(env)
            print "DONE RUNNING INTERNALLY"

        stat_summary = { }
        for x in pandokia.cfg.statuses :
            stat_summary[x] = 0

        if 1 :
            # if the runner did not provide a status summary, collect it from
            # the log file.
            # [ This is "if 1" because no runners currently know how to do it.
            #   Later, some of them will leave behind a status summary file; we 
            #   will read that instead.   ]
            f=open(env['PDK_LOG'],'r')
            # 0 == os.SEEK_SET, but not in python 2.4
            f.seek(end_of_log,0)
            while 1 :
                l = f.readline()
                if l == '' :
                    break
                l = l.strip()
                if l.startswith('status=') :
                    l=l[7:].strip()
                    stat_summary[l] = stat_summary.get(l,0) + 1
            f.close()

        common.print_stat_dict( stat_summary )
        print ""
        if summary_file : 
            # The summary file has a similar format to the log, but there is
            # a "START" line after each record.   If somebody accidentally 
            # tries to import it, the importer can never find any data.
            f = open(summary_file,'a')
            for x in stat_summary :
                f.write("%s=%s\n"%(x,stat_summary[x]))
            # ".file" can never look like a valid status
            f.write(".file=%s\n"%full_filename)
            f.write("START\n\n")
            f.close()

    else :
        print "NO RUNNER FOR",dirname +"/"+basename,"\n"

    os.chdir(save_dir)

    pdkrun_status( '' )

    return ( return_status, stat_summary )


##########
#
# various functions relating to killing a child process that takes
# too long.
#
# We can only be running one child at a time in this file, so the
# accounting is pretty easy.
#

if windows :
    # bug: have to implement timeouts for windows someday.
    pass

else :

    # We ask subprocess to call this function in the child, before the exec.
    #
    # In this case, setpgrp() so we can killpg a runaway test.  Killing just
    # the test process isn't enough because the test may have child processes
    # of its own.  
    #
    # If the test itself creates new process groups, we have a problem.  It
    # may be worth looking in to cgroups on linux to deal with that.
    def unix_preexec() :
        os.setpgrp()

    # the process we are waiting for.
    timeout_proc = None

    # how many times we tried to kill it.  first kill is sigterm, second is
    # sigkill, then we give up waiting
    timeout_proc_kills = 0

    # remember the duration so we can say how long it was when it expires
    timeout_duration = None


    # An exception to raise to abort Popen.wait().
    #
    # at this time, you don't actually catch this exception anywhere -
    # it crashes the whole program.  It is an old-style class to make
    # it less likely that somebody might catch it with "except Exception".
    #
    # I initially considered this to be so unlikely that I never bothered
    # to figure out how to handle this exception.  When a machine starts
    # thrashing (because the working set of all the processes is bigger
    # than physical memory), it can happen, though.
    #
    # b.t.w. This exception kills a pdkrun for a particular directory,
    # but not the entire test run.  Later tests in that directory may
    # be missing.
    class timeout_not_going_away:
        pass

    ## 
    ## start the timeout for the child process
    ##
    def proc_timeout_start(timeout, p) :
        global timeout_proc, timeout_proc_kills, timeout_duration
        timeout_proc = p
        timeout_proc_kills = 0
        timeout_duration = timeout
        signal.signal(signal.SIGALRM, proc_timeout_callback)
        signal.alarm(int(timeout))

    # Kill the process group, but no error if it does not exist.  (In case
    # it exited before we got here.)
    def killpg_maybe( pid, signal ) :
        print "killpg -%d %d"%(signal,pid)
        try :
            os.killpg( pid, signal )
        except OSError, e:
            print "killpg exception:",e
            if e.errno != errno.ESRCH :
                raise

    #
    # callback that happens when it is time to kill the process
    #

    def proc_timeout_callback(sig, stack):
        global timeout_proc_kills
        if timeout_proc :
            pid = timeout_proc.pid
            print "PID=%d"%pid
            sys.stdout.flush()
            if timeout_proc_kills == 0 :
                os.system('ps -fp %s' %pid)
                sys.stdout.flush()
                print "timeout expired - terminate after %s"%str(timeout_duration)
                sys.stdout.flush()
                os.system('top -b -n 1')
                sys.stdout.flush()
                os.system('ps -efl')
                sys.stdout.flush()
                os.system('sleep 5')
                sys.stdout.flush()
                os.system('ps -efl')
                sys.stdout.flush()
                killpg_maybe( pid, signal.SIGTERM )
                os.system('top -b -n 1')
            elif timeout_proc_kills == 1 :
                print "timeout expired again - kill"
                killpg_maybe( pid, signal.SIGKILL )
            elif timeout_proc_kills == 2 :
                print "timeout expired yet again - now what?"
                raise timeout_not_going_away()

            timeout_proc_kills += 1
            signal.alarm(10)


    ##
    ## cancel the timeout for the current child process
    ##

    def proc_timeout_terminate() :
        signal.alarm(0)
        timeout_proc = None

