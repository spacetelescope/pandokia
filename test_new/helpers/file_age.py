import os
import time
import pandokia.helpers.minipyt as mph
import pandokia.helpers.filecomp as fc


dmg_dir='/grp/software/osx/Intel/StandardScience'

now = time.time()

@mph.nottest
def mkfile(name, age) :
    try :
        os.unlink(name)
    except OSError :
        pass
    open(name,"w").close()
    os.utime(name, ( now - age, now - age ) )

mkfile('t1', 3600)
mkfile('t2', 1800)
mkfile('t3', 86400 * 2)

print "t1 age:",fc.file_age('t1')
print "t2 age:",fc.file_age('t2')

@mph.test
def f_older_p() :
    fc.assert_file_older( 't1', 't2' )

@mph.test
def f_newer_p() :
    fc.assert_file_newer( 't2', 't1' )

@mph.test
def f_newer_f() :
    fc.assert_file_newer( 't1', 't2' )

@mph.test
def f_older_f() :
    fc.assert_file_older( 't2', 't1' )


@mph.test
def hour_older_p() :
    fc.assert_file_older( 't1', hours=0.75 )

@mph.test
def hour_older_f() :
    fc.assert_file_older( 't1', hours=1.25 )

@mph.test
def day_older_p() :
    fc.assert_file_older( 't3', days=1 )

@mph.test
def day_older_f() :
    fc.assert_file_older( 't3', days=3 )
