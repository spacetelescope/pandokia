__all__ = [ 'command', 'check_file', ]

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

###
### super-simple implementation of binary file compare
###

# bug: just compare the data right here

def cmp_binary( the_file, reference_file, msg, quiet, **kwargs ) :
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

def cmp_fits( the_file, reference_file, msg, quiet, **kwds ) :

    try :
        # new package name in the next release
        import stpytools.fitsdiff as fitsdiff
    except :
        import pytools.fitsdiff as fitsdiff

    sys.stdout.write("FITSDIFF %s %s\n"%(the_file, reference_file))
    if quiet:
        sys.stdout.write("(sorry - fitsdiff does not know how to be quiet)\n")

    d = fitsdiff.fitsdiff( the_file, reference_file, ** kwds )

    # fitsdiff returns nodiff -- i.e. 0 is differences, 1 is no differences
    if d == 0 :
        return False
    else :
        return True

###
### text comparison
###

# This was copied out of the ASCII comparison in the old regtest code.
# It could probably make use of the standard python diff library 
# instead.

def cmp_text( the_file, reference_file, msg, quiet, **kwds ) :

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
        ignore.append(datespec.timestamp)

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

    if quiet :
        return True

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
    ref = file to compare against. If none, it lives in a ref/ dir
           under the dir containing the file to compare
    exc=True: raise AssertionError if comparison fails
    cleanup=True: delete file "name" if comparison passes
    if okfh present: write (name, refname) to the provided file handle.

    msg, quiet, **kwargs: passed to individual comparators


    Returns: 
       true if same
       false if different

    """
    #Make sure we have a comparator
    if not cmp in file_comparators :
        raise ValueError("cmp=%s"%str(cmp))

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
    if r and cleanup:
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
