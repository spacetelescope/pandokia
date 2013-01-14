#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

# This is a test runner that 

import os
import os.path

# return command string to run the test
#
# This looks like we are not using many parameters, but most of the information 
# we are passing to nose is in the environment.

def command( env ) :
    name=os.path.basename(env['PDK_FILE'])
    if name.endswith('.py') :
        name = name[:-3]
        print name
    else :
        raise AssertionError('pycode test %s: python file names must end .py' %env['PDK_FILE'])
    return 'python -c "import %s as t; t.pycode(1)"'%name

# pycode tests runs are procedural, with the test names generated as
# needed.  Every pycode test author would have to write special code to
# report disabled tests.  Maybe we come back to this.
def list( env ) :

    return [ ]
