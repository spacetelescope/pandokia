#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
# This is a total hack.  We'll fix it later.
#

import os
import re
import pandokia
import pandokia.pcgi
import common

debugging = 1

def nok(x) :
    print "Internal Error"
    if debugging :
        print x
    return None

# list of valid parameters to the cgi
params = { 'query': 0, 'key_id': 0, 'host': 0, 'ok': 0 }

def flagok() :
    print "content-type: text/plain\n\n"

    print "NOT IMPLEMENTED THIS VERSION"

    return

    # the rest of this is a hack that kind-of-works with a legacy test system at stsci

    try :
        # later, check for properly authorized to update the tests
        # later, keep another log of who did what

        form = pandokia.pcgi.form

        # check that all form values that are present are expected
        for x in form :
            if not x in params :
                return nok(0)

        # check that all expected parameters are present
        for x in params :
            if not x in form :
                return nok(1)

        # pick out host, check valid name
        host=form['host'].value

        if not re.search("^[a-zA-z0-9]*$",host) :
            return nok(2)

        # pick out client IP for logging
        # we don't need to validate client because it was done already in the main program
        client = os.environ["REMOTE_ADDR"]

        # find the name of the test
        test = form['ok'].value

        # none of our test names are this long
        if len(test) > 200 :
            return nok(4)

        # look for bogus characters in the test names
        if re.search("[^A-Za-z0-9_./-]",test) :
            return nok(5)
        if re.search("/\.\.",test) :
            return nok(6)

        # key_id of db record to update
        key_id = int(form['key_id'].value)

        # file to append to
        flagfile = pandokia.cfg.flagok_file % host
        print flagfile

        # add to end of file; I hope this isn't a race.
        # I could be storing this in the database, but then I
        # would also have to get it back out.  This is good enough
        # for now.
        try :
            f=open( flagfile, "a+" )
        except :
            return nok(8)
        f.write("%s\t%s\n"%(client,test))
        f.close()

        # update ATTN flag in database
        db = common.open_db()
        db.execute("update result_scalar set attn = 'N' where key_id = ? ",(key_id,))
        db.commit()
        db.close()

        print "OK"

    except Exception, e :
        if debugging :
            raise
        return nok(9)
