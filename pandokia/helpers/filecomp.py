'''
pandokia.helpers.filecomp - a general interface for intelligently
    comparing two files

contents of this module:

    command(str, env) 
            portable way to run a shell command (the python library has
            many ways to do this, but nearly all are deprecated.  This
            interface is meant to use whichever one is in favor.)

    check_file( name, comparator, reference_file, header_message=None, 
        quiet=False, raise_exception=True, cleanup=False, ok_file_handle=None, 
        **kwargs )
            Compare a file to a reference file, using a specified comparator.
            It can display header_message before the comparison, raise an
            AssertionError if the files do not match, delete the input file
            after comparison (cleanup), and write a pdk compliant okfile.

    file_comparators[ ]
            a dict that converts comparator names to a function that performs
            the comparison.  This is here so you can add your own comparators.

    cmp_example( )
            an example of how to make your own comparison function; this is
            not actually used, but you can look at the docstring.

'''

__all__ = [ 'command', 'check_file', 'file_comparators', 'cmp_example' ]

import os
import re
import sys
import subprocess


###
### "portable" way to run a shell command.  Use this in your
### tests to run a command
###

# The standard python library contains MANY methods for starting a
# child process, but nearly all of them are deprecated.  When subprocess
# becomes deprecated, we can update it once here instead of in every
# test that anybody writes.

# bug: capture stdout/stderr of child process and repeat it into
# sys.stdout/sys.stderr (so nose can capture it).
def command(s, env=None) :
    sys.stdout.flush()
    sys.stderr.flush()
    r = subprocess.call(s, shell=True, env=env)
    if r < 0 :
        raise Exception("signal %d from %s"%(-r, s) )
    return r

###
### Various file comparisons
###
### true = same
### false = different
###

def cmp_example( the_file, reference_file, header_message, quiet, **kwargs ) :
    '''
    cmp_example(  the_file, reference_file, header_message, quiet, **kwargs ) 

    This is an example of how to write your own file comparison function.
    See also the source code.

        the_file is the input file that we are testing.

        reference_file is the reference file that we already know to be correct.

        header_message is printed before the comparison.  Use this if you want
        to say something about what you are doing.  Notably, this is useful
        if your comparison might print things.

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

    You can then use it by calling check_file:

        from pandokia.helpers.filecomp import check_file

        # simplest form
        check_file('output_file.txt', 'example')

        # more complex form - see check_file for detail
        check_file('output_file.txt', 'example', msg='Example Compare:',
            cleanup=True )

    '''
    # You can see I just copied cmp_binary for an example.
    if ( not quiet ) and ( header_message is not None ) :
        sys.stdout.write(header_message)
    r=command("cmp -s %s %s"%(the_file, reference_file))
    if r == 1:
        if not quiet :
            sys.stdout.write("file match error: %s\n"%the_file)
        return False
    elif r != 0:
        raise OSError("cmp command returned error status %d"%r)
    return True


###
### super-simple implementation of binary file compare
###

# bug: just compare the data right here

def cmp_binary( the_file, reference_file, msg, quiet, **kwargs ) :
    '''
    cmp_binary - a byte-for-byte binary comparison; the files must
        match exactly.  No kwargs are recognized.
    '''
    r=command("cmp -s %s %s"%(the_file, reference_file))
    if r == 1:
        if not quiet :
            if msg is not None :
                sys.stdout.write("%s\n",msg)
            sys.stdout.write("file match error: %s\n"%the_file)
        return False
    elif r != 0:
        raise OSError("cmp command returned error status %d"%r)
    return True

###
### FITS - Flexible Image Transport System
###

#
# This uses fitsdiff from STSCI_PYTHON, an astronomical data analysis package
#
# http://www.stsci.edu/resources/software_hardware/pyraf/stsci_python
#

def cmp_fits( the_file, reference_file, msg, quiet, **kwargs ) :
    '''
    cmp_fits - compare fits files.  kwargs are passed through to fitsdiff
    '''

    try :
        # new package name in the next release
        import stpytools.fitsdiff as fitsdiff
    except :
        import pytools.fitsdiff as fitsdiff

    sys.stdout.write("FITSDIFF %s %s\n"%(the_file, reference_file))
    if quiet:
        sys.stdout.write("(sorry - fitsdiff does not know how to be quiet)\n")

    d = fitsdiff.fitsdiff( the_file, reference_file, ** kwargs )

    # fitsdiff returns nodiff -- i.e. 0 is differences, 1 is no differences
    if d == 0 :
        return False
    else :
        return True

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

def cmp_text( the_file, reference_file, msg, quiet, **kwds ) :
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

    for val in kwds.get('ignore_wstart',[]):
        if ignore_raw.has_key('wstart'):
            ignore_raw['wstart'].append(val)
        else:
            ignore_raw['wstart']=[val]
        pattern=r'\s%s\S*\s'%val
        ignore.append(pattern)

    for val in kwds.get('ignore_wend',[]):
        if ignore_raw.has_key('wend'):
            ignore_raw['wend'].append(val)
        else:
            ignore_raw['wend']=[val]
        pattern=r'\s\S*%s\s'%val
        ignore.append(pattern)

    for val in kwds.get('ignore_regexp',[]):
        ignore_raw['regexp']=val
        ignore.append(val)

    if kwds.get('ignore_date',False):
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
### end of format-specific file comparison functions
###



file_comparators = {
    'binary':       cmp_binary,
    'fits':         cmp_fits,
    'text':         cmp_text,
}

def update_okfile(okfh, name, ref):
    
    okfh.write("%s %s\n"%(os.path.abspath(name),
                          os.path.abspath(ref)))
    
def check_file( name, cmp, ref=None, msg=None, quiet=False, exc=True,
                cleanup=False, okfh=None, **kwargs ) :
    """
    status = check_file( name, cmp, msg=None, quiet=False, exc=True,
                         cleanup=False, okfh=None, **kwargs )

    name = file to compare

    cmp = comparator to use

    ref = file to compare against. If None, it lives in a ref/ dir
           under the dir containing the file to compare

    exc=True: raise AssertionError if comparison fails

    cleanup=True: delete file "name" if comparison passes

    okfh is a file-like object to write the okfile information; it must
        have a write() method.  If None, no okfile is written.

    msg, quiet, **kwargs: passed to individual comparators

    Returns: 
       True if same
       False if different (but raises exception if exc=True)

    """
    #Make sure we have a comparator
    if not cmp in file_comparators :
        raise ValueError("file comparator %s not known"%str(cmp))

    #Construct the reference file if necessary
    if ref is None:
        ref = os.path.join(os.path.dirname(name),
                           'ref',
                           os.path.basename(name))
    #Do the comparison
    try:
        r = file_comparators[cmp](name, ref, msg, quiet, **kwargs )
    #Catch exceptions so we can update the okfile
    except Exception:
        if okfh:
            update_okfile(okfh, name, ref)
        raise

    #Clean up file that passed if we've been asked to
    if r :
        if cleanup:
            try:
                os.unlink(name)
            except Exception:
                pass

    #Update the okfile if the test failed
    else:
        if okfh:
            update_okfile(okfh, name, ref)

        #Last of all, raise the AssertionError that defines a failed test
        if exc :
            raise(AssertionError("files are different: %s, ref/%s\n"%(name,name)))
    #and return the True/False (Pass/Fail) status
    return r

