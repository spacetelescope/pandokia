#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

# This is a test runner that uses nose with the pandokia plugin.  It
# requires nose 0.11.

import os

# return command string to run the test
# pdknose is our own command to run nose with the pdk plugin.  This command
# uses the nose 0.11 feature of adding a plugin by passing it in to nose.main.
# With this, we don't have to use setuptools to install our nose plugin.
#
# The pdknose command is in the commands/ directory.
#
# This looks like we are not using many parameters, but most of the information 
# we are passing to nose is in the environment.

def command( env ) :
    return 'pdknose --pdk --with-doctest --doctest-tests %(PDK_FILE)s' % env




# return a list of tests that are in the file.  we use this
# to report disabled tests.
def list( env ) :
    # nose has --collect-only which identifies the tests, but does not run them.
    # We run nose with the same set of parameters as if we were running the
    # test, but we add --collect-only.  The result is a pandokia log file
    # that contains abbreviated test reports.  We read that log file to
    # find the test names.  (Everything except the name is an uninteresting
    # side-effect.)
    #
    # Note that the PDK_TESTPREFIX is applied by the nose plugin, not us.

    # If this function is called, it is only once per process.
    import pandokia.helpers.process as process
    import pandokia.helpers.filecomp as filecomp

    tmpfile = 'pdk.runner.tmp'
    # Do our best to make sure the file is not there already.
    try :
        os.unlink(tmpfile)
    except OSError:
        pass

    # run the command to collect the names
    # pandokia log goes to tmpfile - it is ok to used a fixed name because we
    # know that only one process can be running tests in a single directory.
    s='pdknose --pdk --with-doctest --doctest-tests --collect-only %(PDK_FILE)s' % env

    env = env.copy()
    env['PDK_LOG'] = tmpfile
    process.run_process(s.split(), env, output_file='pdknose.tmp' )

    # gather the names from pdk.log
    l = [ ]
    f=open(tmpfile,"r")
    for line in f :
        line = line.strip().split('=')
        if line[0] == 'test_name' :
            l.append(line[1])

    f.close()

    # clean up
    filecomp.safe_rm('pdknose.tmp')
    filecomp.safe_rm(tmpfile)

    # return list
    return l
