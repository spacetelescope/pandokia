import pandokia.helpers.minipyt as minipyt
minipyt.noseguard()

import pprint

# The tests in this file are all named t000_something so that they happen
# in the specified order
minipyt_test_order = 'alpha'

# here is the data we are going to insert into the table
data_set = [
        ( 'a', 'b', 1 ),
        ( 'a', 'c', 2 ),
        ( 'aaa', 'bbb', 111 ),
    ]
data_set = sorted(data_set)

print "sample data set"
for x in data_set :
    print x

@minipyt.test
def t000_create() :
    dbx.execute('create table test_table ( a varchar(100), b varchar(100), c integer )')
    dbx.execute('create index test_table_index on test_table ( a )')

@minipyt.test
def t004_insert():
    print "insert"
    for x in data_set :
        dbx.execute( 'insert into test_table ( a, b, c ) values ( :1, :2, :3 )', x)
    dbx.commit()

@minipyt.test
def t005_select_1():
    c = dbx.execute( 'select a, b, c from test_table where a = :1 and b = :2', ( 'a', 'b' ))
    l = [ x for x in c ]
    print 'result',l
    assert l == [ ( 'a', 'b', 1 ) ]

@minipyt.test
def t005_select_2():
    c = dbx.execute( 'select a, b, c from test_table order by a asc, b asc, c asc', None )
    l = [ x for x in c ]
    print 'result',l
    print "expect",data_set
    assert l == data_set

@minipyt.test
def t010_where_1() :
    # list, non-list for field
    # AND in multiple fields
    # AND in additional text
    where_text, where_dict = dbx.where_dict( [
            ('first', '1'),
            ('second', '2'),
            ('third', [ '3a', '3b', '3c' ] ),
        ], 
        'X = 1' 
        )

    print "where_text:",where_text
    print "where_dict:",pprint.pprint(where_dict)

    s = eat_dup_space(where_text.strip())
    assert s == 'WHERE ( first = :0 ) AND ( second = :1 ) AND ( third = :2 OR third = :3 OR third = :4 ) AND X = 1'
    assert where_dict == {'1': '2', '0': '1', '3': '3b', '2': '3a', '4': '3c'}


@minipyt.test
def t010_where_blank() :
    # blank list turns into no-op
    where_text, where_dict = dbx.where_dict( [ ] )
    print "where_text:",where_text
    print "where_dict:",pprint.pprint(where_dict)
    assert where_text.strip() == ''
    assert where_dict == { }

@minipyt.test
def t010_where_eat_wild() :
    # wild card of * turns in to nop
    where_text, where_dict = dbx.where_dict( [ ( 'a', '*' ) ] )
    print "where_text:",where_text
    print "where_dict:",pprint.pprint(where_dict)
    assert where_text.strip() == ''
    assert where_dict == { }

@minipyt.test
def t010_where_eat_wild_2() :
    # all wild card that have no effect turn into nop
    where_text, where_dict = dbx.where_dict( [ ( 'a', [ '*', '%' ] ), ('b', None ) ] )
    print "where_text:",where_text
    print "where_dict:",pprint.pprint(where_dict)
    assert where_text.strip() == ''
    assert where_dict == { }

@minipyt.test
def t010_where_wild() :
    where_text, where_dict = dbx.where_dict( [ ( 'a', '*' ) ] )
    print "where_text:",where_text
    print "where_dict:",pprint.pprint(where_dict)
    assert where_text.strip() == ''
    assert where_dict == { }
    
@minipyt.test
def t010_where_glob_1() :
    for x in [ '?', '[', '*' ] :
        try :
            where_text, where_dict = dbx.where_dict( [ ( 'a', 'a%sa'%x ) ] )
        except AssertionError :
            pass
        else :
            assert 0, "Expected assertion error from char %s"%x

@minipyt.test
def t030_query_with_where():
    l = [ ( 'a', 'a' ), ( 'b', 'b' ) ] 
    where_text, where_dict = dbx.where_dict( l )

    cur = dbx.execute( "select a, b, c from test_table %s"%where_text, where_dict )
    l1 = grab_result(cur)

    assert l1 == [('a', 'b', 1)]

@minipyt.test
def t030_query_with_where_2():
    l = [ ( 'a', 'a' ), ( 'b', '*' ) ] 
    where_text, where_dict = dbx.where_dict( l )

    cur = dbx.execute( "select a, b, c from test_table %s"%where_text, where_dict )
    l1 = grab_result(cur)

    assert l1 == [('a', 'b', 1), ('a', 'c', 2)]

@minipyt.test
def t040_rollback() :
    c = dbx.execute("select count(*) from test_table")
    count_before = c.fetchone()[0]

    dbx.execute("insert into test_table ( a, b) values ('x', 'y')")
    dbx.rollback()

    c = dbx.execute("select count(*) from test_table")
    count_after  = c.fetchone()[0]

    assert count_before == count_after

@minipyt.test
def t99_table_usage_runs() :
    print dbx.table_usage()

@minipyt.test
def t99_explain_query_runs() :
    print dbx.explain_query('select a,b from test_table where a = :1',( 'a', ) )


# trim all instances of multiple spaces down to a single space
@minipyt.nottest
def eat_dup_space(s) :
    while '  ' in s :
        s = s.replace('  ',' ')
    return s

# get the results from a database cursor into a sorted list
# (sorted so we don't have to worry about db collation)
@minipyt.nottest
def grab_result(cur) :
    l1 = [ ]
    for x in cur :
        l1.append( x )
    return sorted(l1)
