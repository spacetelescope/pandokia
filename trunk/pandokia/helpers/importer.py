'''import an arbitrary file with an arbitrary module name
'''
import sys
import imp

def importer(modulename, filename) :

    if modulename in sys.modules :
        return sys.modules[modulename]
    f=open(filename,"r")
    save = sys.dont_write_bytecode
    try :
        sys.dont_write_bytecode = True
        m = imp.load_source( modulename, filename, f )
    finally :
        f.close()
        sys.dont_write_bytecode = save
    return m
