#
# pandokia - a test reporting and execution system
# Copyright 2011, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import cgi

import urllib

import pandokia
import pandokia.pcgi
import common

def hostinfo( ) :

    admin = common.current_user() in common.cfg.admin_user_list 

    print common.cgi_header_html

    input_query = pandokia.pcgi.form_to_dict(pandokia.pcgi.form)

    for x in input_query['host'] :
        host, os, description = common.hostinfo(x)
        if os is None :
            os = ''
        if description is None :
            description = ''

        print '<b>%s</b><br>'%cgi.escape(host)

        cols = len(os)
        if cols < 40 :
            cols = 40
        if admin :
            print "<form action=%s method=POST>"%common.get_cgi_name()
            print "<input type=hidden name=query value=set_hostinfo>"
            print "<input type=hidden name=host value=%s>"%host
        print '<input type=text cols=%d name=os value="%s">'%(cols,cgi.escape(os,True))

        l = [ len(s) for s in description.split('\n') ]
        cols = max(l)
        if cols < 40 :
            cols = 40
        rows = len(l)
        if rows < 4 :
            rows = 4
        print "<br><textarea name=description rows=%d cols=%d>%s</textarea>"%(rows,cols, cgi.escape(description))
        if admin :
            print "<br><input type=submit value='change'>"
            print "</form>"

def set_hostinfo() :

    admin = common.current_user() in common.cfg.admin_user_list 

    if not admin :
        pandokia.pcgi.error_1201()
        return

    print "content-type: text/plain\n"

    input_query = pandokia.pcgi.form_to_dict(pandokia.pcgi.form)
    os = input_query['os'][0]
    description = input_query['description'][0]
    host = input_query['host'][0]

    pandokia.cfg.pdk_db.execute("DELETE FROM hostinfo WHERE hostname = :1",(host,))
    pandokia.cfg.pdk_db.execute("INSERT INTO hostinfo ( os, description, hostname ) VALUES ( :1, :2, :3 )",(os, description, host))
    pandokia.cfg.pdk_db.commit()

    print (os, description, host)


def expected() :
    import pandokia.text_table as text_table

    pdk_db = pandokia.cfg.pdk_db
    input_query = pandokia.pcgi.form_to_dict(pandokia.pcgi.form)

    if 'format' in input_query :
        format = input_query['format'][0]
    else :
        format = 'html'

    tbl = text_table.text_table()

    q = { }
    for x in ( 'test_run_type', 'project', 'host', 'context' ) :
        if x in input_query :
            q[x] = input_query[x]

    where_str, where_dict = pdk_db.where_dict( q )


    c_t = pdk_db.execute("SELECT DISTINCT test_run_type FROM expected %s ORDER BY test_run_type " 
            % where_str, where_dict )

    row = 0

    for test_run_type, in c_t :

        prev_project = None

        tbl.set_value(row, 'test_run_type', test_run_type)
        row = row + 1

        q['test_run_type'] = test_run_type

        where_str, where_dict = pdk_db.where_dict( q )

        c = pdk_db.execute("SELECT DISTINCT  project, host, context, count(*) FROM "
            "expected %s GROUP BY project, host, context ORDER BY project, host, context "
            % where_str, where_dict )

        for x in c :
            if x[0] != prev_project :
                tbl.set_value(row, 'project', x[0])
                prev_project = x[0]

            for number, name in enumerate( ( 'host', 'context', 'count' ) ):
                tbl.set_value(row,name, x[number+1])
            row = row + 1

    tbl.pad()
    if format == 'html' :
        print "content-type: text/html\n"
        print "<h2>Expected test summary</h2>"
        tbl.set_html_table_attributes(' border=1 ')
        print tbl.get_html(headings=1)
    else :
        print "content-type: text/plain\n"
        print tbl.get(format=format, headings=1)
