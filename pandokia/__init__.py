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
from .version import *
import pandokia.default_config as cfg

#
# some constants that need to be somewhere

# time_t of an event that never expires; make this bigger if you are
# still using this in 2030.
never_expires = 0x7fffffff
