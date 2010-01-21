
#
# bug: this probably only works on unix.
#

import subprocess
import os
import sys
import errno
import time

__all__ = [ 'start', 'done', 'wait', 'wait_all', 'set_max_procs', 'await_process_slot' ]

# max_procs is how many concurrent processes we can start.  default
# is 1 because we might be a single CPU system.  The application can
# set this value higher with set_max_procs().
max_procs = 1


# This is a list of all the processes that are currently running.  The
# index is the process id.  The value is a tuple of ( callback, cookie )
all_procs = { }


# Each process gets a slot number that goes from 0 to max_procs - 1.
# This number can be used by the application to manage shared
# resources.
process_slot = [ ]


# This is a serial number that gets put into the environment variable
# "proc_count" when we start a new process.  The process can use it
# to make up unique file names or whatever.
proc_count = 0


# This is just a struct to store all the information about a process

class process:
    pid=None
    slot=None
    stdout_filename=None
    pass

def set_max_procs( n ) :
    global process_slot
    while len(process_slot) < n :
        process_slot.append(None)
    process_slot = process_slot[ : n ]
    global max_procs
    max_procs = n

set_max_procs(max_procs)


# wait for any process slot to be empty; return the slot number
def await_process_slot( ) :

    while len(all_procs) >= max_procs :
        wait()

    for n, proc_struct in enumerate(process_slot) :
        if proc_struct is None :
            return n
    # we should never fall out of the loop
    assert False


# claim a specific process slot for this process
def _use_process_slot( n, proc_struct ) :
    assert process_slot[n] is None
    process_slot[n] = proc_struct


def start( args, env=None, callback=None, cookie=None, slot=None ) :
    """
    Start another process, possibly waiting if it would go over the limit.

    This function starts a child process with args, env.  If starting
    another process would put us over the max_procs limit, then we
    first wait for one of the existing processes to exit.

    If there is an exception at the exec() call in the child, the
    child exits with code 255.  There is no way to pass the exception
    back to the parent.

    @param  args: argv[] style list of args to process; argv[0] is the
            program to execute
    @type   args: list

    @param  env:  os.environ style dict of environment variables; default is
            os.environ
    @type   env:  dict or None

    @param  callback: callback( cookie, status ) is called when the process
            exit is detected
    @type   callback: function( cookie, status )

    @param  cookie: cookie value passed to callback function when the process
            exit is detected
    @type   cookie: any

    @param  slot: process slot number returned by await_process_slot(); default
            is None, which means to allocate a slot
    @type   slot: int or None

    """
    if slot is None :
        slot = await_process_slot()
    assert process_slot[slot] is None 

    proc_struct = _run_proc(args, env, slot)

    proc_struct.callback = callback
    proc_struct.cookie = cookie

    all_procs[proc_struct.pid] = proc_struct

    _use_process_slot( slot, proc_struct )

    return slot


def done( pid, status ) :
    """
    Declare to mrun that a specific process has exited.

    If you perform os.wait yourself, mrun will not know about those
    processes that exited.  You can call this function directly to
    tell it.

    @param pid: process id of exited process
    @type  pid: int

    @param status: exit code of exited process, or None if not known.
    @type  status: int or None

    """
    if pid in all_procs :
        proc_struct = all_procs[pid]
        if proc_struct.callback :
            proc_struct.callback(proc_struct.cookie, status)
        del all_procs[pid]

    for n, proc_struct in enumerate(process_slot) :
        if not ( proc_struct is None ) and ( proc_struct.pid == pid ) :
            process_slot[n] = None
            sys.stdout.write('#### Output from process %d in slot %d\n'%(pid, n))
            f = open( proc_struct.stdout_filename, "r" )
            while True :
                x=f.read(32768)
                if x == '' :
                    break
                sys.stdout.write(x)
            f.close()
            sys.stdout.write('End of output from process %d in slot %d, status=%d\n\n\n'%(pid, n, status))
            sys.stdout.flush()
            os.unlink(proc_struct.stdout_filename)
            return
    assert False

def wait( ) :
    """
    Wait for one child process to exit.

    If there are no child processes, but we still think there are,
    assume each of them exited, but the exit code will be None instead
    of a number.
    """
    try :
        (pid, status) = os.wait()
    except OSError, e:
        if e.errno == errno.ECHILD :
            #
            # If there are no more child processes, everything must be done.
            # Call all the callbacks and clear them out of the list.
            #
            # You wouldn't think that this code could execute, but if
            # the user is calling os.wait() somewhere else, we might not
            # know about every process that exits.  This is the best we
            # can do.

            # You can't say 'for x in all_procs' because we will be changing
            # all_procs during the loop.
            pending_procs = [ x for x in all_procs ] 
            for x in pending_procs :
                done(x, None)
    done(pid, status)

def wait_all( ) :
    """
    Wait for all child processes (started by mrun) to exit.

    """
    while len(all_procs) > 0 :
        wait()

def _run_proc( args, env, slot ) :
    """
    fork and run a new process

    @param args:    argv[] type list of parameters
    @type  args:    list

    @param env:     envp[] type list of environment variables, or None
                    use the default from os.environ
    @type  env:     dict

    """
    global proc_count

    if env is None :
        env = os.environ
    env['proc_count'] = str(proc_count)
    output = os.environ['PDK_TMP'] + "/pdk.stdout.%d.tmp"%slot
    try :
        os.unlink(output)
    except :
        pass
    f_out = open(output,"w")
    if 0 :
        f_out.write('run_proc: ')
        for x in args :
            f_out.write('%s '%x)
        f_out.write('\n')

    f_out.flush()

    x= subprocess.Popen( args=args, stdout=f_out, stderr=subprocess.STDOUT, bufsize=0, env=env )

    f_out.close()

    proc_count = proc_count + 1

    rval = process()
    rval.pid = x.pid
    rval.slot = slot
    rval.stdout_filename = output
    rval.popen_object = x

    return rval

if __name__ == '__main__' :
    def print_count(cookie, status) :
        print "callback",cookie, status, status >> 8

    count = 0
    for x in [
        1, 3, 5,
        1, 3, 5,
        1, 3, 5,
        1, 3, 5,
        ] :
        start( [ "/bin/sleep", str(x) ], os.environ, print_count, count)
        count = count + 1
    wait_all()
