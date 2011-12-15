#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

"""
bug: put a doc string here
describe pandokia.helpers, pandokia.runners

describe pandokia a little
"""

__version__ = "1.0"

# this looks a little strange, but we are contemplating support for
# multiple configurations; that would go here.
import pandokia.config as cfg

#
# some constants that need to be somewhere

# time_t of an event that never expires; make this bigger if you are
# still using this in 2030.
never_expires = 0x7fffffff

