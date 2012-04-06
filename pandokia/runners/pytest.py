#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

# This is a test runner that uses pytest with the pandokia plugin.  It
# requires pytest 2.1 or later.

import os

# what importable module contains our py.test plugin?  It would be nice
# if we could insert this into os.environ['PYTEST_PLUGINS'] but it is
# already too late because envgetter has already cached the original 
# values from os.environ
# plugin = 'pandokia.helpers.pytest_plugin'

# return command string to run the test pdkpytest is our own command
# to run pytest with the pdk plugin.  This command loads the plugin by
# passing it to pytest.main.  With this, we don't have to use setuptools
# to install our pytest plugin.

def command( env ) :
    # return 'py.test -p %s --pdk %s' % ( plugin, env['PDK_FILE'] ) 
    return 'pdkpytest --pdk %s' % ( env['PDK_FILE'] ) 

# return a list of tests that are in the file.  we use this
# to report disabled tests.
def list( env ) :
    # pytest has --collectonly which identifies the tests, but does
    # not run them.  We run pytest with the same set of parameters as
    # if we were running the test, but we add --collectonly.  The
    # result is a pandokia log file that contains abbreviated test
    # reports.  We read that log file to find the test names.
    # (Everything except the name is an uninteresting side-effect.)
    #
    # Note that the PDK_TESTPREFIX is applied by the pytest plugin, not
    # us.

    # If this function is called, it is only once per process.
    import pandokia.helpers.filecomp

    tmpfile = 'pdk.runner.tmp'
    # Do our best to make sure the file is not there already.
    try :
        os.unlink(tmpfile)
    except OSError:
        pass

    # run the command to collect the names
    # pandokia log goes to tmpfile - it is ok to used a fixed name because we
    # know that only one process can be running tests in a single directory.
    s='pdkpytest --pdk --pdklog='+tmpfile+' --collectonly %(PDK_FILE)s' % env

    pandokia.helpers.filecomp.command(s, env)

    # gather the names from pdk.log
    l = [ ]
    f=open(tmpfile,"r")
    for line in f :
        line = line.strip().split('=')
        if line[0] == 'test_name' :
            l.append(line[1])

    f.close()

    # clean up
    os.unlink(tmpfile)

    # return list
    return l
