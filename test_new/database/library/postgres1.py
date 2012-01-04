import d_open
import os

minipyt_test_order = 'alpha'

dbx = d_open.postgres(1)

import shared
shared.dbx = dbx

from shared import *

import csv_t
csv_t.dbx = dbx

from csv_t import *

import pandokia.helpers.minipyt as minipyt

@minipyt.test
def t020_sequence() :
    assert dbx.next('test_sequence') == 1
    assert dbx.next('test_sequence') == 2
    assert dbx.next('test_sequence') == 3
