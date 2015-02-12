#
# pandokia - a test reporting and execution system
#

import os
import os.path

####################
#
# This part is used as the runner in pdkrun as the runner "maker"
#

# return command string to run the test
#
# This looks like we are not using many parameters, but most of the information 
# we are passing is in the environment.

def command( env ) :
    return 'python -m pandokia.runners.maker'

# Not likely to support reporting disabled tests in a compiled external program
def list( env ) :
    return [ ]

####################
#
# this part is used as a stand-alone program that compiles/runs the test
#

'''

maker reads the source file of a test to find commands to compile and
execute the test program.  You need this for compiled languages like C.

Put the commands in a comment like this at the top of the file:

C:

/*
>>> python_command
    any platform
$ unix shell command
    linux/unix only
> windows cmd command
    windows only
*/

Fortran:

C >>> python command
C $ shell command (linux)
C > shell command (windows cmd)

There will be an environment variable PDK_MAKER that states the name
of a directory of possibly useful files:  include files, libraries,
whatever that may be helpful.  For example, when using FCTX, you
need pandokia_fct.h, which can be found in $PDK_MAKER.

'''

if __name__ == '__main__' :
    import sys
    import re
    import platform

    # group 0 is the tag that comes before the command
    #   $ > >>>
    # group 1 is the actual tag
    command_re = re.compile('[^ \t]{0,5}[ \t]*([>\$]+)[ \t]*(.*$)')

    #
    windows = platform.system() == 'Windows'

    #
    print "MAKER HERE"

    # 
    d = os.path.dirname(__file__) + '/maker'
    os.environ['PDK_MAKER']  = d

    f = open(os.environ['PDK_FILE'],'r')
    line_count = 0
    lc_expire = 0
    total_status = 0
    while 1 :
        line = f.readline()
        if line == '' :
            break
        line_count += 1
        g = command_re.match(line)
        if g :
            lc_expire = 0
            tag = g.group(1)
            cmd = g.group(2)
            print line_count, tag, cmd
            if tag == '>>>' :
                exec(cmd)
            elif tag == '$' :
                if not windows :
                    status = os.system(cmd)
                    print "status=",status
                    total_status |= status
            elif tag == '>' :
                if windows :
                    status = os.system(cmd)
                    print "status=",status
                    total_status |= status
            else :
                print "Tag not recognized!"
        lc_expire += 1
        if lc_expire > 10 :
            break

    if total_status :
        sys.exit(1)
    else :
        sys.exit(0)
