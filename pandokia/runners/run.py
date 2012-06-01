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
    return env['PDK_DIRECTORY'] + '/' + env['PDK_FILE']

# Not likely to support reporting disabled tests in an external program
def list( env ) :
    return [ ]

