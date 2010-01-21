import os
import os.path
import pandokia
import pandokia.multirun
import stat
import errno


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

    # Now we look at all the subdirectories.
    dir_list = os.listdir( dir )
    dir_list.sort()

    for short_name in dir_list :
        # Skip directories that we know to be non-useful.
        if short_name in pandokia.cfg.exclude_dirs :
            continue

        # Find out if it is a directory.  If not, skip it.
        full_name = os.path.join(dir,short_name)
        try :
            file_stat = os.lstat(full_name)
        except OSError, e:
            if e.errno != errno.ENOENT :
                print full_name, e
        if not stat.S_ISDIR(file_stat.st_mode) :
            continue

        # It is a directory - recursively search it.
        for x in generate_directories( full_name ) :
            yield x


def run( dirs, envgetter, max_procs=None ) :

    # The basic command to run tests in a directory is
    #   pdk run --dir --environment_already_set $directory
    cmd = [ 'pdk', 'run', '--dir', '--environment_already_set' ]

    # loop over the directories they gave us; recurse into each.
    for x in dirs :

        x = os.path.abspath(x)

        # Declare the maximum processes to the parallel runner.
        # Each process can run tests in one directory at a time.
        # This is here because we don't have an environment to
        # look in for PDK_PARALLEL until we know a directory.
        d = envgetter.envdir(x)
        if max_procs is not None :
            n = max_procs
        elif 'PDK_PARALLEL' in d :
            n = d['PDK_PARALLEL']
        else :
            n = 1
        try :
            n = int(n)
        except ValueError :
            print "cannot convert ",n," to integer - running one process at a time"
            n = 1
        pandokia.multirun.set_max_procs(n)

        # x is a directory; y is a loop over all nested subdirectories
        # that may be of interest.
        for y in generate_directories( x ) :

            # For max_procs=N, we have slots 0 to N-1 to
            # run test processes in.  We wait for a process
            # slot to open up because we want to tell the
            # new process which slot it is in.  (It can use that
            # for things like file names.)
            n = pandokia.multirun.await_process_slot()

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


