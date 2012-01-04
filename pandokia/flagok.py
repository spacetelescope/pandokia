
#
# This is a library routine used by the CGI portion of the flagok operation
#

import cgi
import pandokia
import os.path

import pandokia

pdk_db = pandokia.cfg.pdk_db

fdarray = { }

def noflag( name, err ) :
    print 'Flagok not possible for %s: %s<br>'%(cgi.escape(name), err)

def flagok( client, key_id, user) :

    c = pdk_db.execute('SELECT host, location, test_name FROM result_scalar WHERE key_id = :1 ', (key_id,))
    x = c.fetchone()
    if x is None :
        noflag('key_id '+str(key_id), 'no such key_id')
        return 1

    (host, location, test_name) = x

    c = pdk_db.execute('SELECT value FROM result_tda WHERE key_id = :1 AND name = :2 ', (key_id,'_okfile'))
    x = c.fetchone()
    if x is None :
        flagok_file = None
    else :
        (flagok_file, ) = x

    if flagok_file is None or flagok_file == '' :
        noflag(test_name, 'no _okfile tda')
        return 1
        
    if location is None or location == '' :
        noflag(test_name, 'location not known')
        return 1

    if host is None or host == '' :
        noflag(test_name, 'host not known')
        return 1

    if not os.path.isabs(flagok_file) :
        # os.path.join ignores the directory if the filename is full qualified
        flagok_file = os.path.join(os.path.dirname(location),flagok_file)

    flagfile = pandokia.cfg.flagok_file % host
    print "OK",cgi.escape(test_name),cgi.escape(flagok_file),flagfile,"<br>"

    if not flagfile in fdarray :
        fdarray[flagfile] = open(flagfile,"a+")

    fdarray[flagfile].write("%s\t%s\t%s\t%s\n"%(client,location,user,flagok_file))

    pdk_db.execute("update result_scalar set attn = 'N' where key_id = :1 ",(key_id,))

    return 1

def commit() :
        global fdarray
        for x in fdarray :
            fdarray[x].close()

        fdarray = { }
        pdk_db.commit()
