from __future__ import absolute_import
import os

import pandokia.db_sqlite as dbx

minipyt_test_order = 'alpha'

from . import d_open
dbx = d_open.sqlite(0)

from . import csv_t
csv_t.dbx = dbx
from .csv_t import *

from . import shared2
shared2.dbx = dbx
from .shared2 import *
