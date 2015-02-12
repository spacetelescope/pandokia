'''
pandokia.helpers.filecomp - a general interface for intelligently
    comparing two files

contents of this module:

    delete_output_files( clist ) 
    compare_files( clist, okroot=None, tda=None )
        a function to compare output files to reference files

    file_comparators[ ]
        a dict that converts comparator names to a function that performs
        the comparison.  This is here so you can add your own comparators.

    cmp_example( )
        an example of how to make your own comparison function; this is
        not actually used, but you can look at the docstring.

    ensure_dir( name )
        make sure directory exists, creating if necessary.  (There is no
        function like this in the python library.)

    safe_rm( name )
    safe_rm( [ name, name, ... ] )
        remove files, ignoring OSError

    file_age( name ) 
        return how long ago a file was modified

    assert_file_newer( file1, file2 )
    assert_file_newer( file1, file2 )
    assert_file_older( file1, days=0, hours=0 ) :
    assert_file_older( file1, days=0, hours=0 ) :
        compare files modification times to other files or relative times

    diffjson( s1, s2 )
        show a unified diff of two json strings - does a string diff,
        but ignoring trailing whitespace

            
'''

__all__ = [ 'file_comparators', 'compare_files', 'ensure_dir' ]

import os
import re
import sys
import difflib
import traceback
import glob

import pandokia.helpers.process as process

###
### Various file comparisons
###
### true = same
### false = different
###

def cmp_example( the_file, reference_file, msg=None, quiet=False, attr_prefix=None, tda=None, tra=None, **kwargs ) :
    '''
    This is an example of how to write your own file comparison function.
    See also the source code.

        the_file is the input file that we are testing.

        reference_file is the reference file that we already know to be correct.

        quiet is true to suppress all output.  Not all comparison functions
        are capable of this, because some of them use external packages
        (e.g. fitsdiff) that are too chatty.

        kwargs is a place for optional args that may influence how the
        comparison takes place.  For example, you might use this to specify
        to ignore case, to compare numbers with a certain tolerance, or to
        ignore certain fields in the file.

    This function returns True if the files are the same (according to the
    comparison parameters given).  Return False otherwise.  Raise an exception
    if some exceptional condition prevents you performing the comparison.

    Define a function like this, then add it to the dictionary with a commmand
    like:
        pandokia.helpers.filecomp.file_comparators['example'] = cmp_example

    You can then use it by calling file_compare()

    '''
    if ( not quiet ) and ( header_message is not None ) :
        sys.stdout.write(header_message)

    safe_rm('filecomp.tmp')

    # cmp command - only works on unix-like systems
    r = process.run_process( [ "cmp", the_file, reference_file ],  output_file="filecomp.tmp" )

    process.cat('filecomp.tmp')
    safe_rm('filecomp.tmp')

    if r == 1:
        if not quiet :
            sys.stdout.write("file match error: %s\n"%the_file)
        return False
    elif r != 0:
        raise OSError("cmp command returned error status %d"%r)
    return True


###
### binary file compare
###

def cmp_binary( res, ref, msg=None, quiet=False, attr_prefix=None, tda=None, tra=None, **kwargs ) :
    '''
    cmp_binary - a byte-for-byte binary comparison; the files must
        match exactly.  No kwargs are recognized.
    '''
    try :
        f1 = open(res, 'r')
    except :
        print "cannot open result file:",res
        raise

    try :
        f2 = open(ref,'r')
    except :
        f1.close()
        print "cannot open reference file",ref
        raise

    # pick the length out of the stat structure
    s1 = os.fstat(f1.fileno())[6]
    s2 = os.fstat(f2.fileno())[6]

    if s1 != s2 :
        print "files are different size:"
        print "    %s %d"%(res,s1)
        print "    %s %d"%(ref,s2)
        f1.close()
        f2.close()
        return False

    blksize=65536
    offset=0
    while 1 :
        d1 = f1.read(blksize)
        d2 = f2.read(blksize)

        if d1 == '' and d2 == '' :
            f1.close()
            f2.close()
            return True

        if d1 == d2 :
            continue

        # bug: be nice to show the offset where they are different
        print "files are different: ",res,ref
        f1.close()
        f2.close()
        return True

    # not reached

