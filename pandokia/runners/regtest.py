#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

# test runner for IRAF/PyRAF based tests used by STScI OED/SSB group 
# This is likely of little interest to you.

# returns a command to run the test
def command( env ) :
    return 'pdk_stsci_regress'

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
