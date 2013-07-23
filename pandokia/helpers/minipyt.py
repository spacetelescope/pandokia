#
# minipyt decorators 
#

__all__ = [ 'test', 'istest', 'nottest', 'disable', 'noseguard' ]

##########
#
# Note that you might expect the user to 
#
#   from pandokia.helpers.minipyt import *
#
# so we tag every function in this file as not a test by setting __test__
# to false.

#
##########
#
# Nose compatible
#
# These look like nose decorators and use the same signalling,
# so nose/minipyt tests can be more compatible.  You can use
# these decorators with nose, and you can use nose decorators
# for these features with minipyt.
#

###
#
# This thing _is_ a test
#

def test(f) :
    f.__test__ = True
    return f

    # in case somebody calls it by the name nose uses
istest = test

test.__test__ = False

###
#
# This this is not a test
#

def nottest(f) :
    f.__test__ = False
    return f

nottest.__test__ = False

##########
#
# features that nose does not have
#

def disable(f) :
    f.__disable__ = True
    return f

disable.__test__ = False


###
#
# prevent a file running in nose
#

disable_noseguard = False

def noseguard() :
    '''
    Prevent a test file from running in nose

        import pandokia.helpers.minipyt
        pandokia.helpers.minipyt.noseguard()

    raises an exception if 'nose' in sys.modules

    This prevents importing the file if nose is also loaded.  If pandokia
    is using minipyt as the test runner, nose will not have been imported.
    If nose is in sys.modules, we assume that is because the test file
    was mistakenly run with nose.

    Presumably, this may cause you problems if you are trying to import the
    test into an interactive python.  If so, disable this function with

        import pandokia.helpers.minipyt
        pandokia.helpers.minipyt.disable_noseguard = True

'''

    if disable_noseguard :
        print "pandokia.helpers.minipyt.noseguard() disabled!"
        return

    import sys
    if 'nose' in sys.modules :
        raise Exception('Do not run these tests with nose!')

