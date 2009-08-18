# update the regtest

import os.path
import os

import stsci_regtest.configuration

import shutil


def op_update( dir, output, ref ) :
    try :
        shutil.copyfile( output, ref )
    except Exception, e:
        print output,ref,e
    else :
        print "updated",ref
        try :
            os.unlink( output )
        except Exception, e :
            print "    cannot delete",output
        else :
            print "    deleted",output
    

def op_list_ref( dir, output, ref ) :
    print ref

def main(args) :
    if args[0] == '-u' :
        args = args[1:]
        op = op_update
    else :
        op = op_list_ref

    for x in args :
        config = stsci_regtest.configuration.regtest_read (x)
        dir = os.path.dirname(x)
        x = config['output']
        for y in x :
            output  = dir + '/' + y['fname']
            ref     = dir + "/" + y['reference']
            op(dir,output,ref)

