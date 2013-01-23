.. index:: single: patterns; xml; replacing
.. index:: single: patterns; regtest; replacing

===============================================================================
Python: Replacing XML regtests with Python
===============================================================================

It is fairly easy to translate an XML stsci regest into python.  Here is an example.

An XML regtest: ::

    <!--
    ## 
    ## HEDIT - images/imutil/hedit: level 2
    ##  This test adds a new keyword to a header and compares the result to
    ## an image of expected results. Because the hedit task works on images
    ## in-place, a copy of the input image is created before running hedit,
    ## in order to preserve the original image.
    ##
    -->

    <RegTest>
    <pre-exec>
       <command>import shutil</command>
       <command>shutil.copy('m51.fits', 'm51_test2.fits')</command>
    </pre-exec>

    <title>images/imutil/hedit: test 2</title>
    <level>2</level>
    <taskname>hedit</taskname>
    <pfile>hedit_test2.par</pfile>
    <output>
      <val>
        <file>m51_test2.fits</file>
        <reference>m51_test2_ref.fits</reference>
        <comparator>image</comparator>  
        <ignorekeys>filename,date,iraf-tlm</ignorekeys>
      </val>
    </output>

    </RegTest>

Translate to python: ::

    # To reproduce the regtest functionality, use these imports:

    import pandokia.helpers.process as process
    import pandokia.helpers.filecomp as filecomp


    #
    # The old xml tests contain a single test in a <regtest> block.
    # We write that as a test in python.  The most convenient way to do
    # it is as a test function.  This works with both nose and py.test
    #

    def test_2():

        # Even though the test is named after the test function, we
        # still need a string for the test name.  We use it later.
        testname = 'test_2'

        # You need to have a tda dict for:
        #  - recording information to make FlagOK work
        #  - recording parameters to the task as attributes
        global tda
        tda = { }

        # We use the same information from the <output> section, but
        # written as a python data structure instead of xml.
        #  <output>
        #    <val>
        #      <file>m51_test2.fits</file>
        #      <reference>m51_test2_ref.fits</reference>
        #      <comparator>image</comparator>   
        #      <ignorekeys>filename,date,iraf-tlm</ignorekeys>
        #    </val>
        #  </output>

        output = [
                # one dict for each output file to compare (i.e. each <val>)
                {
                    # copy file, reference, and comparator from the XML
                    'file'      : 'm51_test2.fits',
                    'reference' : 'm51_test2_ref.fits',
                    'comparator': 'image',

                    # any other XML fields in the <val> should be put in a
                    # dict and stored in args:
                    'args'      : {
                        # fitsdiff args ignorekeys and ignorecomm take
                        # a list instead of comma separated text
                        'ignorekeys': [ 'filename', 'date', 'iraf-tlm' ],
                        'maxdiff' : .0001,
                     },

                },
                # if there are more files, list more dicts here
            ]

        # delete all the output files before starting the test
        filecomp.delete_output_files( output )

        # for <pre-exec> and <post-exec>, just write the python commands
        # directly into your test
        # 
        # <pre-exec>
        # <command>import shutil</command>
        # <command>shutil.copy('m51.fits', 'm51_test2.fits')</command>
        # </pre-exec>
        #
        import shutil
        shutil.copy('m51.fits', 'm51_test2.fits')

        # <title> and <level> don't count for anything in pandokia,
        # so ignore them

        # The old regtest runner loads the IRAF tasks for tables,
        # stsdas, images, and fitsio.  Load as many of the IRAF tasks 
        # as you need.
        #
        # Skip this section if your test does not require pyraf/iraf.
        import pyraf        # not all tests need or want pyraf
        from pyraf.iraf import tables
        from pyraf.iraf import stsdas

        # for an IRAF task, use this helper function to run it
        #
        # <taskname>hedit</taskname>
        # <pfile>hedit_test2.par</pfile>
        #
        process.run_pyraf_task( 'hedit', 'hedit_test2.par', tda=tda )

        # If you have a post-exec, put the code here

        # compare the output files - use this exact command
        filecomp.compare_files( output, ( __file__, testname ), tda = tda,)


