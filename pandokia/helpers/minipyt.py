#
# minipyt decorators 
#

__all__ = [ 'test', 'istest', 'nottest', 'disable' ]

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


