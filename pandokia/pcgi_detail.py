#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import cgi
import re
import copy
import time
import datetime

import pandokia.text_table as text_table

import urllib

import pandokia.pcgi
import pandokia.common as common

import pandokia
cfg = pandokia.cfg

#
# Display the detailed test results
#
# This is the page with the heading at the top and the log text at the bottom
#
#

def run ( ) :

    sys.stdout.write(common.cgi_header_html)

    form = pandokia.pcgi.form

    db = common.open_db()

    if form.has_key("test_name") :
        test_name = form["test_name"].value
    else :
        test_name = ""
        
    if form.has_key("host") :
        host = form["host"].value
    else :
        host = "*"

    if form.has_key("test_run") :
        test_run = form["test_run"].value
    else :
        test_run = "*"

    if form.has_key("project") :
        project = form["project"].value
    else :
        project = "*"

    if form.has_key("status") :
        status = form["status"].value
    else :
        status = "*"

    if form.has_key("test_name") :
        cmp_run = form["test_name"].value
        if cmp_run == '' :
            cmp_run = common.previous_daily(test_run)
            if cmp_run is not None :
                cmp_run = common.find_test_run(cmp_run)
            else :
                cmp_run = ''
        else :
            cmp_run = common.find_test_run(cmp_run)
    else :
        cmp_run = ""

    if form.has_key("key_id") :
        key_id = form["key_id"].value
    else :
        key_id = ""
        
    if form.has_key("qid" ) :
        qid = form["qid"].value
    else :
        qid = ""

    #
    # main heading
    #

    sys.stdout.write("<h1>Test detail</h1>\n")

    #
    # this query finds all the test results that are an interesting part of this request
    #

    if key_id != "" :
        do_result( key_id )
    elif qid != "" :
        qdb = common.open_qdb()
        c1 = qdb.execute("SELECT key_id FROM query WHERE qid = ? ", (qid,) )
        l = [ ] 
        for x in c1 :
            l.append(x[0])
        del c1
        for key_id in l :
            do_result(key_id )
    else :
        c1 = db.execute("SELECT key_id FROM result_scalar WHERE test_run = ? AND project = ? AND host = ? AND test_name = ? ", ( test_run, project, host, test_name ) )
        for x in c1 :
            (key_id, ) = x
            do_result( key_id )
            

def do_result( key_id ) :

    c = common.db.execute("SELECT key_id, test_run, project, host, test_name, status, attn, start_time, end_time, location, test_runner FROM result_scalar WHERE key_id = ? ", ( key_id, ) )
    for x in c :
        ( key_id, test_run, project, host, test_name, status, attn, start_time, end_time, location, test_runner ) = (x)

        linkback_dict = { 'project' : project, 'host' : host, 'test_run' : test_run, 'test_name' : test_name }
        prevday_dict =  { 'project' : project, 'host' : host, 'test_run' : test_run, 'test_name' : test_name }

        row = 0
        tb = text_table.text_table()
        tb.set_html_table_attributes("border=1")
        tb.set_value(row, 0, "test_run")
        tmp = common.previous_daily(test_run) 
        if tmp is not None :
            prevday_dict["test_run"] = tmp
            tmp = test_run + " &nbsp;&nbsp;(view <a href=%s>%s</a>)"%(common.selflink(prevday_dict, linkmode = 'detail'), tmp)
            tb.set_value(row, 1, test_run, html= tmp )
        else :
            tb.set_value(row, 1, test_run)
        row += 1

        tb.set_value(row, 0, "project")
        tb.set_value(row, 1, project)
        row += 1

        tb.set_value(row, 0, "host")
        tb.set_value(row, 1, host)
        row += 1

        tb.set_value(row, 0, "test_name")
        tb.set_value(row, 1, test_name)
        row += 1

        tb.set_value(row, 0, "contact")
        tb.set_value(row, 1, common.get_contact(project, test_name))
        row += 1

        tb.set_value(row, 0, "status")
        if status != "P" :
            tb.set_value(row, 1, text=status, html="<font color=red>"+status+"</font>")
        else :
            tb.set_value(row, 1, status)
        row += 1

        tb.set_value(row, 0, "attn")
        tb.set_value(row, 1, attn)
        row += 1
        
        tb.set_value(row, 0, "test_runner")
        tb.set_value(row, 1, test_runner)
        row += 1
        
        try :
            # ignoring exceptions here because we don't know how good the values in
            # the database are.  some preliminary software does not fill them in
            # correctly, for example.
            tb.set_value(row, 1, float(end_time) - float(start_time) )
            tb.set_value(row, 0, "duration")
            row += 1
        except :
            pass

        # merge all of this into a generalized "get the times" function that
        # can be used anywhere
        if start_time == '0' :
            st = 'unknown'
        else :
            try :
                # you might think that you could use .%f in strftime, but you would be wrong
                # the documentation describes it, but it isn't implemented
                st = datetime.datetime.fromtimestamp(float(start_time))
                st = st.strftime("%Y-%m-%d %H:%M:%S")+"."+"%03d"%(st.microsecond/1000)
            except :
                # it is some non-time_t format - just display it
                st = start_time

        if end_time == '0' :
            et = 'unknown'
        else :
            try :
                # you might think that you could use .%f in strftime, but you would be wrong
                # the documentation describes it, but it isn't implemented
                et = datetime.datetime.fromtimestamp(float(end_time))
                et = et.strftime("%Y-%m-%d %H:%M:%S")+"."+"%03d"%(et.microsecond/1000)
            except :
                # it is some non-time_t format - just display it
                et = end_time

        tb.set_value(row, 0, "start_time")
        tb.set_value(row, 1, st)
        row += 1

        tb.set_value(row, 0, "end_time")
        tb.set_value(row, 1, et)
        row += 1

        tb.set_value(row, 0, "location")
        tb.set_value(row, 1, location)
        row += 1

        c1 = common.db.execute("SELECT name, value FROM result_tda WHERE key_id = ?", (key_id, ) )
        for y in c1 :
            (name, value) = y
            tb.set_value(row, 0, "tda_"+name)
            tb.set_value(row, 1, value)
            row += 1

        c1 = common.db.execute("SELECT name, value FROM result_tra WHERE key_id = ?", (key_id, ) )
        for y in c1 :
            (name, value) = y
            tb.set_value(row, 0, "tra_"+name)
            tb.set_value(row, 1, value)
            row += 1

        sys.stdout.write(tb.get_html())

        sys.stdout.write("<a href=%s>back to treewalk</a><br>\n"%common.selflink(linkback_dict, linkmode = 'treewalk'))

        # if ( test_runner in cfg.flagok_test_runners ) and ( status in cfg.flagok_test_runners[test_runner] ) :
        #     flagok_dict = { 'host':host, 'ok': location, 'key_id': key_id }
        #     flagok_link = "<a href=%s>flagok</a><br>\n" % common.selflink(flagok_dict, linkmode = "flagok")
        #     sys.stdout.write(flagok_link)
        # else :
        flagok_link = ''

        c1 = common.db.execute("SELECT log FROM result_log WHERE key_id = ?", (key_id, ) )
        for y in c1 :
            (y, ) = y
            if y != "" :
                sys.stdout.write("Log:<br><pre>")
                sys.stdout.write(cgi.escape(y))
                sys.stdout.write("</pre>\n")

        sys.stdout.write("<br>\n")

        sys.stdout.write(flagok_link)

        sys.stdout.write("<br><hr>\n")