###
### FITS - Flexible Image Transport System
###

#
# This uses fitsdiff from STSCI_PYTHON, an astronomical data analysis package
#
# http://www.stsci.edu/institute/software_hardware/pyraf/stsci_python
#

def cmp_fits( the_file, reference_file, msg=None, quiet=False, attr_prefix=None, tda=None, tra=None, maxdiff=None, ignorekeys=None, ignorecomm=None ) :
    '''
    cmp_fits - compare fits files.  kwargs are passed through to fitsdiff
    '''

    if quiet:
        sys.stdout.write("(sorry - fitsdiff does not know how to be quiet)\n")

    safe_rm('filecomp.tmp')

    # fitsdiff does not know how to distinctively report that a reference
    # file was missing (it gives the same status as for a failed match)
    if not os.path.exists( reference_file ) :
        e = IOError( 'No reference file: %s' % reference_file )
        print e
        raise e

    # run fitsdiff externally - if you call it directly, it does
    # weird things to the tests. (This will change with Erik's new
    # fitsdiff API, but it isn't here yet.)

    arglist = [ 'fitsdiff' ] 
    if maxdiff is not None :
        arglist  = arglist + [ '-d', str(maxdiff)    ]
    if ignorekeys is not None :
         arglist = arglist + [ '-k', ','.join(ignorekeys) ]
    if ignorecomm is not None :
        arglist  = arglist + [ '-c', ','.join(ignorecomm) ]
    arglist = arglist + [ the_file, reference_file ]

    print arglist
    status = process.run_process( arglist, output_file="filecomp.tmp" )

    process.cat('filecomp.tmp')
    safe_rm('filecomp.tmp')

    if status == 0 :
        return True
    elif status == 1 :
        return False
    else :
        raise Exception("fitsdiff error - exited %d"%status)

###
### text comparison
###

cmp_text_timestamp = None

def cmp_text_assemble_timestamp() :
    # This module assembles regular expressions for many of the common
    # date specification formats we find in our data files. It includes
    # the pieces from which such dates are constructed for easy expansion.
    # 
    # Created by RIJ, Jan 26 2006
    # Modified for use with the regtest software by VGL, Jun 1 2006
    # copied into pandokia.helpers May 2010

    # bug: This should really be 1) a list/dict/whatever that can be updated,
    # 2) dynamically generated as needed.  In fact, I just copied this out
    # of stsci_regtest and tweaked it a bit to use it here.

    #String specifications of the pieces
    Dow = '(Sun|Mon|Tue|Wed|Thu|Fri|Sat)'
    Mon ='(Jan|Feb|Mar|Apr|May|Jun' + \
              '|Jul|Aug|Sep|Oct|Nov|Dec)'
    #Numeric specifications of the pieces
    MN = '(0[1-9]|1[0-2])'
    DD = '([ 0][1-9]|[12][0-9]|3[01])'
    HH = '([01][0-9]|2[0-3])'
    MM = '([0-5][0-9])'
    SS = '([0-5][0-9])'
    TZ = '(HS|E[SD]T)'
    YYYY = '(19|20[0-9][0-9])'
    #Specification of separators
    sep = '( |:|-)'


    #Date specifications constructed from the pieces
    Date1 = Dow+sep+Mon+sep+DD+sep+HH+sep+MM+sep+SS+sep+TZ+sep+YYYY
    Date2 = Dow+sep+HH+sep+MM+sep+SS+sep+DD+sep+Mon+sep+YYYY
    Date3 = Mon+sep+DD+sep+HH+sep+MM
    Kdate = '^#K DATE       = '+YYYY+sep+MN+sep+DD
    Ktime = '^#K TIME       = '+HH+sep+MM+sep+SS

    #Any common datespec
    #(Sorry, Kdate/Ktime are not included because it overflows the
    #named-group limit of 100)

    global cmp_text_timestamp
    cmp_text_timestamp = "%s|%s|%s"%(Date1,Date2,Date3)


