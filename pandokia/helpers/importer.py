'''import an arbitrary file with an arbitrary module name
'''
import sys

from ..common import load_source



def importer(modulename, filename):

    if modulename in sys.modules:
        return sys.modules[modulename]
    f = open(filename, "r")
    save = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        m = load_source(modulename, filename, f)
    finally:
        f.close()
        sys.dont_write_bytecode = save
    return m
