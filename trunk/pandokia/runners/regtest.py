#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import platform
windows = platform.system() == 'Windows'

# test runner for IRAF/PyRAF based tests used by STScI OED/SSB group 
# This is likely of little interest to you.

if windows :
    def run_internally(env) :
        f = open(env['PDK_LOG'],"a")

        # construct the name the same way that shunit2 does
        name = env['PDK_TESTPREFIX'] + env['PDK_FILE']
        if name.endswith('.xml') :
            name = name[:-4]
        f.write("name=%s\n"%name)

        f.write("status=D\nlog=stsci_regtest not available on Windows\nEND\n\n")
        f.close()

    def command(env) :
        return None

else :
    # returns a command to run the test
    def command( env ) :
        # arg is not used, but shows up in ps
        return 'pdk_stsci_regress %s'%env['PDK_FILE']


# returns a list of tests in the file
# Easy for regtest because there is only one test in the file, and it is named
# after the file.
def list( env ) :
    fn = env['PDK_FILE']
    prefix = env['PDK_TESTPREFIX']
    if fn.endswith(".xml") :
        fn = fn[:-4]
    # the prefix ends with a /, so we don't need to add one
    fn = prefix+fn
    return [ fn ]
