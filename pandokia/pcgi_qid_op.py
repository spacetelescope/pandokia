#
# pandokia - a test reporting and execution system
# Copyright 2010, Association of Universities for Research in Astronomy (AURA) 
#

#
# operations on a qid
#

import sys
import cgi
import re
import copy
import time
import os

import urllib

import pandokia
pdk_db = pandokia.cfg.pdk_db

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

    form = pandokia.pcgi.form

    qid = int(form['qid'].value)

    output.write('<h2>QID = %d</h2>' % qid )

    output.write('<p>operate on this QID</p>' )

    change = 0

    if 'other' in form :
        other_qid = int( form['other'].value )

    if 'nameremove' in form :
        #####

        output.write('nameremove operation<br>')
        c = pdk_db.execute("SELECT result_scalar.test_name FROM result_scalar, query WHERE query.qid = %d AND query.key_id = result_scalar.key_id " % other_qid )
        remove_names = [ ]
        for x, in c :
            remove_names.append(x)

        remove_key_ids = [ ]

        c = pdk_db.execute("SELECT query.key_id, result_scalar.test_name  FROM query, result_scalar WHERE query.qid = %d AND query.key_id = result_scalar.key_id" % qid)
        for key_id, name in c :
            if name in remove_names :
                remove_key_ids.append(key_id)

        for key_id in remove_key_ids :
            pdk_db.execute("DELETE FROM query WHERE query.qid = %d AND query.key_id = %d" % (qid, key_id))

        pdk_db.commit()
        change=1

    if 'add' in form :
        pdk_db.execute( "INSERT INTO query ( qid, key_id ) SELECT %d, key_id FROM query WHERE qid = %d AND key_id NOT IN ( SELECT key_id FROM query WHERE qid = %d )" % ( qid, other_qid, qid ) )
        pdk_db.commit()
        change = 1

    if 'remove' in form :
        # mysql doesn't like it if you 
        #       DELETE FROM query WHERE ... IN ( SELECT ... FROM query )
        pdk_db.execute("CREATE TEMPORARY TABLE IF NOT EXISTS temporary_xyzzy ( key_id INTEGER )")
        pdk_db.execute("INSERT INTO temporary_xyzzy ( key_id ) SELECT key_id FROM query WHERE qid = %d " % other_qid )
        pdk_db.execute("DELETE FROM query WHERE ( qid = %d ) AND ( key_id IN ( SELECT key_id FROM temporary_xyzzy ) ) "
            % ( qid, ) )
        pdk_db.execute("DELETE FROM temporary_xyzzy")
        pdk_db.commit()
        change = 1

    if change or 1:
        c = pdk_db.execute("SELECT COUNT(*) FROM query WHERE query.qid = %d"%qid)
        x = c.fetchone()
        output.write('%d rows<br>'%x[0])

    output.write('<br>')

    output.write( "<a href='"+common.selflink( { 'qid' : qid } , linkmode = "summary")+"'>" )
    output.write('back to summary page')
    output.write('</a> <br>\n')

    
    #
    # present an input field and possible actions
    #

    output.write('<br>')

    output.write('<form action=%s method=GET>'%common.get_cgi_name())
    output.write('<input type=hidden name=query value=qid_op>')
    output.write('<input type=hidden name=qid value=%d>'%qid)

    output.write('Enter another qid:<br><input type=text name=other><br><br>')

    output.write('<input type=submit name=nameremove value="Remove tests that have the same test_name as tests in the other QID"> <br><br>\n')
    output.write('<input type=submit name=add value="Add tests from the other QID by key"> <br>\n')
    output.write('<input type=submit name=remove value="Remove tests that are also in other QID by key"> <br>\n')
    output.write('</form>')


def qid_list( ) :
    import datetime

    print "content-type: text/html\n"
    print common.page_header()

    print "<h1>Interesting QID</h1>"

    input_query = pandokia.pcgi.form_to_dict(pandokia.pcgi.form)

    order_by = 'qid'
    order_dir = 'asc'
    if 'order_by' in input_query :
        x = input_query['order_by'][0]
        if x in ( 'qid', 'expires', 'username', 'notes' ):
            order_by = x
    if 'order_dir' in input_query :
        x = input_query['order_dir'][0]
        if x in ( 'asc', 'desc' ) :
            order_dir = x

    def sl(s) :
        d = 'asc' 
        if order_dir == 'asc' :
            d = 'desc'
        return common.selflink( { 'order_by' : s, 'order_dir' : d }, linkmode='qid_list' )

    t = text_table.text_table()
    t.define_column("QID",      html='<a href=%s>QID</a>'%sl('qid') )
    t.define_column("Expires",  html='<a href=%s>expires</a>'%sl('expires') )
    t.define_column("User",     html='<a href=%s>username</a>'%sl('username') )
    t.define_column("Notes",    html='<a href=%s>notes</a>'%sl('notes') )
    t.set_html_table_attributes("border=1")

    qdict = { }

    c = pdk_db.execute("SELECT qid, expires, username, notes FROM query_id WHERE expires = :1 OR username <> '' OR notes <> '' ORDER BY %s %s"%(order_by,order_dir),(pandokia.never_expires,))
    row = 0
    for x in c :

        v = int(x[0])
        qdict['qid']=v
        t.set_value(row,0,v,html='<a href="%s">%s</a>'%( common.selflink(qdict, linkmode = "summary"), v ) )

        try :
            v = int(x[1])
            if v == pandokia.never_expires :
                v = 'never'
            else :
                v = str(datetime.date.fromtimestamp(v))
        except :
            v= '?'
        t.set_value(row,1,v)

        v = str(x[2])
        t.set_value(row,2,v,html=cgi.escape(v))

        if x[3] is None :
            v = ''
        else :
            v = str(x[3])
        t.set_value(row,3,v,html='<pre>'+cgi.escape(v)+'</pre>')

        row = row + 1

    print t.get_html()
