"""
import pandokia.helpers.dcomp as dict_comp
import pandokia.helpers.pycode as pycode

# minipyt

    with pycode.test('name') as t :
        okfh = dcomp.open_okfile( t.full_name )
        
        dict_comp.dictionary_comp( 
            data_dict = d, 
            file_base = t.full_name + '.a', 
            t.tda, t.tra,  ... )
        
        dict_comp.dictionary_comp( 
            data_dict = d, 
            file_base = t.full_name + '.b', 
            t.tda, t.tra,  ... )

        okfh.close()

# py.test

    def test_foo( pdk_test_name ) :

        okfh = dcomp.open_okfile( pdk_test_name )
    
        dict_comp.dictionary_comp( ... file_base = pdk_test_name + '.a' ... )

        dict_comp.dictionary_comp( ... file_base = pdk_test_name + '.b' ... )

"""
    

from __future__ import division
import os
import sys
import glob
import re
import errno
import numbers

from   pandokia.helpers.filecomp import safe_rm
import pandokia.helpers.display as display

# looking ahead to python 3
string_type = basestring

##########
#
# The interface to the comparison function gets complicated if the dict
# holds a hierarchical data structure.  Rather than a recursive compare
# and a recursive way to specify tolerances, etc, we flatten the index
# into a single namespace.
#
# The separator is '.' like in python, so a['a.b']=1 can conflict with
# a['a']={'b':1}.  Bummer if you have that kind of structure.
#
# This is a non-destructive operation.
#

class DuplicateIndexException(Exception) :
    "Raised if two different elements of a dict flatten to the same name"


#
# flatten from a dict into another dict; if it is recursive, the prefix
# describes which branch of the tree we are in right now
#
def _flatten_into( from_d, to_d, prefix  ):
    for x in from_d :
        if isinstance( from_d[x], dict ) :
            # A dict is just flattened into the same output dict with
            # a longer prefix.
            _flatten_into( from_d[x], to_d, prefix + x + '.' )

        elif isinstance( from_d[x], ( list, tuple, set ) )  :
            # It is way easier to convert a list into a dict and the
            # flatten the dict.

            # Find out how many digits in the last index value.  Use that
            # to make a format string for the index values.
            fmtlen = len( '%d' % (len(from_d[x])-1) )
            fmtstr = '%%0%dd' % fmtlen

            # actually convert the list to the dict and flatten it
            t = { }
            for i,y in enumerate( from_d[x] ) :
                t[fmtstr % i] = y
            _flatten_into( t, to_d, prefix + x + '.' )

        else :
            # anything else is presumed scalar
            idx = prefix + str(x)
            if idx in to_d :
                raise DuplicateIndexException(idx)
            to_d[ idx ] = from_d[ x ]

def flatten( d ) :
    "Mash a hierarchical dict/list structure (like from json) into a flat dict"
    new = { }
    _flatten_into( d, new, '' )
    return new

##########
# handling of output and reference files
#

class NoReferenceFile(Exception):
    "raise when we cannot find the reference file"

# ensure that required directories exist
for x in ( 'output', 'ref', 'okfile' ) :
    try :
        os.mkdir(x)
    except :
        # No need to write a lot of code to distinguish good/bad exceptions here.
        # If there is a problem, we will find out when we try to use the directory.
        pass

def write_output( file_base, data_dict, interesting_fields ) :
    fn = "output/"+file_base
    safe_rm(fn)
    fp = open(fn,"w")
    dict_copy = {}
    for x in interesting_fields :
        try :
            dict_copy[x] = data_dict[x]
        except KeyError :
            # yes, this means the output file cannot possibly be correct.
            pass
    fp.write(display.dprint(dict_copy))
    fp.close()
    return fn

def read_reference( fn ) :
    try :
        fp = open(fn,"r")
    except IOError, e :
        if e.errno == errno.ENOENT :
            raise NoReferenceFile(fn)
        raise
    d = eval( fp.read() )
    fp.close()
    return d
    

##########


spaces = re.compile("[\s]")

##########
#
# write an okfile for pandokia's flagok feature
#

def open_okfile( test_name ) :
    # the okfile is in the subdirectory okfile/
    okfile = os.getcwd() + '/okfile/' + test_name
    safe_rm( okfile )
    f = open( okfile, "w")
    return f

def append_okfile( okfh, output_file, reference_file ) :
    # we put the okfile in a subdirectory, so the names we have are relative to ../
    if reference_file.startswith('/'):
        okfh.write('../%s %s\n' % ( output_file, reference_file ) )
    else:
        okfh.write('../%s ../%s\n' % ( output_file, reference_file ) )
    okfh.flush()

##########
#
# Compare all the interesting fields.  This function is used by
# the tests.
#

