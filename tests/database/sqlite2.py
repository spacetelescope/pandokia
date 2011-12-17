import os

import pandokia.db_sqlite as dbx

dbx = dbx.PandokiaDB('sqlite.db')

import csv_t
csv_t.dbx = dbx

from csv_t import *