# This was copied out of the ASCII comparison in the old regtest code.
# It could probably make use of the standard python diff library 
# instead.

def cmp_text( the_file, reference_file, msg=None, quiet=False, attr_prefix=None, tda=None, tra=None, **kwargs ) :

    '''
    cmp_text - compare files as text

    kwargs are:
        ignore_wstart=xxx   ignore words that start with this pattern
        ignore_wend=xxx     ignore words that end with this pattern
        ignore_regexp=xxx   ignore this regular expression
        ignore_date=true    ignore various recognized date formats

    ignored patterns are replaced with ' IGNORE '
    '''

    diffs = [ ]
    ignore = [ ]
    ignore_raw = { }
    files_are_same = True

    for val in kwargs.get('ignore_wstart',[]):
        if ignore_raw.has_key('wstart'):
            ignore_raw['wstart'].append(val)
        else:
            ignore_raw['wstart']=[val]
        pattern=r'\s%s\S*\s'%val
        ignore.append(pattern)

    for val in kwargs.get('ignore_wend',[]):
        if ignore_raw.has_key('wend'):
            ignore_raw['wend'].append(val)
        else:
            ignore_raw['wend']=[val]
        pattern=r'\s\S*%s\s'%val
        ignore.append(pattern)

    for val in kwargs.get('ignore_regexp',[]):
        ignore_raw['regexp']=val
        ignore.append(val)

    if kwargs.get('ignore_date',False):
        ignore_raw['date']=True
        if cmp_text_timestamp is None :
            cmp_text_assemble_timestamp()
        ignore.append(cmp_text_timestamp)

    #Compile them all into a regular expression
    if len(ignore) != 0:
        ignorep=re.compile('|'.join(ignore))
    else:
        ignorep = None

    th=open(the_file)
    rh=open(reference_file)

    test=th.readlines()
    ref=rh.readlines()

    th.close()
    rh.close()

    if len(test) != len(ref):
        #Files of different sizes cannot be identical
        diffs=[('%d lines'%len(test),'%d lines'%len(ref))]
        files_are_same = False

    else:
        for i in range(len(ref)):
            #This may be slow, but it's clean
            if ignorep is not None:
                tline=ignorep.sub(' IGNORE ', test[i])
                rline=ignorep.sub(' IGNORE ', ref[i])
            else:
                tline=test[i]
                rline=ref[i]
            if tline != rline:
                files_are_same = False
                diffs.append((tline,rline))

    if files_are_same :
        return True

    # If we get this far, the files are different.  If quiet, it is
    # sufficient to know that they are different, so we return.
    if quiet :
        return False

    # Otherwise, we speak in detail about the comparison.
    if msg is not None :
        sys.stdout.write("%s\n",msg)

    fh=sys.stdout

    fh.write("\n")
    fh.write("Text Comparison\n")
    fh.write("Test file:      %s\n"%the_file)
    fh.write("Reference file: %s\n"%reference_file)
    fh.write("\n")
    if len(ignore_raw) > 0:
        fh.write("Patterns to ignore: \n")
        for k in ignore_raw:
            fh.write('  %s: %s\n'%(k,ignore_raw[k]))
    fh.write('\n')
    fh.flush()

    fwidth = max(len(the_file),len(reference_file))
    
    for tline,rline in diffs:
        fh.write("%-*s: %s\n"%(fwidth,the_file,tline.rstrip()))
        fh.write("%-*s: %s\n"%(fwidth,reference_file,rline.rstrip()))
        fh.write("\n")
    fh.flush()

    return False

###
### use difflib to make a unified diff
###

# diff two files

