#
# pandokia - a test reporting and execution system
# Copyright 2010, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import os
import os.path
import shutil
import pandokia.common as common

import datetime

# suffix to put on old reference files
old = "." + datetime.date.today().isoformat() + ".old"

#
# pdk ok [ list_of_okfiles ]
#
# an okfile contains information to update a single test that uses
# reference files.  Each line of the file contains two fields separated
# by spaces.  The first field is the name of the output file, and the
# second field is the name of the reference file.  If the second field
# is missing, the reference file has the same name in the directory "ref/".

try_to_delete = 1

def run(args) :
    # entry point for the command line

    prob = 0

    for okfile in args :
        if okfile == '-h' :
            print helpstr

        f = open(okfile,'r')

        dirname = os.path.dirname(okfile)

        for line in f :
            line = line.strip()
            if line.startswith('#') :
                continue
            line = line.split()
            if len(line) != 2 :
                print "invalid input:",line

            src = line[0]
            dest = line[1]

            # watch carefully: os.path.join can tell whether src is a
            # fully qualfied path.  If it is, it ignores dirname, otherwise
            # it uses src as a relative path.
            src = os.path.join(dirname,src)

            dest = os.path.join(dirname,dest)

            prob = prob | doit(src,dest)

        try :
            if try_to_delete :
                os.unlink(okfile)
        except IOError, e:
            print "cannot remove ",okfile
            print e

        return prob


# actually do the rename/copy with any directory create needed
def doit(src, dest) :

    # We ignore a lot of errors here with overly broad except clauses.
    # That is because the possible exceptions are not clearly defined,
    # and when you get one, you have to work to know what it means.
    # (e.g. you get IOError for both 'file not found' and 'disk is on fire')
    #
    # This function tries a lot of different things, and returns when it
    # thinks it has success.  If not, the last error it encounters will
    # still represent the real problem that the user needs to know about.

    if not os.path.exists(src):
        print "source (output from test) does not exist:",src
        return 1

    # Make sure the "old" reference file is not there.  If you do multiple
    # updates per day, you will lose some of the old reference files.
    try :
        os.unlink(dest+old)
    except :
        pass

    # rename the reference file to the "old" name
    try :
        os.rename(dest, dest+old)
    except Exception, e:
        if os.path.exists(dest) :
            print "cannot rename",dest," to ",dest+old
            print e
            return 1

    # The destination file must not be there.
    try :
        os.unlink(dest)
    except :
        pass

    # try to rename the file; if it works, we're done
    try :
        os.rename(src,dest)
        return 0
    except :
        pass

    # maybe the destination directory is not there - ignore the exception
    # when the last directory is already there
    try :
        os.makedirs(os.path.dirname(dest))
    except :
        pass

    # maybe we created the directory and the rename can work now
    try :
        os.rename(src,dest)
        return 0
    except :
        pass

    # ok, maybe not, but maybe we can copy the file
    try :
        shutil.copyfile(src, dest)
    except IOError, e :
        # ok, we are now out of options - it didn't work
        print "cannot copy",src,"to",dest
        print e

    return 1
