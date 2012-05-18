import os.path
import json
import time

import pandokia.helpers.minipyt as mph
import pandokia.helpers.pycode as pycode

# software under test:
import pandokia.helpers.filecomp as filecomp

#

mph.noseguard()

@mph.test
def filecomp_t() :
    global tda
    tda = { }

    # list of files to compare
    files = [ 
            ( "test_1.txt", "diff" ) 
        ]

    # delete output files before running test
    filecomp.delete_output_files( files )

    # some data
    l = [ { 'a' : 1, 'b' : 2 }, [ 1, 2 ] ]

    # make the output file ( in directory out/ )
    f = open("out/test_1.txt","w" )
    result = json.dump( l, f, indent=4, sort_keys=True, default=str )
    f.close()

    # file comparison tool
    filecomp.compare_files( 
        # files to compare
        files,
        # name to use to construct okfile
        "okfile/" + os.path.basename(__file__) + ".test_1",
        # tda dict (to record name of okfile)
        tda
        )

@mph.test
def safe_rm() :
    with pycode.test('dne') :
        filecomp.safe_rm("does_not_exist")
        filecomp.safe_rm("does_not_exist")
        filecomp.safe_rm( [ "does_not_exist", "does_not_exist" ] )
    with pycode.test('exists') :
        open("safe_rm.tmp","w").close()
        filecomp.safe_rm("safe_rm.tmp")
        try :
            open("safe_rm.tmp","r")
        except IOError :
            pass
        else :
            assert 0, "should have had IOError"
        

@mph.nottest
def make_file_with_age( f, age ) :
    fd = open(f,"w")
    fd.write("hello\n")
    fd.close()
    t = time.time() - age
    os.utime(f, ( t, t ) )

make_file_with_age( 'times_o', 10 * 3600 )
make_file_with_age( 'times_n',  5 * 3600 )

@mph.test
def assert_file_newer() :
    with pycode.test("rel") :
        with pycode.test("is") :
            filecomp.assert_file_newer( 'times_n', 'times_o' )
        with pycode.test("not") :
            try :
                filecomp.assert_file_newer( 'times_o', 'times_n' )
            except AssertionError :
                pass
            else :
                assert 0, "should have had AssertionError"
    with pycode.test("abs") :
        with pycode.test("is") :
            filecomp.assert_file_newer( 'times_n', hours = 8 )
            filecomp.assert_file_newer( 'times_o', hours = 12 )
        with pycode.test("not") :
            try :
                filecomp.assert_file_newer( 'times_n', hours = 3 )
            except AssertionError :
                pass
            else :
                assert 0, "should have had AssertionError"

@mph.test
def assert_file_older() :
    with pycode.test("rel") :
        with pycode.test("is") :
            filecomp.assert_file_older( 'times_o', 'times_n' )
        with pycode.test("not") :
            try :
                filecomp.assert_file_older( 'times_n', 'times_o' )
            except AssertionError :
                pass
            else :
                assert 0, "should have had AssertionError"
    with pycode.test("abs") :
        with pycode.test("is") :
            filecomp.assert_file_older( 'times_o', hours = 8 )
            filecomp.assert_file_older( 'times_n', hours = 3 )
        with pycode.test("not") :
            try :
                filecomp.assert_file_older( 'times_n', hours = 8 )
            except AssertionError :
                pass
            else :
                assert 0, "should have had AssertionError"

@mph.test
def file_age() :
    n = filecomp.file_age( 'times_o' )
    print "o",n
    assert int( n / 120) == int( 10 * 3600 / 120 ), 'file age is within 2 minutes of right'
    n = filecomp.file_age( 'times_n' )
    print "n",n
    assert int( n / 120) == int(  5 * 3600 / 120 ), 'file age is within 2 minutes of right'