def cmp_diff( fromfile, tofile, msg=None, quiet=False, attr_prefix=None, tda=None, tra=None, rstrip=False, **kwargs ) :

    fromlines = open(fromfile, 'U').readlines()
    tolines = open(tofile, 'U').readlines()
    return difflist(fromlines, tolines, fromfile, tofile, quiet, msg, rstrip=rstrip)

# common code to perform/display results from the diff

def difflist( fromlines, tolines, fromfile=None, tofile=None, quiet=False, msg=None, addnl=None, rstrip=False ) :
    if rstrip :
        fromlines  = [ x.rstrip() for x in fromlines  if x != '' ]
        tolines    = [ x.rstrip() for x in tolines    if x != '' ]
    diff = difflib.unified_diff(fromlines, tolines, fromfile, tofile, n=5)
    diff = list(diff)
    if len(diff) :
        if not quiet :
            if msg :
                sys.stdout.write(msg)
            if addnl :
                for x in diff :
                    sys.stdout.write(x)
                    sys.stdout.write(addnl)
            else :
                sys.stdout.writelines(diff)
            sys.stdout.write('========\n')
        return False
    else :
        return True

# compare the two json string representations - from strings in memory, not from files

def diffjson( found, expected ) :
    '''diff two json strings'''
    found    = found.split()
    expected = expected.split()
    return difflist( found, expected, fromfile="found", tofile="expected", rstrip=True )

###
### end of format-specific file comparison functions
###


###
### Here are the built-in comparisons available; add your own if necessary
###

file_comparators = {
    'binary':       cmp_binary,
    'diff':         cmp_diff,
    'fits':         cmp_fits,
    'text':         cmp_text,

    # compatibility with old regtest
    'image':        cmp_fits,
}

###
###
###

def update_okfile(okfh, name, ref):
    
    okfh.write("%s %s\n"%(os.path.abspath(name),
                          os.path.abspath(ref)))

###
### compare a single file
###
    
def check_file( name, cmp, ref=None, msg=None, quiet=False, 
                cleanup=False, okfh=None, attr_prefix=None, tda=None, tra=None, **kwargs ) :
    """
    status = check_file( name, cmp, msg=None, quiet=False, 
                         cleanup=False, okfh=None, tda=None, tra=None,
                         **kwargs )

    name = file to compare

    cmp = comparator to use

    ref = file to compare against. If None, it lives in a ref/ dir
           under the dir containing the file to compare

    cleanup=True: delete file "name" if comparison passes

    okfh is a file-like object to write the okfile information; it must
        have a write() method.  If None, no okfile is written.

    msg, quiet, **kwargs: passed to individual comparators

    Returns True if same
    Raises AssertionError if different

    """
    #Make sure we have a comparator
    if not cmp in file_comparators :
        raise ValueError("file comparator %s not known"%str(cmp))

    #Do the comparison
    try:
        r = file_comparators[cmp](name, ref, msg=msg, quiet=quiet, attr_prefix=attr_prefix, tda=tda, tra=tra, **kwargs )
    #Catch exceptions so we can update the okfile
    except Exception:
        if okfh:
            update_okfile(okfh, name, ref)
        raise

    #Clean up file that passed if we've been asked to
    if r :
        if cleanup:
            safe_rm(name)

    #Update the okfile if the test failed
    else:
        if okfh:
            update_okfile(okfh, name, ref)

        #Last of all, raise the AssertionError that defines a failed test
        raise(AssertionError("files are different: %s, %s\n"%(name,ref)))

    #and return the True/False (Pass/Fail) status
    return r


###
### a file comparator that does everything you need to check several
### output files in a single test.  (but not yet with all the options of
### compare_file)
###

