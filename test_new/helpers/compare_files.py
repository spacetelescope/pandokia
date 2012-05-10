import os.path
import json
import pandokia.helpers.filecomp as filecomp

def test_1() :
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
