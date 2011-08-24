import pandokia.helpers.minipyt as minipyt
minipyt.noseguard()


data_set = [
        ( 'a', 'b', 1 ),
        ( 'a', 'c', 2 ),
        ( 'AAA', 'BBB', 111 ),
    ]
data_set = sorted(data_set)

print "sample data set"
for x in data_set :
    print x

@minipyt.test
def t00_create() :
    dbx.db_execute('create table test_table ( a varchar(100), b varchar(100), c integer )')

@minipyt.test
def t01_insert():
    print "insert"
    for x in data_set :
        dbx.db_execute( 'insert into test_table ( a, b, c ) values ( :1, :2, :3 )', x)

@minipyt.test
def t02_select_1():
    c = dbx.db_execute( 'select a, b, c from test_table where a = :1 and b = :2', ( 'a', 'b' ))
    l = [ x for x in c ]
    print 'result',l
    assert l == [ ( 'a', 'b', 1 ) ]

@minipyt.test
def t02_select_2():
    c = dbx.db_execute( 'select a, b, c from test_table order by a, b asc', None )
    l = [ x for x in c ]
    print 'result',l
    assert l == data_set

