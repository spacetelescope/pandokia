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

    pandokia.config.pdk_db.execute("DELETE FROM hostinfo WHERE hostname = :1",(host,))
    pandokia.config.pdk_db.execute("INSERT INTO hostinfo ( os, description, hostname ) VALUES ( :1, :2, :3 )",(os, description, host))
    pandokia.config.pdk_db.commit()

    print (os, description, host)

