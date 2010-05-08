
# minipyt decorators 
#
# idea: make these look like nose decorators and use the same signalling,
# so nose/minipyt tests can be more compatible

def test(f) :
    f.__test__ = True
    return f

# in case somebody calls it by the name nose uses
istest = test

def nottest(f) :
    f.__test__ = False
    return f