# the user gives us a list of files to compare.  There are two ways
# to specify them; this function normalizes them into a single
# representation.
def _normalize_list( l ) :
    for x in range(len(l)) :
        data = l[x]
        if isinstance(data,tuple) :
            newdata = { }
            newdata['output']       = 'out/' + data[0]
            newdata['reference']    = 'ref/' + data[0]
            newdata['comparator']   = data[1]
            if len(data) > 2 :
                newdata['args']   = data[2]

            l[x] = newdata
            data = newdata

        if not 'args' in data :
            data['args']   = { }

        if 'file' in data :
            data['output'] = data['file']
            del data['file']

        ensure_dir( os.path.dirname(data['output'   ]) )
        ensure_dir( os.path.dirname(data['reference']) )

def delete_output_files( l ) :
    '''Remove all the output files in a list intended for compare_files

Use this at the start of a test to ensure that none of your output
files already exist (so old files cannot mistakenly cause the test
to pass), then use compare_files() at the end of your test.

'''
    _normalize_list( l )
    for x in l :
        safe_rm(x['output'])

def compare_files( clist, okroot=None, tda=None, tra=None, cleanup=True ):
    '''
        clist is a tuple of (filename, comparator, args) 
            filename is the name of a file in the directory out/; it is
                compared to a file of the same name in the directory ref/,

            comparator is the name of the comparator to use.  The default
                system has 'text', 'binary', and 'fits'.

            args is a dict of keyword args to pass to comparator
                function, or None.  You may omit args if it is not needed.

        okroot is the base name of the okfile.  If present, an okfile named
            okroot+'.okfile' is created.  Normally, you would use the
            basename of the current file plus the test name.

        tda is the tda dict.  If there is a tda dict and an okfile, the
            "_okfile" tda is set.

        tra is the tra dict.  If the file comparator is able
            to put useful attributes in the tra, this will be used.

        cleanup is true if it should delete output files from passing tests.

    In your code, you would write something like:

        x = compare_files(
                clist = [
                    ( 'binary_output',  'binary' ),
                    ( 'text_output',    'binary', { 'ignore_date' : True } ),
                    ],
                okroot= ( __file__, 'testname' ),
                tda=tda,
                tra=tra
                )

    The function call will compare all the files, then raise an
    exception for one of the errors or assertions.

    '''

    # see if we are using an okfile; if we are, get it ready
    if okroot is not None :

        if isinstance(okroot, tuple) :
            # if it is a tuple, it is ( __file__, 'testname' );
            # chop it up and assemble a reasonable okfile name
            ok_dir  = os.path.dirname(okroot[0])
            ok_file = os.path.basename(okroot[0])
            if ok_file.endswith('.py') :
                ok_file = ok_file[:-3]
            elif ok_file.endswith('.pyc') or ok_file.endswith('.pyo') :
                ok_file = ok_file[:-4]
            ok_test = okroot[1]
            if ok_dir == '' :
                ok_dir = '.'
            okroot = ok_dir + "/okfile/" +ok_file + "." + ok_test

        # construct the path name
        okfn = os.path.join(os.getcwd(), okroot + '.okfile')
        ensure_dir( os.path.dirname(okfn) )

        # remember it in the tda
        if tda is not None :
            tda['_okfile'] = okfn

        #
        safe_rm(okfn)

        #
        okfh = open(okfn, 'w')
    else :
        # 
        okfh = None

    # ret_exc is the exception that the application should raise
    # to fail/error the test.  We want to compare all the files in
    # the list, then pick one of the worst-case exceptions to return.
    # We do this by looping over all the files and only remembering an
    # exception that is worse than what we have seen so far.
    ret_exc = None

    _normalize_list(clist)

    for n, x in enumerate(clist) :
        # make sure we are looking in the right place for the reference file
        if 'PDK_REFS' in os.environ.keys():
            PDK_REFS = os.environ['PDK_REFS']
            here = os.path.abspath(os.curdir)
            relpath = os.path.relpath(
                here,
                os.environ['PDK_TOP']
            )
            x['reference'] = os.path.join(PDK_REFS, relpath, x['reference'])

        # perform the comparison
        try :
            print "\nCOMPARE:",x['output']
            attr_prefix = 'cmp_%d_'%n
            for y in x['args'] :
                tda[attr_prefix + y] = x['args'][y]
            tda[attr_prefix + 'file'] = x['output']
            check_file( name=x['output'], cmp=x['comparator'],
                 ref=x['reference'], okfh=okfh, cleanup=False, 
                 attr_prefix=attr_prefix,
                 tda=tda, tra=tra,
                 **x['args'] )

        # assertion error means the test fails
        except AssertionError, e :
            print "FAIL"
            if ret_exc is None :
                ret_exc = e

        # any other exception means the test errors
        except Exception, e:
            print "ERROR", e
            traceback.print_exc()
            if ( ret_exc is None ) or ( isinstance(e, AssertionError) ) :
                ret_exc = e

        else :
            print "PASS"

    print ""

    # remember to close the okfile
    if okfh :
        okfh.close()

    # raise the exception if there is one
    if ret_exc :
        raise ret_exc

    # If we were asked to clean up the output files, do that now
    # -- after we know there were no exceptions, so all the compares
    # passed.
    if cleanup :
        for x in clist :
            safe_rm(x['output'])

    # done

