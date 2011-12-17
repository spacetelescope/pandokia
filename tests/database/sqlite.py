import os

import pandokia.db_sqlite as dbx

try :
    os.unlink('sqlite.db')
except OSError :
    pass

dbx = dbx.PandokiaDB('sqlite.db')

dbx.execute('drop table if exists test_table')

import shared
shared.dbx = dbx

from shared import *

import csv_t
csv_t.dbx = dbx

from csv_t import *

