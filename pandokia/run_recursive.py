import os
import os.path
import pandokia
import pandokia.multirun
import pandokia.run_status
import stat
import errno

import pandokia.common as common


def generate_directories( dir ) :
    #
    # This is a generator to find all the directories that _might_
    # have tests in them.  (We will find out for sure later.)
    #
    # result is a directory name.
    #
    # This is way easier than trying to do this with os.walk
    #

    if not os.path.isdir(dir) :
        print "WARNING: ",dir," is not a directory"
        return

    # The first directory we can yield is the one we are starting in.
    yield dir

    try :
        # Now we look at all the subdirectories.
        dir_list = os.listdir( dir )
    except ( OSError, IOError ) , e:
        # various errors listing the directory mean we skip it
        print e
        return

    dir_list.sort()

    for short_name in dir_list :
        # Skip directories that we know to be non-useful.
        if short_name in pandokia.cfg.exclude_dirs :
            continue

        # Find out if it is a directory.  If not, skip it.
        full_name = os.path.join(dir,short_name)
        try :
            # lstat - not recursing into symlinks
            file_stat = os.lstat(full_name)
        except OSError, e:
            if e.errno != errno.ENOENT :
                print "cannot lstat",full_name
                print e
            continue

        if not stat.S_ISDIR(file_stat.st_mode) :
            continue

        # It is a directory - recursively search it.
        for x in generate_directories( full_name ) :
            yield x


def run( dirs, envgetter, max_procs=None ) :

    # The basic command to run tests in a directory is
    #   pdk run --dir --environment_already_set $directory
    cmd = [ 'pdkrun', '--dir', '--environment_already_set' ]

    # We use multirun to runs up to max_procs concurrent processes.
    # In each process, we run tests in one directory.  We don't
    # know max_procs in advance, or even if it is the same through
    # the whole run.  So, remember which slots were used.  Later,
    # will will look for a status file from each slot.
    slots_used = { }

    # loop over the directories they gave us; recurse into each.
    for x in dirs :

        x = os.path.abspath(x)

        # Declare the maximum processes to the parallel runner.
        # Each process can run tests in one directory at a time.
        # This is inside the loop because we are not certain of
        # the value for PDK_PARALLEL until we have a directory
        # where we look for pdk_environment.
        d = envgetter.envdir(x)
        if max_procs is not None :
            pass
        elif 'PDK_PARALLEL' in d :
            max_procs = d['PDK_PARALLEL']
        else :
            max_procs = 1
        try :
            max_procs = int(max_procs)
        except ValueError :
            print "cannot convert ",max_procs," to integer - running one process at a time"
            max_procs = 1
        pandokia.multirun.set_max_procs(max_procs)

        # x is a directory; y is a loop over all nested subdirectories
        # that may be of interest.
        for y in generate_directories( x ) :

            # For max_procs=N, we have slots 0 to N-1 to
            # run test processes in.  We wait for a process
            # slot to open up because we want to tell the
            # new process which slot it is in.  (It can use that
            # for things like file names.)
            n = pandokia.multirun.await_process_slot()

            # remember that we used this slot at least once
            slots_used[n] = 1

            # Get the environment to use for this directory.
            # We will pass this in as the process's inherited
            # environment.  (That's why we say --environment_already_set.)
            d = envgetter.envdir(y)

            # Add the process slot number to the environment.  The
            # test runners can use this, but it is now way too late 
            # to define other environment variables in terms of
            # PDK_PROCESS_SLOT.
            #
            # run_dir uses PDK_PROCESS_SLOT to choose a pdk log file
            # to report results into.
            d['PDK_PROCESS_SLOT'] = str(n)

            # Start the actual process to run the tests in that directory.
            pandokia.multirun.start(cmd + [ y ], d )

    # multirun starts several concurrent processes, but we don't want 
    # to say we are finished until they are all done.
    pandokia.multirun.wait_all()

    # ensure that all the slots are reporting empty by the time we
    # are finished.
    for slot in slots_used :
        pandokia.run_status.pdkrun_status( '', slot )


    # collect the summary of how many tests had each status
    stat_summary = { }
    for x in slots_used :
        fn = "%s.%s.summary"%( os.environ['PDK_LOG'], str(x))
        try :
            f = open(fn,"r")
        except IOError, e:
            # It is possible for a process slot to run a process without
            # creating a log file.  (e.g. when there is a directory that 
            # does not contain any tests.)  So, if there is no file, that
            # is not an errr.
            if e.errno == errno.ENOENT :
                continue
            raise
        for line in f :
            line = line.strip()
            if line == 'START' :
                continue
            if line.startswith('.') :
                continue
            if line == '' :
                continue
            line = line.split('=')
            status = line[0]
            count = line[1]
            stat_summary[status] = stat_summary.get(status,0) + int(count)
        f.close()

        # we are the only consumer for this file, so toss it (but don't
        # get too excited if it doesn't work)
        try :
            os.unlink(fn)
        except :
            pass


    print ""
    print "Summary of entire run:"
    common.print_stat_dict(stat_summary)

    # bug: multirun is not reporting exit status back to us, so we have no
    # error status to return.
    return ( 0, stat_summary )

