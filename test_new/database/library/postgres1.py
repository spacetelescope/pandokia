from __future__ import absolute_import

from . import d_open
import os

minipyt_test_order = 'alpha'

dbx = d_open.postgres(1)

from . import shared
shared.dbx = dbx
from .shared import *

from . import csv_t
csv_t.dbx = dbx
from .csv_t import *

import pandokia.helpers.minipyt as minipyt

@minipyt.test
def t020_sequence() :
    assert dbx.next('test_sequence') == 1
    assert dbx.next('test_sequence') == 2
    assert dbx.next('test_sequence') == 3
