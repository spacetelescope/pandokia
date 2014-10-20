#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#
# Assorted functions that are useful in more than one place

import time
import datetime


#
# determine the host name, for reporting purposes
#
# For now, I don't care about the domain because it is always the same
# for me and writing .stsci.edu after the host name all the time just
# causes clutter.  Later, we'll make it configurable whether to
# trim off the domain or not.
#

hostname = None

def gethostname( ) :
    global hostname
    if hostname is None :
        import platform
        hostname = platform.node()
        if "." in hostname :
            hostname = hostname.split(".")[0]
    return hostname
    # bug: decided when to use fqdn or not; override hostname in config; etc



def decode_time_float( istr ) :
    if istr is None :
        return None
    try :
        tyme = float(istr)
    except ValueError :
        if '.' in istr :
            l = istr.split('.',1)
        else :
            l = [ istr ]

        try :
            d = time.strptime( l[0], "%Y-%m-%d %H:%M:%S" )
            tyme = time.mktime(d)
        except ValueError :
            try :
                d = time.strptime( l[0], "%Y-%m-%dT%H:%M:%S" )
                tyme = time.mktime(d)
            except ValueError :
                return None

        if len(l) > 1 :
            a = l[1]
            frac = float(int(a)) / int( '1'+'0'*len(a) )
            tyme = tyme + frac

    return tyme

def decode_time_str( istr ) :
    if istr is None :
        return None
    try :
        tyme = float(istr)
    except ValueError :
        return istr
    return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tyme)) + '.' + ("%03d" % ( int( tyme - int(tyme) ) * 1000 ))

def time_diff( max, min ) :
    max = decode_time_float( max )
    min = decode_time_float( min )
    if max is None :
        return None
    if min is None :
        return None
    return datetime.timedelta( seconds= int(max - min ) )