###
### what os.makedirs should have been...
###

def ensure_dir(name) :
    '''
    Create a directory hierarchy, ignoring any exceptions.  
    There is no native python function that does this.  

    If there is an error, presumably your code will try to use
    the directory later and detect the problem then.
    '''
    try :
        os.makedirs(name)
    except :
        pass


###
### checking age of files
###

import os
import time

def file_age(f) :
    'return the time from the last modification of the file to now, in seconds'
    st = os.stat( f )
    return time.time() - st.st_mtime

def file_age_ref( other=None, days=0, hours=0 ) :
    if other is None :
        ref = ( days * 86400 + hours * 3600 )
    else :
        ref = file_age(other)
    return ref

def t_to_s( sec ) :
    days = int(sec) / 86400
    sec = sec - days * 86400
    hours = int(sec) / 3600
    sec = sec - hours * 3600
    min = int(sec) / 60
    sec = sec - min * 60
    sec = sec - hours * 3600
    return '%d days %d:%02d:%02d'%(days,hours,min,sec)

def assert_file_older( file1, file2=None, days=0, hours=0 ) :
    '''file is older than a reference

assert_file_older( 'a', 'b' )
    raises exception if 'a' is not older than 'b'

assert_file_older( 'a', days=1, hours=5 )
    raises exception if 'a' is not older than 1 day 5 hours

'''
    f_age = file_age(file1)
    ref_age = file_age_ref( file2, days, hours )
    if f_age < ref_age :
        assert False, 'file %s is %s older'%(file1,t_to_s(ref_age - f_age))

def assert_file_newer( file1, file2=None, days=0, hours=0 ) :
    '''file is newer than a reference

assert_file_newer( 'a', 'b' )
    raises exception if 'a' is not newer than 'b'

assert_file_newer( 'a', days=1, hours=5 )
    raises exception if 'a' is not newer than 1 day 5 hours

'''
    f_age = file_age(file1)
    ref_age = file_age_ref( file2, days, hours )
    if f_age > ref_age :
        assert False, 'file %s is %s newer'%(file1,t_to_s(f_age - ref_age))


#####
#####
#####

def safe_rm( fname ) :
    '''Remove a file, ignoring OSError

safe_rm( filename )
    removes a file

safe_rm( [ f1, f2, f3 ... ] )
    removes several files

OSError is what you see when the file does not currently exist.
You should structure your usage so that it does not matter if
the remove fails because of permissions or some such.
'''
    if isinstance(fname, list) :
        for x in fname :
            safe_rm( x ) 
        return
    try :
        os.unlink( fname )
    except OSError :
        pass

def wild_rm( fname ) :
    '''Remove files, matching wildcard patterns, ignoring OSError

'''
    if isinstance(fname, list) :
        for x in fname :
            wild_rm( x )
        return
    for x in glob.glob( fname ) :
        safe_rm( x )

