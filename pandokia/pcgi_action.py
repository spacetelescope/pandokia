
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

pdk_db = pandokia.cfg.pdk_db


def run( ) :
    # 
    # take actions based on the button a user slected from the summary page
    #

    output = sys.stdout

    text_present = 0

    output.write(common.cgi_header_html)
    output.write('...')
    output.flush()

    # don't issue the redirect for internet explorer
    if 'MSIE' in os.environ['HTTP_USER_AGENT'] :
        output.write('<p>Internet Explorer fumbles the redirect.  Click the link below.</p>')
        no_redirect = 1
    else :
        no_redirect = 0

    #
    # gather up all the expected parameters
    #

    form = pandokia.pcgi.form

    # lots of cases use qid
    if 'qid' in form :
        qid = int(form['qid'].value)
    else :
        qid = None

    #

    if 'action_remove' in form :
        qid = copy_qid(qid)
        for key_id in valid_key_ids(form) :
            pdk_db.execute('DELETE FROM query WHERE qid = :1 AND key_id = :2 ', (qid, key_id))
        pdk_db.commit()

    if ( 'action_cattn' in form ) or ( 'action_sattn' in form ) :
        if 'action_cattn' in form :
            value='N'
        else :
            value='Y'
        for key_id in valid_key_ids(form) :
            pdk_db.execute("UPDATE result_scalar SET attn = :1 WHERE key_id = :2 ", (value,key_id))
        pdk_db.commit()

    elif 'action_keep' in form :
        qid = copy_qid(qid)
        c = pdk_db.execute('SELECT key_id FROM query WHERE qid = :1 ', (qid,))
        for key_id, in c :
            if not str(key_id) in form :
                pdk_db.execute('DELETE FROM query WHERE qid = :1 AND key_id = :2 ', (qid, key_id))
        pdk_db.commit()

    elif ( 'action_flagok' in form ) or ( 'action_flagok_rem' in form ) :
        # pick out client IP for logging
        # we don't need to validate client because it was done already in the main program
        output.write("<h3>flagging tests as ok</h3>\n")
        client = os.environ["REMOTE_ADDR"]
        user = common.current_user()
        if user is None :
            user = 'None'

        for key_id in valid_key_ids(form) :
            print "Flagging %s<br>"%key_id
            text_present |= pandokia.flagok.flagok(client, key_id, user)

        pandokia.flagok.commit()

        if 'action_flagok_rem' in form :
            # copy of 'remove' above - expedient for the moment
            qid = copy_qid(qid)
            for key_id in valid_key_ids(form) :
                pdk_db.execute('DELETE FROM query WHERE qid = :1 AND key_id = :2 ', (qid, key_id))
            pdk_db.commit()

    elif 'not_expected' in form :
        for key_id in valid_key_ids(form) :
            c = pdk_db.execute("SELECT project, host, test_name, context FROM result_scalar WHERE key_id = :1 ", (key_id,) )
            for project, host, test_name, context in c :
                pdk_db.execute("DELETE FROM expected WHERE test_run_type = 'daily' AND project = :1 AND host = :2 AND test_name = :3 AND context = :4 ",(project,host,test_name,context))
        pdk_db.commit()

    elif 'claim_qid' in form :
        print "CLAIM", common.current_user()
        pdk_db.execute("UPDATE query_id SET username = :1 WHERE qid = :2 ",(common.current_user(), qid))
        pdk_db.commit()

    elif 'valuable_qid' in form :
        v = int(form['valuable_qid'].value)
        if v :
            expire = pandokia.never_expires
        else :
            expire = time.time() + pandokia.cfg.default_qid_expire_days * 86400
        pdk_db.execute("UPDATE query_id SET username = :1, expires = :2 WHERE qid = :3",(common.current_user(), expire, qid))
        pdk_db.commit()

    elif 'valuable_run' in form :
        text_present = 1
        v = int(form['valuable_run'].value)
        test_run = str(form['test_run'].value)
        pdk_db.execute("UPDATE distinct_test_run SET valuable = :1 WHERE test_run = :2",(v,test_run))
        pdk_db.commit()
        if v :
            v = 'valuable'
        else :
            v = 'not valuable'
        print "Test run",test_run," marked as ",v

    elif 'note' in form :
        text_present = 1
        v = str(form['note'].value)
        test_run = str(form['test_run'].value)
        pdk_db.execute("UPDATE distinct_test_run SET note = :1 WHERE test_run = :2",(v,test_run))
        pdk_db.commit()
        print "Note set"

    elif 'count_run' in form :
        text_present = 1
        v = str(form['count_run'].value)
        c = pdk_db.execute("SELECT COUNT(*) FROM result_scalar WHERE test_run = :1",(v,))
        x = c.fetchone()
        count = x[0]
        if count == 0 :
            print "zero test results - record deleted"
            pdk_db.execute("DELETE FROM distinct_test_run WHERE test_run = :1",(v,))
        else :
            print "updated - count = ",count
            pdk_db.execute("UPDATE distinct_test_run SET record_count = :1 WHERE test_run = :2 ", (count,v) )
        pdk_db.commit()

    elif 'edit_comment' in form :
        text_present = 1
        c = pdk_db.execute("SELECT notes FROM query_id WHERE qid = :1",(qid,))
        note = c.fetchone()[0]
        if note is None :
            note = ''
        output.write('<form action=%s method=get name=edit_comment>' % pandokia.pcgi.cginame )
        output.write('<input type=hidden name=query value=action>')
        output.write('<input type=hidden name=qid value=%d>'%qid)
        output.write('<input type=hidden name=save_comment value=1>')
        output.write('<textarea cols="80" rows="10" name=comment>%s</textarea><br>'%(cgi.escape(note)))
        output.write('<input type=submit value="save">')
        output.write('</form>')

    elif 'save_comment' in form :
        notes = form['comment'].value
        pdk_db.execute('UPDATE query_id SET notes = :1 WHERE qid = :2', (notes, qid) )
        pdk_db.commit()

    else :
        no_redirect = 1
        print form

    if qid is not None :
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
    else :
        output.write("<br>Hit BACK and RELOAD\n")

def copy_qid(old_qid) :
    now = time.time()
    c = pdk_db.execute("INSERT INTO query_id ( time ) VALUES ( :1 ) ",(now,))
    new_qid = c.lastrowid
    pdk_db.commit()

    s = "INSERT INTO query ( qid, key_id ) SELECT %d, key_id FROM query WHERE qid = %d" % ( new_qid, old_qid )
    pdk_db.execute(s)
    pdk_db.commit()

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
