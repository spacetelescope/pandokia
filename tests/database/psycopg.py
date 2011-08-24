import os

import pandokia.db_psycopg as dbx

dbx.open_db('dbname=test')

dbx.db_execute('drop table if exists test_table')

import shared
from shared import *

shared.dbx = dbx
