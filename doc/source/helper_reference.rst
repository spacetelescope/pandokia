.. index:: single: patterns; xml; alternative for new tests
.. index:: single: patterns; regtest; new

===============================================================================
Python: Tests based on reference files
===============================================================================

:abstract:

    One way to write tests is to create some output files and then
    compare them to reference files.  This is often a form of
    regression test, where the reference is output from a previous
    run.

    This section describes a way to implement these tests in python
    using tools in pandokia.helpers

Basic outline
-------------------------------------------------------------------------------

You write a test based on reference files in the same way as any
other python test, except that your assertions are based on the
result of file comparisons.

Here is a basic template that works in py.test, nose, and minipyt: ::

    import pandokia.helpers.filecomp as filecomp

    def test_foo():

        # define your test name here
        testname = 'test_foo'

        # put this exact code here
        global tda
        tda = { }

        # definition of output/reference files
        output = [
            ... details described below
            ]

        # Delete all the output files before starting the test.
        filecomp.delete_output_files( output )

        # YOUR TEST CODE HERE
        open("file","w").write("something\n")

        # compare the output files - use this exact command
        filecomp.compare_files( output, ( __file__, testname ), tda = tda,)


Here is a detailed commentary: ::

    def test_foo():

        # define your test name here
        testname = 'test_foo'

The test name is used in the call to compare_files; it is used to create a unique file name that is used by the FlagOK feature. ::

        # put this exact code here
        global tda
        tda = { }

The tda is needed to report the location of the okfile.  You can also add your own attributes if you want. ::

        # definition of output/reference files
        output = [
            ... details described below
            ]

You need a list of output files, reference files, and how to peform
the comparison.  This is somewhat involved, so it is described
below. ::

        # Delete all the output files before starting the test.
        filecomp.delete_output_files( output )

Before starting the test, delete all the output files.  If the code
under test fails to produce an output file, it will be detected.
(If you don't delete the output files, your comparison may see an
old file that was left behind from a previous test run.) ::

        # YOUR TEST CODE HERE
        f = open("out/file","w")
        f.write("something\n")
        f.close()               # be sure to close the output file

Here, you would write some code that produces the output files.  This is your test. ::

        # compare the output files - use this exact command
        filecomp.compare_files( output, ( __file__, testname ), tda = tda,)

This tool compares all the files.  It raises an Exception if there
is an error or AssertionError if one of the files does not match.


Defining the list of output files - simple form
...............................................................................

If you create your output files in the directory out/, then you can use this
simple form.  Each element of the list is a tuple of ( filename,
comparator, comparator_args ).  

Your test should create the file name in the directory out/, but
list only the base name of the output file.

For example, if your test creates "out/xyzzy.fits", you can compare it to 
"ref/xyzzy.fits" using fitsdiff: ::

    output = [
        ( 'xyzzy.fits', 'fits' ),
    ]

It is often useful to pass additional parameters to fitsdiff.  List
them in a dict in the third element of the tuple: ::

    output = [
        ( 'xyzzy.fits', 'fits', { 'ignorekeys' : [ 'filename', 'date' ] } ),
    ]

If you follow the framework in this chapter, the out/ and ref/
directories will be created for you.  You will need to create your
own reference files, either by copying files into the ref/ directory
or using the FlagOK feature in the GUI.

You can mix the two styles in a single list: ::

    output = [
        ( 'xyzzy.fits', 'fits', { 'ignorekeys' : [ 'filename', 'date' ] } ),
        ( 'plugh.fits', 'fits' ),
        ( 'plover.fits', 'fits' ),
    ]


Defining the list of output files - complex form
...............................................................................

The simple form requires a certain directory structure for your
output and reference files.  If you cannot adhere to that requirement,
you can give a more detailed definition: ::

    output = [
            {
                'file'      : 'A.fits',         # the name of the output file
                'reference' : 'A_ref.fits',     # the name of the reference file
                'comparator': 'image',          # the comparator to use

                # additional args to the comparator
                'args'      : { 
                    'ignorekeys': [ 'filename', 'date', 'iraf-tlm' ],
                 },

            },
    ]

Available Comparators
-------------------------------------------------------------------------------

binary
......................................................................

This comparator checks that the files contain identical byte streams.
It takes no additional args. ::

    output = [
        ( 'xyzzy', 'binary' ),
    ]

diff
......................................................................

This comparator uses difflib to make a unified diff of two text files.
This comparator reads both entire files into memory. ::

    output = [ 
        ( 'xyzzy.txt', 'diff' ),
    ]

There is one optional parameter:

    * rstrip (True/False) 

        removes trailing white space from each line before the comparison

rstrip is useful if you might use json.dump() or pprint.pprint()
to write out a more complex python data structure to your file.  In
some cases, json will write trailing spaces that are not significant. ::

    output = [ 
        ( 'xyzzy.txt', 'diff', { 'rstrip' : True } ),
    ]



fits
......................................................................

This runs fitsdiff to compare the files. ::

    output = [ 
        ( 'xyzzy.fits', 'fits', { 'maxdiff' : 1e-5 } ),
    ]

Additional arguments are :

    * maxdiff (float)

        This is the fitsdiff maxdiff number specified by ``fitsdiff -d``

    * ignorekeys (list)

        This is a list of header keywords that are ignored.  They are passed to ``fitsdiff -k``.

    * ignorecomm (list)

        This is a list of header keywords whose comments are ignored.  They are passed to ``fitsdiff -c``.

These additional arguments are the same as used in the stsci XML
regtest system, but the lists are specified as python lists like [
'a', 'b' ] instead of as a single string like 'a,b'


text
......................................................................

This is the text comparison from the stsci XML regtest system.  It
does not make especially interesting diffs, but is has facilities
to ignore various patterns in the text. ::

    output = [
        ( 'xyzzy.txt', 'text', { 'ignore_wstart' : [ 'plugh', 'plover' ]  } ),
    ]

Additional arguments are :

    * ignore_wstart (list)

        words that start with this text are ignored

    * ignore_wend (list) 

        words that start with this text are ignored

    * ignore_regexp (list)

        this regex is ignored

    * ignore_date (True/False)

        patterns that look like a date/time stamp are ignored; the
        system contains a rather elaborate regex to recognize many
        date formats

All this ignoring is performed by translating regular expression
matches to the value " IGNORE ".


user-defined comparators
......................................................................

You can provide your own comparison function before you call filecomp.compare_files(). ::

    filecomp.file_comparators['mycmp'] = my_function

    def test_1() :
        ...
        filecomp.compare_files( ... )


See the docstring for pandokia.helpers.filecomp.cmp_example for a definition of the
interface to your comparator function.


