
import cgi
import pandokia.config

fdarray = { }

def noflag( name, err ) :
    print 'Flagok not possible for %s: %s<br>'%(cgi.escape(name), err)

def flagok(db, client, key_id, user) :

    c = db.execute('SELECT host, location, test_name FROM result_scalar WHERE key_id = ?', (key_id,))
    x = c.fetchone()
    if x is None :
        noflag('key_id '+str(key_id), 'no such key_id')
        return 1

    (host, location, test_name) = x

    c = db.execute('SELECT value FROM result_tda WHERE key_id = ? AND name = ?',(key_id, 'tda__okfile'))
    x = c.fetchone()
    if x is None :
        flagok_file = None
    else :
        (flagok_file, ) = c.fetchone()

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

    flagfile = pandokia.config.flagok_file % host
    print "OK",cgi.escape(test_name),cgi.escape(flagok_file),flagfile,"<br>"

    if not flagfile in fdarray :
        fdarray[flagfile] = open(flagfile,"a+")

    fdarray[flagfile].write("%s\t%s\t%s\t%s\n"%(client,location,user,flagok_file))

    db.execute("update result_scalar set attn = 'N' where key_id = ? ",(key_id,))

    return 1

def commit(db) :
        global fdarray
        for x in fdarray :
            fdarray[x].close()

        fdarray = { }
        db.commit()
