#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

# This test runner uses nose with the pandokia plugin to execute
# tests that are in installed modules, rather than in the test
# directory.
#
# The initial motivation was to execute doctests, but in fact it
# runs any nose-runnable test that it finds.

import os
import os.path

# To run these tests, we need to know where the installed software
# is.  You might think you can import it and ask for __file__, but
# too many packages _do_ _things_ when you import them.   For example,
# pyraf changes the semantics of the import statement.  We can't allow
# the code we are testing to mess up the test environment.
#
# So, we use the import hooks to locate the stuff instead.
# Unfortunately, there is not a feature that just tells you "where
# is a.b.c?", so we have find_module_location() to provide that
# service.

import imp

def find_module_location(name, path=None) :
    if '.' in name :
        # The imp package doesn't support hierarchical names, so you
        # have to do it yourself if there is a . in the name.
        l = name.split('.',1)
        # find the top level package
        ( file, pathname, description ) = imp.find_module( l[0], path )
        if not file is None :
            file.close()
        # find the remaining packages in the directory that it was in
        return find_module_location( l[1], [ pathname ] )
    else :
        # If no . in the name, we have it on the first try.
        ( file, pathname, description ) = imp.find_module( name, path )
        if not file is None :
            file.close()
        return pathname



#
# Read the list of package/module names from the input file; make
# a list of file names where those package/modules are.

def find_locations( file ) :
    f = open( file, 'r' )
    l = [ ]
    for x in f :
        x = x.strip()
        if x == '' or x.startswith('#') :
            continue
        try :
            location = find_module_location(x)
            l.append( location ) 
        except ImportError :
            print "Cannot find module",x
            # we can't generate a test result of error because 
            # we don't know the test name
    f.close()
    return l
    pass


###
### the rest of this file is almost, but not quite, just copied from nose.py
###

# return list of command strings to use to run the test
#
# The input file that we are given contains a list of packages/modules to test.

def command( env ) :
    filename = env['PDK_FILE']
    l = find_locations( filename )
    l1 = [ ]
    # We need to add to PDK_TESTPREFIX - nose will make up a test
    # name, but it does not know about the .snout file that we are
    # looking at.
    basename = filename
    if basename.endswith(".snout") :
        basename = basename[:-len(".snout")]
    # the prefix already ends with a /
    prefix = env['PDK_TESTPREFIX'] + basename
    for location in l :
        l1.append( 'pdknose --pdk --exe --with-doctest --doctest-tests --pdktestprefix=%s %s' % ( prefix, location)  )


    return l1


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

    for location in find_locations(env['PDK_FILE']) :
        s='pdknose --pdk --exe --with-doctest --doctest-tests --pdklog='+tmpfile+' --collect-only %s' % location
        pandokia.helpers.filecomp.command(s)

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
