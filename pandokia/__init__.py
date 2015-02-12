#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

"""
bug: put a doc string here
describe pandokia.helpers, pandokia.runners

describe pandokia a little
"""

import os

# setup.py searches for this exact form of the next line:
__version__ = "1.3.10"

# this looks a little strange, but we are contemplating support for
# multiple configurations; that would go here.
if 'PDK_CONFIG' in os.environ :
    import pandokia.helpers.importer as i
    cfg = i.importer( 'pandokia.config', os.environ['PDK_CONFIG'] )
else :
    import pandokia.default_config as cfg

#
# some constants that need to be somewhere

# time_t of an event that never expires; make this bigger if you are
# still using this in 2030.
never_expires = 0x7fffffff

