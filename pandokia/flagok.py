
import pandokia.config

fdarray = { }

def flagok(db, client, key_id, user) :

    print "d1"
    c = db.execute('SELECT host, location, test_name FROM result_scalar WHERE key_id = ?', (key_id,))
    for host, location, test_name in c :
        if location is None :
            continue
        print "d3",host,location,test_name
        print "d3a", pandokia.config.flagok_file
        flagfile = pandokia.config.flagok_file % host
        print flagfile
        print "d3b"
        if not flagfile in fdarray :
            print "d3bb"
            fdarray[flagfile] = open(flagfile,"a+")
        print "d3c"
        fdarray[flagfile].write("%s\t%s\t%s\t%s\n"%(client,location,test_name,user))
        print "d4"
        db.execute("update result_scalar set attn = 'N' where key_id = ? ",(key_id,))
        print "d5"


def commit(db) :
        global fdarray
        for x in fdarray :
            fdarray[x].close()

        fdarray = { }
        print "d6"
        db.commit()
