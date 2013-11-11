.. index:: single: patterns; json

===============================================================================
Python: Using JSON or pprint to compare complex data structures
===============================================================================

:abstract:

    JSON or pprint can convert various complex data structures
    into printable text for user display.  Your tests can convert
    your data to a printable format and diff the results to make
    a comparison.


We have various systems that contain nested trees of lists and dicts.  You can display these
data items with python builtins.

JSON makes a very readable format, but it does not represent every
possible python object.  pprint makes a slightly less readable
format, but knows (for example) the difference between tuples and
lists.

Using json: ::

    import json

    # to a string
    s = json.dumps( mydata, indent=4, sort_keys=True, default=str )

    # to a file
    f=open("out/myfile.txt","w")
    json.dump( mydata, f, indent=4, sort_keys=True, default=str )

pprint understands python objects better, but is harder to read.

Using pprint: ::

    import pprint

    # to a string
    s = pprint.pformat( mydata, indent=4 )

    # to a file
    f=open("out/myfile.txt","w")
    pprint.pprint( mydata, stream=f, indent=4 )

Once you have the object in a string or file, you can use various diff-like tools to compare it.

This example uses difflib and json.  The reference data is a string constant in the source code. ::

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

This example creates an output file and compares to a reference file.  You can update the reference file by using the okify feature
in the gui. ::

    import os.path
    import json
    import pandokia.helpers.filecomp as filecomp

    def test_1() :
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

