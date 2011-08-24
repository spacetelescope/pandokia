import sqlite3
import os

import pandokia.db_sqlite as dbx

try : os.unlink('test.db')
except : pass

open('test.db','w').close()

dbx.open_db('test.db')

import shared
from shared import *

shared.dbx = dbx
