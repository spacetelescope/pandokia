import os
import os.path
import sys
import fnmatch

import pandokia

# subprocess is the interface du jour for starting a new process
import subprocess

import pandokia.common as common

#
# find the file name patterns that associate a file name with a test runner
#
runner_glob_cache = { }

def read_runner_glob ( dirname ) :
    # Find the list of file patterns and test runners that apply
    # in a specific directory.  This is only called once per directory.
    # The content of this file does NOT apply to more deeply nested
    # directories.
    #
    # return value is a list of ( file_pattern, test_runner )
    # 

    # maybe we already know the answer
    if dirname in runner_glob_cache :
        return runner_glob_cache[dirname]

    # try to read it from a file in the directory with the test
    try :
        f=open(dirname+"/pdk_runners","r")
    except :
        # bug: no error handling - should distinguish file not found
        # (IOError) from permission denied (IOError) or not-a-file
        # (IOError)
        return pandokia.cfg.runner_glob

    # read pairs from file
    # bug: no real error handling here
    l = [ ]
    for line in f :
        line = line.strip()
        if line.startswith("#"):
            continue
        line = line.split()
        if len(line) == 2 :
            l.append( (line[0],line[1]) )

    # explicit close
    f.close()

    # the list we find in the file goes in front of the defaults from the config
    l = l + pandokia.cfg.runner_glob
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

        runner_mod = get_runner_mod(runner)
        env['PDK_FILE'] = basename

        env['PDK_LOG'] = pdk_log_name(env) 

        # We will write a count of statuses to a summary file.  But where?
        # If no PDK_PROCESS_SLOT, we do not need a summary -- we just return
        # it to our caller.  Otherwise, we use a file based on the log file name.
        if 'PDK_PROCESS_SLOT' in env :
            summary_file = env['PDK_LOG'] + '.summary'
        else :
            summary_file = None

        f=open(env['PDK_LOG'],'a+')
        f.seek(0,os.SEEK_END)
        end_of_log = f.tell()
        f.close()

        env['PDK_DIRECTORY'] = dirname

        #
        # A test runner that only works within pandokia can assume
        # that we made all of these log entries for it.

        full_filename = dirname+"/"+env['PDK_FILE']
        f = open(env['PDK_LOG'],"a")
        f.write("\n\nSTART\n")
        f.write('test_run=%s\n'     % env['PDK_TESTRUN'])
        f.write('project=%s\n'      % env['PDK_PROJECT'])
        f.write('host=%s\n'         % common.gethostname() )
        f.write('location=%s\n'     % full_filename )
        f.write('test_runner=%s\n'  % runner)
        f.write('context=%s\n'      %env['PDK_CONTEXT'])
        f.write("SETDEFAULT\n")
        f.close()

        # fetch the command that executes the tests
        cmd = runner_mod.command(env)

        if cmd is not None :
            # run the command -- To understand how we do it, see
            # "Replacing os.system()" in the docs for the subprocess module.
            if not isinstance(cmd, list ) :
                cmd = [ cmd ]
            for thiscmd in cmd :
                print 'COMMAND :', thiscmd, '(for file %s)'% full_filename
                sys.stdout.flush()
                sys.stderr.flush()
                p = subprocess.Popen(thiscmd, shell=True, env = env )
                ( pid, status ) = os.waitpid(p.pid,0)
                # python doesn't just give you the unix status
                if status & 0xff == 0 :
                    status="exit %d"%(status >> 8)
                    if status != 0 :
                        return_status = 1
                else :
                    return_status = 1
                    if status & 0x80 :
                        status="signal %d, core dumped" % ( status & 0x7f )
                    else :
                        status="signal %d" % ( status & 0x7f )
                print "COMMAND EXIT:",status

                

        else :
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
            f.seek(end_of_log,os.SEEK_SET)
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

    return ( return_status, stat_summary )


