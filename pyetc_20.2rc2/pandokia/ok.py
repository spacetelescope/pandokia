#
# pandokia - a test reporting and execution system
# Copyright 2010, Association of Universities for Research in Astronomy (AURA) 
#

#
# pdk ok [ list_of_okfiles ]
#
# an okfile contains information to update a single test that uses
# reference files.  Each line of the file contains two fields separated
# by spaces.  The first field is the name of the output file, and the
# second field is the name of the reference file.  If the second field
# is missing, the reference file has the same name in the directory "ref/".

import sys
import os
import os.path
import shutil
import pandokia.common as common
import re

import datetime

# suffix to put on old reference files
old = "." + datetime.date.today().isoformat() + ".old"

try_to_delete = 1

def run(args) :
    # entry point for the command line

    prob = 0
    verbose = 0
    web_file = 0
    create_old = 0

    for okfile in args :
        if okfile == '-h' :
            print helpstr

        if okfile == '-v' :
            verbose = 1
            continue

        if okfile == '-w' :
            web_file = 1
            continue

        if okfile == '-old' :
            create_old = 1
            continue

        if verbose :
            print "okfile", okfile

        if web_file :
            prob |= process_webfile( okfile, verbose )
            if create_old :
                try :
                    os.rename( okfile, okfile + old )
                except Exception, e :
                    print "cannot rename",okfile,"to",okfile+old
                    print e
        else :
            prob |= process_okfile( okfile, verbose )

    return prob

#
# process_webfile processes the file that the web server created
#

web_re = re.compile('^[A-Za-z0-9/_.-]*$')

def process_webfile( webfile, verbose ) :
    prob = 0

    f = open( webfile, 'r' )

    for line in f :
        line = line.strip()
        if line.startswith('#' ) :
            continue
        line = line.split()
        if len(line) != 4 :
            print "invalid input in web file:",line
            prob = 1
            continue

        ip, tesfile, user, okfile = line

        if not web_re.match( okfile ) :
            print "invalid okfile",ip, user, repr(okfile)
            prob = 1
            continue

        print user, ip, okfile 

        process_okfile( okfile, verbose )

    return prob


#
# process_okfile processes an okfile directly
#

def process_okfile( okfile, verbose ) :

    try :
        f = open(okfile,'r')
    except Exception, e :
        print "    cannot open",okfile
        print "    ",e
        return 1

    print "    okfile",okfile

    prob = 0

    dirname = os.path.dirname(okfile)

    for line in f :
        line = line.strip()
        if line.startswith('#') :
            continue
        line = line.split()
        if len(line) != 2 :
            print "        invalid input in ok file %s: %s"%(okfile,line)
            prob = 1
            continue

        src = line[0]
        dest = line[1]

        # watch carefully: os.path.join can tell whether src is a
        # fully qualfied path.  If it is, it ignores dirname, otherwise
        # it uses src as a relative path.
        src = os.path.join(dirname,src)

        dest = os.path.join(dirname,dest)

        prob = prob | doit(src,dest, verbose)

    try :
        if try_to_delete :
            os.unlink(okfile)
    except IOError, e:
        print "        cannot remove ",okfile
        print e

    return prob



# actually do the rename/copy with any directory create needed
def doit(src, dest, verbose) :

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
