# tests of the examples doc/source/helper_json.rst


import pandokia.helpers.minipyt as mph

@mph.nottest
def mkfile(name, age) :
    pass

@mph.test
def json_string() :
    import json
    import pandokia.helpers.filecomp as filecomp

    l = [ { 'a' : 1, 'b' : 2 }, [ 1, 2 ] ]
    result = json.dumps( l, indent=4, sort_keys=True, default=str )
    print result

    ref = """
    [
        {
            "a": 1, 
            "b": 2
        }, 
        [
            1, 
            2
        ]
    ]
    """
    assert filecomp.diffjson( result, ref )

import os.path
import json
import pandokia.helpers.filecomp as filecomp

@mph.test
def json_file() :
    global tda
    tda = { }

    # list of files to compare
    files = [ 
            ( "test_1.txt", "diff", { 'rstrip' : True } ) 
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

