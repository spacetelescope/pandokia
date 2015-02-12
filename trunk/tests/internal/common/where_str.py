from pandokia.common import where_tuple


def test_blank() :
    r = where_tuple( [ ] )
    print "r=",r
    assert r == ('', {})

def test_a2() :
    r = where_tuple( [ ('a', 1) , ( 'b', 2 ) ] )
    print "r=",r
    assert r == ('WHERE (a = :0 ) AND (b = :1 )', {'1': '2', '0': '1'})

def test_a3() :
    r = where_tuple( [ ('a', 1) , ( 'b', 2 ), ( 'c', 3  )  ] )
    print "r=",r
    assert r == ('WHERE (a = :0 ) AND (b = :1 ) AND (c = :2 )', {'1': '2', '0': '1', '2': '3'})

def test_o1() :
    r = where_tuple( [ ('a', [ 1, 2 ] ) ] )
    print "r=",r
    assert r == ('WHERE (a = :0  OR a = :1 )', {'1': '2', '0': '1'})

def test_o2() :
    r = where_tuple( [ ('a', [ 1, 2, 3 ] ) ] )
    print "r=",r
    assert r == ('WHERE (a = :0  OR a = :1  OR a = :2 )', {'1': '2', '0': '1', '2': '3'})

def test_ao0() :
    r = where_tuple( [ ('a', [ 1, 2 ] ) , ('b', 2) ] )
    print "r=",r
    assert r == ('WHERE (a = :0  OR a = :1 ) AND (b = :2 )', {'1': '2', '0': '1', '2': '2'})

def test_ao1() :
    r = where_tuple( [ 
         ('b', 2) ,
        ('a', [ 1, 2 ] ) ,
        ] )
    print "r=",r
    assert r == ('WHERE (b = :0 ) AND (a = :1  OR a = :2 )', {'1': '1', '0': '2', '2': '2'})

def test_ao2() :
    r = where_tuple( [ 
        ('x', [ 1, 2 ] ) ,
         ('b', 2) ,
        ('a', [ '*', 2 ] ) ,
        ] )
    print "r=",r
    assert r == ('WHERE (x = :0  OR x = :1 ) AND (b = :2 ) AND (a GLOB :3  OR a = :4 )', {'1': '2', '0': '1', '3': '*', '2': '2', '4': '2'})

def test_glob_1() :
    r = where_tuple( [ ( 'a', '*' ) ] )
    print "r=",r
    assert r == ('', {})

def test_glob_2() :
    r = where_tuple( [ ( 'a', 'xx[A-Z]yy' ) ] )
    print "r=",r
    assert r == ('WHERE (a GLOB :0 )', {'0': 'xx[A-Z]yy'})

def test_glob_3() :
    r = where_tuple( [ ( 'a', 'a?b' ) ] )
    print "r=",r
    assert r == ('WHERE (a GLOB :0 )', {'0': 'a?b'})

def test_glob_4() :
    r = where_tuple( [ ( 'a', 'x*' ) ] )
    print "r=",r
    assert r == ('WHERE (a GLOB :0 )', {'0': 'x*'})

def test_glob_5() :
    r = where_tuple( [ ( 'a', '*x' ) ] )
    print "r=",r
    assert r == ('WHERE (a GLOB :0 )', {'0': '*x'})

def test_a_None() :
    r = where_tuple( [
        ( 'a', None ),
        ( 'b', 'a' ),
        ] )
    print "r=",r
    assert r == ('WHERE (b = :0 )', {'0': 'a'})

def test_o_None() :
    r = where_tuple( [
        ( 'a', [ 1, None ] ),
        ( 'b', 'a' ),
        ] )
    print "r=",r
    assert r == ('WHERE (b = :1 )', {'1': 'a', '0': '1'})

def test_bad() :
    r = where_tuple( [
        ( 'a', "Robert'); DROP TABLE Students; --" ),
        ])
    print "r=",r
    assert r == ('WHERE (a = :0 )', {'0': "Robert'); DROP TABLE Students; --"})

    
