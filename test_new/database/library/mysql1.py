import d_open
dbx = d_open.mysql(1)

minipyt_test_order = 'alpha'

import shared
shared.dbx = dbx

from shared import *

import csv_t
csv_t.dbx = dbx

from csv_t import *

import pandokia.helpers.minipyt as minipyt

@minipyt.test
def t020_sequence() :
    dbx.execute("drop table if exists foo")
    dbx.execute("create table foo ( n integer auto_increment, primary key ( n ), s varchar(10) )")
    c = dbx.execute("insert into foo ( s ) values ( 'x' )")
    assert c.lastrowid == 1
    c = dbx.execute("insert into foo ( s ) values ( 'x' )")
    assert c.lastrowid == 2
    c = dbx.execute("insert into foo ( s ) values ( 'x' )")
    assert c.lastrowid == 3

@minipyt.test
def t020_implicit_sequence() :
    assert dbx.next is None

