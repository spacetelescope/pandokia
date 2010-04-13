
# minipyt decorators 
#
# idea: make these look like nose decorators and use the same signalling,
# so nose/minipyt tests can be more compatible

def istest(f) :
    f.__test__ = True
    return f

test = istest

def nottest(f) :
    f.__test__ = False
    return f

