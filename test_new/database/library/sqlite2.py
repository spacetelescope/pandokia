import os

import pandokia.db_sqlite as dbx

minipyt_test_order = 'alpha'

import d_open
dbx = d_open.sqlite(0)

import csv_t
csv_t.dbx = dbx

from csv_t import *

import shared2
shared2.dbx = dbx

from shared2 import *