def dictionary_comp(
        data_dict,
            # the actual data
        file_base,
            # implies output file name
            # implies reference file name
            # implies ok file name
            # implies refs/file.fields for compare/ignore fields
            # assumes PDK_REFS environment
        tda = None,
        tra = None,
            # if present, fill tra with output, relative difference
        interesting_fields = None,
            # if interesting, compare only those
        uninteresting_fields = [ ],
            # if uninteresting, exclude those from the default list
        fp_tolerance = 1e-7,
            # 
        tolerance_dict = { },
            # you can give a specific tolerance for specific fields
            # default is no special preference
        print_info = False,
            # 
        okfh = None,
            #
        fail_only = False,
            # if true, only report fields that are involved in a failure
        ) :

    # Start off saying the whole comparison has not failed.  This
    # will be the state until the end, unless some element fails.
    fail = False

    # The list of fields that had an error in the comparison.
    errors = [ ]

    # so we don't have to keep saying "if tda : tda[xx] = yy"
    # these dicts will go out of scope at the end of the function
    if tda is None :
        tda = { }
    if tra is None :
        tra = { }
	
    # a reference dict, generated by hand or from a previous result.
    # or nothing, if it is not there -- gets us through the test

    # BUG: support PDK_REFS
    ref_fn = "ref/"+file_base

    # Read the reference dictionary.  no_reference_file will be the
    # exception if there is no reference file; it is re-raised at
    # the end.  We don't just raise it now because we want all
    # the reporting that comes below.
    try :
        ref_dict = read_reference( ref_fn )
        no_reference_file = None
    except NoReferenceFile as e:
        ref_dict = { }
        no_reference_file = e

    # flatten the data dict (the ref dict is already flattened)
    data_dict = flatten( data_dict )

    # identify interesting fields.  if explicitly specified, use 
    # just that.  Otherwise it defaults to all the fields except
    # those identified as uninteresting.
    if interesting_fields is None :
        interesting_fields = set( [ x for x in data_dict ]
             + [ x for x in ref_dict ] ) - set(uninteresting_fields)

    # save the interesting fields from the flattened dict
    out_fn = write_output( file_base, data_dict, interesting_fields )

    # add a line to the okfile
    if okfh :
        append_okfile( okfh, out_fn, ref_fn )
    
    # Which fields were in the expected answers, but missing from the result.
    missing=set()

    # Which fields did not compare closely enough.
    failed= []

    # Report the default tolerance.
    tda['tolerance'] = fp_tolerance

    # Set up to report the max discrep
    if not fail_only :
        tra['max_discrep']=0
        tra['max_discrep_var']=None

    # Loop over the interesting keys, comparing each one.
    for k in interesting_fields :

        # flag of whether this iteration of the loop fails the compare
        this_fail = False

        # value of the discrepancy for this iteration of the loop
        discrep = None

        # see if there are custom tolerances for this field
        try:
            tol = tolerance_dict[k]
            tda['tol_%s'%k] = tol
        except KeyError:
            tol = fp_tolerance

        # pick out the data value
        try :
            data = data_dict[k]
        except AttributeError :
            tra['discrep_%s'%k] = 'missing data'
            this_fail = True
            missing.add(k)
            continue

        # pick out the reference value
        try :
            ref = ref_dict[k]
        except KeyError :
            tra['discrep_%s'%k] = 'missing ref'
            this_fail = True
            missing.add(k)
            continue

        ## comparing numbers
        if isinstance(data, numbers.Number) and isinstance(ref, numbers.Number) :

            # If both are zero, everything is good.
            if data == 0 and ref == 0 :
                discrep = 0

            else:
                # Compare the discrepancy as a proportion of the reference
                # value.
                try:
                    discrep=(data-ref)/ref
                    if (abs(discrep) > tol):
                        failed.append(k)
                        this_fail = True

                # If the reference is zero, use absolute difference instead.
                except ZeroDivisionError, e:
                    discrep = ( data - ref )
                    if (abs(discrep) > tol):
                        failed.append(k)
                        this_fail = True

        ## comparing strings
        elif isinstance(data, string_type) and isinstance(ref, string_type) :
            if ref.strip() != data.strip() :
                failed.append(k)
                discrep = True
                this_fail = True

        ## comparing non-number, non-string, non-dict, non-list
	    ## If you use json for your data, this just means booleans
	    ## or two different types
        else:
            # neither string nor number - all we have for comparing is equality
            if data != ref :
                failed.append(k)
                discrep = True
                this_fail = True

        # If this element of the data failed, the whole test failed.
        if this_fail :
            fail = True

        # Report this element in the tra if it failed, or if we are
	    # reporting all elements.
        if this_fail or not fail_only :
            # Report the computed value and the reference value as tra.
            tra[k]=str(data)
            tra['ref_%s'%k]=str(ref)
            tra['discrep_%s'%k]=discrep

    # end: for k in interesting_fields

    # If any of the fields failed, report what they were.
    if len(failed) > 0:
        failed.sort()
        tra['failed']=failed

        # For failed numerical values, report the max discrepancy and variable
        discrep, vname = 0.0, None
        for k in failed:
            val=abs(tra['discrep_%s'%k])
            if (isinstance(val,float) and val > discrep):
                discrep=val
                vname=k

        if vname is not None:
            tra['max_discrep']=discrep
            tra['max_discrep_var']=vname


    # anything that wasn't there is also a problem
    if missing :
        m=list(missing)
        m.sort()
        tra['missing']=str(m)
        fail = True

    # This is a pretty display for the interactive user.
    if print_info and ( fail or ( not fail_only ) ) :
        from pandokia.text_table import text_table
        tt = text_table()

        failed_set = set(failed)

        tt.define_column('name')
        tt.define_column('expect')
        tt.define_column('actual')
        tt.define_column('F')
        tt.define_column('discrep')

        for row, k in enumerate( sorted(interesting_fields) ):
            tt.set_value( row, 'name', k )
            if k in ref_dict :
                tt.set_value( row, 'expect', ref_dict[k] )
            if k in data_dict :
                tt.set_value( row, 'actual', data_dict[k] )
            s = 'discrep_%s' % k
            if s in tra :
                tt.set_value( row, 'discrep', tra[s] )
            if k in failed_set :
                tt.set_value( row, 'F', '*' )

        print tt.get_rst(headings=1)

        if missing:
            m=list(missing)
            m.sort()
            print "Missing keys:", m

        if fail :
            print "FAILED"

    if no_reference_file:
        raise no_reference_file

    if len(errors) :
        raise Exception(str(errors))

    if fail :
        raise AssertionError('%s failed' % file_base )

