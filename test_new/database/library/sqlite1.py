import os

import d_open

import pandokia.db_sqlite as dbx

minipyt_test_order = 'alpha'

dbx = d_open.sqlite(1)

dbx.execute('drop table if exists test_table')

import shared
shared.dbx = dbx

from shared import *

import csv_t
csv_t.dbx = dbx

from csv_t import *

import pandokia.helpers.minipyt as minipyt

@minipyt.test
def t020_sequence() :
    dbx.execute("create table foo ( n integer primary key, s varchar );")
    c = dbx.execute("insert into foo ( s ) values ( 'x' )")
    assert c.lastrowid == 1
    c = dbx.execute("insert into foo ( s ) values ( 'x' )")
    assert c.lastrowid == 2
    c = dbx.execute("insert into foo ( s ) values ( 'x' )")
    assert c.lastrowid == 3

@minipyt.test
def t020_implicit_sequence() :
    assert dbx.next is None

