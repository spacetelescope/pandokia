#
# pandokia - a test reporting and execution system
#

import os
import os.path

# return command string to run the test
#
# This looks like we are not using many parameters, but most of the information
# we are passing to nose is in the environment.


def command(env):
    name = os.path.basename(env['PDK_FILE'])
    return 'pdk_python_runner minipyt %s' % name

# Maybe support disabled tests someday...


def lst(env):
    return []
