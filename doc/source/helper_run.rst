.. index:: single: patterns; external executables

===============================================================================
Python: Running external executables in your test
===============================================================================

There are some helper functions for running external programs.  You can
use these instead of any of the half-dozen or so variants of popen that
are in the standard library.  This interface is simpler, and it will not
be deprecated as often as the other popen variants.

``run_process`` executes a command with stdout/stderr redirected into a file: ::

    import pandokia.helpers.process as pr
    import os

    arg = [ 'ls', '-ld', '.' ]

    # run the process with arg list, using default environment and output file
    status = pr.run_process( arg )

    # explicitly read the output
    out = open('output_file','r').read()
    print "output was:"
    print out
    print "exit code is %d" % status

    # run the process, explicitly specify everything
    status = pr.run_process( arg, env=os.environ, output_file='myfile.tmp' )
    out = open('myfile.tmp','r').read()

    # just repeat the output to our own stdout
    print "output was:"
    pr.cat( [ 'myfile.tmp' ] )
    print "exit code is %d" % status

``cat`` reads each file in a list and writes the content to stdout: ::
    
    import pandokia.helpers.process as pr
    pr.cat( [ 'myfile.tmp' ] )

This is much like ``os.system("cat myfile.tmp")`` with one significant
difference:  os.system will write stdout to the same stdout that pandokia
is writing to, so the output will not appear in your test report;
``process.cat`` will write the output into the sys.stdout that the test
is using, which means that the file content will appear
in the test report.

IRAF tasks
-------------------------------------------------------------------------------

If you have Pyraf installed, you can run IRAF tasks: ::

    import pandokia.helpers.filecomp as filecomp
    import pandokia.helpers.process as process

    tda = { }

    f = open('parfile','w')
    f.write('''
    input,s,a,"dev$pix",,,Input images
    output,s,a,"foo.fits",,,Output images or directory
    verbose,b,h,no,,,Print operations performed?
    mode,s,h,ql
    ''')
    f.close()

    filecomp.safe_rm('foo.fits')

    process.run_pyraf_task('imcopy', 'parfile', output_file='foo.txt', tda=tda )

The tda dict is optional.  If you supply it, task parameters will be entered as TDAs.

This is a simplified interface for pyraf tasks.  You can also use the full
capabilities of pyraf directly.

If the task returns an error, it will raise pr.RunPyrafTaskException which contains
the values ``task`` and ``err``: ::

    except process.RunPyrafTaskException as e :
        print "task ",e.task
        print "err  ",e.err

The call may also raise any of the pyraf-related exceptions.

