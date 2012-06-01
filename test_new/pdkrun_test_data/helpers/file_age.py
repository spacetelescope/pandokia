import os
import time
import pandokia.helpers.minipyt as mph
import pandokia.helpers.filecomp as fc

now = time.time()

@mph.nottest
def mkfile(name, age) :
    try :
        os.unlink(name)
    except OSError :
        pass
    open(name,"w").close()
    os.utime(name, ( now - age, now - age ) )

mkfile('60m', 3600)
mkfile('30m', 1800)
mkfile('1d', 86400 * 2)

# take int to make the text compare of the log file work
print "60m age:",int(fc.file_age('60m'))
print "30m age:",int(fc.file_age('30m'))

@mph.test
def f_older_p() :
    fc.assert_file_older( '60m', '30m' )

@mph.test
def f_newer_p() :
    fc.assert_file_newer( '30m', '60m' )

@mph.test
def f_newer_f() :
    fc.assert_file_newer( '60m', '30m' )

@mph.test
def f_older_f() :
    fc.assert_file_older( '30m', '60m' )


@mph.test
def hour_older_p() :
    fc.assert_file_older( '60m', hours=0.75 )

@mph.test
def hour_older_f() :
    fc.assert_file_older( '60m', hours=1.25 )

@mph.test
def day_older_p() :
    fc.assert_file_older( '1d', days=1 )

@mph.test
def day_older_f() :
    fc.assert_file_older( '1d', days=3 )
