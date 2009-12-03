
#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import cgi
import re
import copy
import time
import os

import urllib

import pandokia
import pandokia.text_table as text_table
import pandokia.pcgi
import pandokia.flagok
import common


def run( ) :
    # 
    # take actions based on the button a user slected from the summary page
    #

    output = sys.stdout

    output.write(common.cgi_header_html)

    # don't issue the redirect for internet explorer
    if 'MSIE' in os.environ['HTTP_USER_AGENT'] :
        output.write('<p>Internet Explorer fumbles the redirect.  Click the link below.</p>')
        no_redirect = 1
    else :
        no_redirect = 0

    #

    print "A"
    qdb = common.open_qdb()
    print "A1"
    db = common.open_db()
    print "A2"

    try :
        print "A2A",dir(pandokia.pcgi),"A2A"
    except Exception, e :
        print e

    #
    # gather up all the expected parameters
    #

    form = pandokia.pcgi.form

    print "A3"
    for x in form :
        print "A4"
        print x
        print "A5"
    print "A6"

    qid = int(form['qid'].value)
    print "b"
    if 'action_remove' in form :
        for key_id in form :
            try :
                key_id = int(key_id)
            except ValueError :
                continue
            qdb.execute('DELETE FROM query WHERE qid = ? AND key_id = ?', (qid, key_id))
        qdb.commit()

    if ( 'action_cattn' in form ) or ( 'action_sattn' in form ) :
        if 'action_cattn' in form :
            value='N'
        else :
            value='Y'
        for key_id in form :
            try :
                key_id = int(key_id)
            except ValueError :
                continue
            db.execute("UPDATE result_scalar SET attn = ? WHERE key_id = ?", (value,key_id))
        db.commit()

    elif 'action_keep' in form :
        c = qdb.execute('SELECT key_id FROM query WHERE qid = ?', (qid,))
        for key_id, in c :
            if not str(key_id) in form :
                qdb.execute('DELETE FROM query WHERE qid = ? AND key_id = ?', (qid, key_id))
        qdb.commit()

    elif 'action_flagok' in form :
        # pick out client IP for logging
        # we don't need to validate client because it was done already in the main program
        print "c1"
        client = os.environ["REMOTE_ADDR"]
        if "REMOTE_USER" in os.environ :
            user = os.environ["REMOTE_USER"] 
        else :
            user = str(os.getuid())
        print "c2"

        for key_id in form :
            print "c3",key_id
            try :
                key_id = int(key_id)
            except ValueError :
                continue
            print "c4",db,client,key_id, user
            pandokia.flagok.flagok(db, client, key_id, user)
            print "c5"

        print "c6"
        pandokia.flagok.commit(db)
        print "c7"

    print "e"

    if 1 :
        print "f"
        if not no_redirect :
            output.write(
                '<html><head><meta http-equiv="REFRESH" content="0;'
                + pandokia.pcgi.cginame
                + ( '?query=summary&qid=%s"' % qid )
                + '>\n</head><body>\n'
                )
        output.write(
            "redirecting: <a href='"
            + pandokia.pcgi.cginame
            + ("?query=summary&qid=%s'>qid = " % qid)
            + str(qid)
            + "</a><br>\n"
            )

    print "g"
