#!/usr/stsci/pyssgdev/Python-2.5.1/bin/python
import sys
import getopt
import os
import os.path
import stat
import errno
import pandokia.common as common

helpstr = '''
pdk run [ options ] [ files/directories ]
pdkrun  [ options ] [ files/directories ]

Runs tests and generates a pandokia report file of the results.

filename
    If you specify a file name, it runs the test in that file.

directoryname
    If you specify a file name, it searches for files in that
    directory that look like tests.

    If you do not specify any files/directories, the default
    command is "pdkrun -r ."

-r
--recursive
    search subdirectories

--log file
    write the PDK report log into this file

    default is "PDK_DEFAULT.LOG."+test_run

--parallel N
    run up to N tests concurrently ( but it can run at most one
    test at a time in any single directory )

    default is 1

--project NAME
    use NAME for the project name in reports
    
    default is "default"

--test_run NAME
    use NAME for the test_run in reports

    default is a generated string including the user name and the
    time to the nearest minute

-s
--status
    show the status 

    --wait
    -w
        wait for something to start before displaying the status
    
    -v
        clear the screen and do an updating display

    --vs
        same as pdkrun -s -w -v
        

Defaults can also be set by environment variables.


'''


def run(args) :
    import pandokia.envgetter

    recursive = False
    environment_already_set = False
    directory = False
    log         = os.environ.get("PDK_LOG",         None)
    project     = os.environ.get("PDK_PROJECT",     None)
    test_run    = os.environ.get("PDK_TESTRUN",     None)
    test_prefix = os.environ.get("PDK_TESTPREFIX",  None)
    context     = os.environ.get("PDK_CONTEXT",     'default')
    parallel    = os.environ.get("PDK_PARALLEL",    None)
    tmpdir      = os.environ.get("PDK_TMP",         None)
    verbose = 0 # not implemented
    dry_run = 0 # not implemented

    want_status = 0 # only want status, not actual run
    w_flag = 0      # when showing status, 

    if args == [ ] :
        args = [ '-r', '.' ]
    opts,args = getopt.gnu_getopt(args,"rvpsw",
            ["recursive", "environment_already_set", "dir", "log=",
             "project=", "test_run=", "test_prefix=",
             "show-command", "verbose","parallel=","help", "context=",
             "status","wait","vs",
             ])
    for (opt, optarg) in opts :
        if opt == '-r' or  opt == '--recursive' :
            recursive = True
        elif opt == '--environment_already_set' :
            environment_already_set = True
        elif opt == '--dir' :
            # we don't do anything with --dir, but it is there to see
            # when you run ps
            pass
        elif opt == '--help':
            print helpstr
            return ( 0, { } )
        elif opt == '--log' :
            log = optarg
        elif opt == '--test_run' :
            test_run = optarg
        elif opt == '--test_prefix' :
            test_prefix = optarg
        elif opt == '--project' :
            project = optarg
        elif opt == '--context' :
            context = optarg
        elif opt == '--verbose' or opt == '-v' :
            verbose = 1
        elif opt == '--dry-run' :
            dry_run = 1
        elif opt == '-' or opt == '--parallel' : 
            parallel = str(int(optarg))
        elif opt == '--status' :
            want_status=1
        elif opt == '--wait' or opt == '-w' :
            w_flag = 1
        elif opt == "--vs" :
            want_status = 1
            w_flag = 1
            verbose = 1

    if want_status :
        # only show the status of something else that is running
        import pandokia.run_status as x
        x.display(visual=verbose, waiting_for_start=w_flag)
        return 0,0

    if project is None :
        project = default_project()
    if test_run is None :
        test_run = default_test_run()
    if log is None :
        log = "PDK_DEFAULT.LOG."+test_run

    if parallel is not None :
        os.environ['PDK_PARALLEL'] = parallel

    log = os.path.abspath(log)

    os.environ['PDK_LOG'] = log
    os.environ['PDK_PROJECT'] = project
    os.environ['PDK_TESTRUN'] = test_run
    os.environ['PDK_CONTEXT'] = context

    if not 'PDK_STATUSFILE' in os.environ :
        initialized_status_file = 1
        os.environ['PDK_STATUSFILE'] = os.getcwd() + '/pdk_statusfile'
        import pandokia.run_status
        if parallel is None :
            n_status_records = 1
        else :
            n_status_records =  int(parallel)
        pandokia.run_status.init_status( file = os.environ['PDK_STATUSFILE'], n_records = n_status_records )
    else :
        initialized_status_file = 0

    if test_prefix is not None :
        os.environ['PDK_TESTPREFIX'] = test_prefix

    if tmpdir is None :
        tmpdir = os.getcwd()
    os.environ['PDK_TMP'] = tmpdir

    envgetter = pandokia.envgetter.EnvGetter(context=context )
    # environment_already_set=environment_already_set )     bug: we need to get this optimization in some how


    if recursive :
        import pandokia.run_recursive
        ( was_error, t_stat ) = pandokia.run_recursive.run(args, envgetter )
    else :
        # t_stat is a count of status values of each type.  The counts were printed at the end
        # of each file/dir that we ran, but if there are more than one file/dir, we will print
        # the total in t_stat.
        t_stat = { }
        was_error = 0
        n_things_run = 0
        for x in args :
            try :
                file_stat = os.stat(x)
            except OSError, e:
                print x, e
                continue

            lstat = { }
            if stat.S_ISDIR(file_stat.st_mode) :
                import pandokia.run_dir
                n_things_run += 1
                ( err, lstat ) = pandokia.run_dir.run(x, envgetter )
            elif stat.S_ISREG(file_stat.st_mode) :
                import pandokia.run_file
                n_things_run += 1
                
                basename = os.path.basename(x)
                dirname  = os.path.dirname(x)
                if dirname == '' :
                    dirname = '.'
                runner = pandokia.run_file.select_runner(dirname,basename)
                if runner is not None :
                    ( err, lstat ) = pandokia.run_file.run(dirname, basename, envgetter, runner )
                else :
                    print "no runner for ",x
                    err = 1
            else :
                lstat = { }
                err = 0
            was_error |= err
            for y in lstat :
                t_stat[y] = t_stat.get(y,0) + lstat[y]

        if n_things_run > 1 :
            print ""
            print "Summary:"
            common.print_stat_dict(t_stat)

    if initialized_status_file :
        for x in range(0, n_status_records ) :
            pandokia.run_status.pdkrun_status('', slot=x)
        os.unlink(os.environ['PDK_STATUSFILE'])

    return ( was_error, t_stat )

def default_project() :
    return "default"

def default_test_run() :
    import datetime
    d = datetime.datetime.now()
    if 'USER' in os.environ :
        fmt = 'user_' + os.environ['USER'] + '_%Y-%m-%d-%H-%M-%S'
    else :
        fmt = 'user_%Y-%m-%d-%H-%M'
    d = d.strftime( fmt )
    print "DEFAULT TEST RUN",d
    return d

def export_environment(args) :
    import pandokia.envgetter
    out = sys.stdout
    context=None
    env = { } 

    format = 'env'

    opts,args = getopt.getopt(args,"o:c:f",["output=", "context=", "full","csh","sh"])
    for (opt, optarg) in opts :
        if opt == '-o' or opt == '-optput' :
            out = open(optarg,"w")
        elif opt == '-c' or opt == '--context' :
            context = optarg
        elif opt == '-f' or opt == '--full' :
            env = os.environ
        elif opt == '--csh' or opt == '--sh' :
            format = opt[2:]

    if len(args) == 0 :
        args = [ '.' ]
    for x in args :
        envgetter = pandokia.envgetter.EnvGetter(context=context, defdict=env )
        envgetter.populate(x)
        envgetter.export(x,format=format,fh=out)

    out.flush()

