'''import an arbitrary file with an arbitrary module name
'''
import sys
import importlib.util
import importlib.machinery

# replacement for imp.load_source() from https://docs.python.org/dev/whatsnew/3.12.html#imp
# see similar usage in steuermann config.py
def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module

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
