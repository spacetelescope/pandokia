
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

    text_present = 0

    output.write(common.cgi_header_html)

    # don't issue the redirect for internet explorer
    if 'MSIE' in os.environ['HTTP_USER_AGENT'] :
        output.write('<p>Internet Explorer fumbles the redirect.  Click the link below.</p>')
        no_redirect = 1
    else :
        no_redirect = 0

    #

    qdb = common.open_qdb()
    db = common.open_db()

    #
    # gather up all the expected parameters
    #

    form = pandokia.pcgi.form

    qid = int(form['qid'].value)
    if 'action_remove' in form :
        qid = copy_qid(qdb,qid)
        for key_id in valid_key_ids(form) :
            qdb.execute('DELETE FROM query WHERE qid = ? AND key_id = ?', (qid, key_id))
        qdb.commit()

    if ( 'action_cattn' in form ) or ( 'action_sattn' in form ) :
        if 'action_cattn' in form :
            value='N'
        else :
            value='Y'
        for key_id in valid_key_ids(form) :
            db.execute("UPDATE result_scalar SET attn = ? WHERE key_id = ?", (value,key_id))
        db.commit()

    elif 'action_keep' in form :
        qid = copy_qid(qdb,qid)
        c = qdb.execute('SELECT key_id FROM query WHERE qid = ?', (qid,))
        for key_id, in c :
            if not str(key_id) in form :
                qdb.execute('DELETE FROM query WHERE qid = ? AND key_id = ?', (qid, key_id))
        qdb.commit()

    elif 'action_flagok' in form :
        # pick out client IP for logging
        # we don't need to validate client because it was done already in the main program
        output.write("<h3>flagging tests as ok</h3>\n")
        client = os.environ["REMOTE_ADDR"]
        user = common.current_user()
        if user is None :
            user = 'None'

        for key_id in valid_key_ids(form) :
            text_present |= pandokia.flagok.flagok(db, client, key_id, user)

        pandokia.flagok.commit(db)

    elif 'not_expected' in form :
        for key_id in valid_key_ids(form) :
            c = db.execute("SELECT project, host, test_name, context FROM result_scalar WHERE key_id = ?", (key_id,) )
            for project, host, test_name, context in c :
                db.execute("DELETE FROM expected WHERE test_run_type = 'daily' AND project = ? AND host = ? AND test_name = ? AND context = ?",(project,host,test_name,context))
        db.commit()


    if text_present :
        output.write(
            "<a href='"
            + pandokia.pcgi.cginame
            + ("?query=summary&qid=%s'>back to qid = " % qid)
            + str(qid)
            + "</a><br>\n"
            )
    else :
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

def copy_qid(qdb,old_qid) :
    now = time.time()
    c = qdb.execute("INSERT INTO query_id ( time ) VALUES ( ? ) ",(now,))
    new_qid = c.lastrowid
    qdb.commit()

    s = "INSERT INTO query ( qid, key_id ) SELECT %d, key_id FROM query WHERE qid = %d" % ( new_qid, old_qid )
    qdb.execute(s)
    qdb.commit()

    return new_qid

def valid_key_ids(form) :
    l = [ ]
    for key_id in form :
        try :
            key_id = int(key_id)
        except ValueError :
            continue
        l.append(key_id)
    return l
