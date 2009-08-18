#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import cgi
import re
import copy
import time
import string

import urllib

import text_table

def genlink(text, link) :
    return "<a href='"+link+"'>"+text+"</a>"

selflink_cginame = "/huh?"


def sselflink(text, qdict, linkmode = "treewalk") :
    return selflink_cginame+"?query="+linkmode+"&"+urllib.urlencode(qdict)

def selflink(text, qdict, linkmode = "treewalk") :
    return genlink(text,sselflink(text, qdict, linkmode))


def vview_match( name, query_name) :
    # name is the name of the test that we found
    # query_name is the name that we asked for (with implied *query_name*)
    # return value is the prefix we should use
    n = string.rfind(name,query_name)
    if n < 0 :
        return ""
    cp = n+len(query_name)
    while cp < len(name) and name[cp] != '.' and name[cp] != '/' :
        cp = cp + 1
    if cp < len(name) and ( name[cp] == '.' or name[cp] == '/' ) :
        cp = cp + 1
    r = name[:cp]
    return r
    


#
# walk the test tree
#
#

def testwalk ( stash ) :

    form = stash.form

    global selflink_cginame
    selflink_cginame = stash.cginame
    
    output = sys.stdout

    db = stash.open_db()

    #
    # gather up all the expected parameters
    #

    if form.has_key("test_name") :
        test_name = form["test_name"].value
    else :
        test_name = "*"
        
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

    if form.has_key("rstatus") :
        # rstatus is us overriding our own parameter; instead of changing the cgi parameter
        # string for each field, we just append "rstatus=value".  status still comes in
        # as "*" or whatever, but we ignore it.
        status = form["rstatus"].value

    # handle special names of test runs
    test_run = stash.find_test_run(test_run)

    #
    # query values we will always pass back to the next instantion of ourself
    #

    query = { "test_name" : test_name , "test_run" : test_run, "project" : project, "host": host, "status": status }

    #
    # main heading
    #

    output.write("<h1>vview</h1>")

    #
    # if a host is selected, show the host here
    # include a link to clear the host selection
    #

    if host != "*" :
        lquery = copy.copy(query)
        lquery["host"] = ""
        output.write("<h2>host = "+host)
        output.write("&nbsp;&nbsp;&nbsp;")
        output.write(selflink("<",lquery))
        output.write("</h2>\n")

    #
    # if a test_run is selected, show the host here
    # include a link to clear the test_run selection
    #

    if test_run != "*" :
        lquery = copy.copy(query)
        lquery["test_run"] = ""
        output.write("<h2>test_run = "+test_run)
        output.write("&nbsp;&nbsp;&nbsp;")
        output.write(selflink("<",lquery))
        output.write("</h2>\n")


    #
    # if a project is selected, show the host here
    # include a link to clear the project selection
    #

    if project != "*" :
        lquery = copy.copy(query)
        lquery["project"] = ""
        output.write("<h2>project = "+project)
        output.write("&nbsp;&nbsp;&nbsp;")
        output.write(selflink("<",lquery))
        output.write("</h2>\n")
        
    if status != "*" :
        lquery = copy.copy(query)
        lquery["status"] = ""
        output.write("<h2>status = "+status)
        output.write("&nbsp;&nbsp;&nbsp;")
        output.write(selflink("<",lquery))
        output.write("</h2>\n")

        
    output.write("</h2>\n")

    if 1 or (test_run != "*" and project != "*" ) :
        #
        # display the test names present at this level
        #
        output.write("<h3>Choose test</h3>")

        lquery = copy.copy(query)
        output.write(selflink("show all", lquery, "treewalk.linkout" ))
        output.write("<br><br>")

        c = db.execute("SELECT test_name, status FROM result_scalar WHERE test_name GLOB ? AND test_run GLOB ? AND project GLOB ? AND host GLOB ? AND status GLOB ? ORDER BY test_name", ('*'+test_name+'*',test_run,project, host, status))

        lquery = copy.copy(query)
        
        l = len(test_name)
        prev_one = None

        rownum = 0
        table = text_table.text_table()
        del lquery["status"]
        link=sselflink("", lquery )
        table.set_html_table_attributes("border=1")
        table.define_column("test_name")
        table.define_column("count")
        table.define_column("pass",link=link+"&status=P")
        table.define_column("fail",link=link+"&status=F")
        table.define_column("error",link=link+"&status=E")
        table.define_column("disable",link=link+"&status=D")

        count = 0
        count_pass = 0
        count_fail = 0
        count_error = 0
        count_disable = 0

        lquery = copy.copy(query)

        for x in c :
            (r_test_name, r_status ) = x

            this_one = vview_match(r_test_name, test_name )

            if this_one != prev_one :
                if prev_one is not None : 
                    add_line( prev_one+'*', lquery, rownum, count, count_pass, count_fail, count_error, count_disable, l, table)
                    rownum=rownum+1
                    count = 0
                    count_pass = 0
                    count_fail = 0
                    count_error = 0
                    count_disable = 0
                prev_one = this_one

            count = count + 1
            if r_status == 'P' :
                count_pass += 1
            elif r_status == 'F' :
                count_fail += 1
            elif r_status == 'E' :
                count_error += 1
            elif r_status == 'D' :
                count_disable += 1

        if prev_one is not None :
            add_line( prev_one+'*', lquery, rownum, count, count_pass, count_fail, count_error, count_disable, l, table)

        output.write(table.get_html())

        output.write("<br>")
        lquery = copy.copy(query)
        lquery["test_name"]=test_name
        output.write(selflink("show all", lquery, "treewalk.linkout" ))
        output.write("<br>")

    #
    # if no test_run specified, give an option to choose one (but only from the
    # test_runs that are in the tests specified)
    #

    if "*" in test_run :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        output.write("<h3>Narrow to test_run</h3>")
        c = db.execute("SELECT DISTINCT test_run FROM result_scalar WHERE test_name GLOB ? AND test_run GLOB ? AND project GLOB ? AND host GLOB ? AND status GLOB ? ORDER BY host", (test_name+"*",test_run,project, host,status))
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["test_run"] = x
            output.write("<a href='"+stash.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")
        test_run = "*"


    #
    # if no project specified, give an option to choose one (but only from projects
    # that are in the tests specified)
    #

    if "*" in project :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        output.write("<h3>Narrow to project</h3>")
        c = db.execute("SELECT DISTINCT project FROM result_scalar WHERE test_name GLOB ? AND test_run GLOB ? AND project GLOB ? AND host GLOB ? AND status GLOB ? ORDER BY host", (test_name+"*",test_run,project, host, status))
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["project"] = x
            output.write("<a href='"+stash.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")
        project = "*"


    #
    # if no host specified, give an option to choose one (but only from hosts
    # that are in the tests specified)
    #

    if host == "*" :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        output.write("<h3>Narrow to host</h3>")
        c = db.execute("SELECT DISTINCT host FROM result_scalar WHERE test_name GLOB ? AND test_run GLOB ? AND project GLOB ? AND host GLOB ? AND status GLOB ? ORDER BY host", (test_name+"*",test_run,project, host, status))
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["host"] = x
            output.write("<a href='"+stash.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")
        host = "*"



    #
    # bug: put help for the page here
    #
    output.write("")

#
# add a line to the table
#

def add_line( prev_one, lquery, rownum, count, count_pass, count_fail, count_error, count_disable, l, table) :
    # print "->this",this_one," prev", prev_one,"row",rownum,"<br>"
    lquery["test_name"]=prev_one

    y = re.search("[/.]",prev_one[l:])
    if not y :
        linkmode = 'treewalk.linkout'
    else :
        linkmode = 'treewalk'

    # if there is only one, we can link out now
    if count == 1 :
        linkmode = 'treewalk.linkout'

    link=sselflink(prev_one, lquery, linkmode )
    table.set_value(rownum,"test_name",text=prev_one, link=link)
    table.set_value(rownum,"count",     text=count)
    table.set_value(rownum,"pass",      text=count_pass,    link=link+"&rstatus=P" )
    table.set_value(rownum,"fail",      text=count_fail,    link=link+"&rstatus=F" )
    table.set_value(rownum,"error",     text=count_error,   link=link+"&rstatus=E" )
    table.set_value(rownum,"disable",   text=count_disable, link=link+"&rstatus=D" )



def linkout( stash ) :
    #
    # linking out of the test walker and into the test display
    #

    #
    # gather up all the expected parameters
    #

    form = stash.form

    if form.has_key("test_name") :
        test_name = form["test_name"].value
    else :
        test_name = "*"
        
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

    if form.has_key("rstatus") :
        status = form["rstatus"].value

    # create a new qid

    now = time.time()

    qdb = stash.open_qdb()
    c = qdb.execute("INSERT INTO query_id ( time ) VALUES ( ? ) ",(now,))
    qid = c.lastrowid
    qdb.commit()

    # find a list of the tests
    db = stash.open_db()
    c1 = db.execute("SELECT key_id FROM result_scalar WHERE test_name GLOB ? AND test_run GLOB ? AND project GLOB ? AND host GLOB ? AND status GLOB ? ORDER BY host", (test_name,test_run,project, host, status))

    a = [ ]
    for x in c1 :
        (key_id, ) = x
        a.append(key_id)


    if len(a) == 1 :
        pass
        sys.stdout.write('<html><head><meta http-equiv="REFRESH" content="0;'+stash.cginame+ ( '?query=detail&key_id=%s"'%key_id ) + '>\n</head><body>\n' )
        sys.stdout.write( ("redirecting: <a href='"+stash.cginame+"?query=detail&key_id=%s'>key_id = "%key_id) + str(key_id) + " without attributes</a><br>\n" )

    else :

        for key_id in a :
            qdb.execute("INSERT INTO query ( qid, key_id ) VALUES ( ?, ? ) ", (qid, key_id ) )
        qdb.commit()

        sys.stdout.write('<html><head><meta http-equiv="REFRESH" content="0;'+stash.cginame+ ( '?query=summary&qid=%s"'%qid ) + '>\n</head><body>\n' )
        sys.stdout.write( ("redirecting: <a href='"+stash.cginame+"?query=summary&qid=%s'>qid = "%qid) + str(qid) + " without attributes</a><br>\n" )

        # print "<a href='"+stash.cginame+"?query=summary&qid=%s&show_attr=1'>qid = "%qid,qid," with attributes</a>"
