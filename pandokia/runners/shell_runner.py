#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

# test runner that runs shell scripts - this is primarily an example of how
# to add a new test runner, though in principle you could use it for real
# tests.
#
# shell_runner runs a shell script.  The basename of the file is the name
# of the test.  The exit status of the script determines the test result.
#
# pdk_shell_runner is a shell script that performs the test.  We are not
# passing any parameters to it because it gathers them all from the environment.
# See the script source in commands/pdk_shell_runner.
#
# 

# returns a command to run the test
def command( env ) :
    return 'pdk_shell_runner'

# returns a list of tests in the file
#
# Since there is only one test in a shell_runner file, we make a list
# containing only one name.
def list( env ) :
    fn = env['PDK_FILE']
    prefix = env['PDK_TESTPREFIX']
    if fn.endswith(".sh") :
        fn = fn[:-3]
    # the prefix already ends with a /
    fn = prefix+fn
    return [ fn ]
