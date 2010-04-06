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

import pandokia.text_table as text_table
import pandokia.pcgi
import common


#
# walk the test tree
#
#

def treewalk ( ) :

    form = pandokia.pcgi.form

    output = sys.stdout

    output.write(common.cgi_header_html)

    db = common.open_db()

    #
    # gather up all the expected parameters
    #

    if form.has_key("test_name") :
        test_name = form["test_name"].value
        if test_name == '' :
            test_name = '*'
    else :
        test_name = "*"
        
    if form.has_key("context") :
        context = form["context"].value
    else :
        context = "*"

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

    if form.has_key("contact") :
        contact = form["contact"].value
    else :
        contact = None

    # not implemented yet
    contact = None

    if form.has_key("rstatus") :
        # rstatus is us overriding our own parameter; instead of changing the cgi parameter
        # string for each field, we just append "rstatus=value" to the link text.
        # status still comes in as "*" or whatever, but we ignore it.
        status = form["rstatus"].value

    if form.has_key("attn") :
        attn = form["attn"].value
    else :
        attn = '*'

    # handle special names of test runs
    test_run = common.find_test_run(test_run)

    #
    # query values we will always pass back to the next instantion of ourself
    #

    query = { "test_name" : test_name , "test_run" : test_run, "project" : project, "host": host, "status": status, "attn": attn, "context":context }

    if contact is not None :
        query['contact'] = contact

    #
    # main heading
    #

    output.write("<h1>Test tree browser</h1>")

    #
    # if a context is selected, show the context here
    # include a link to clear the context selection
    #

    s_line = "<h2>%s = %s &nbsp;&nbsp;&nbsp; %s </h2>\n"


    #
    # if a context is selected, show the context here
    # include a link to clear the context selection
    #

    if context != "*" :
        lquery = copy.copy(query)
        lquery["context"] = "*"
        line = s_line % ( "context", cgi.escape(context), common.self_href(lquery,"treewalk","<-")  )
        output.write(line)


    #
    # if a host is selected, show the host here
    # include a link to clear the host selection
    #

    s_line = "<h2>%s = %s &nbsp;&nbsp;&nbsp; %s </h2>\n"

    if host != "*" :
        lquery = copy.copy(query)
        lquery["host"] = "*"
        line = s_line % ( "host", cgi.escape(host), common.self_href(lquery,"treewalk","<-")  )
        output.write(line)

    #
    # if a test_run is selected, show the test_run here
    # include a link to clear the test_run selection
    #

    if test_run != "*" :
        lquery = copy.copy(query)
        lquery["test_run"] = "*"
        test_run_line = "<h2>%s = %s &nbsp;&nbsp;&nbsp; %s &nbsp;&nbsp;&nbsp; %s </h2>\n"
        tmp1 = common.self_href(lquery,"treewalk","<-")
        tmp2 = common.previous_daily(test_run)
        if tmp2 is not None :
            lquery["test_run"] = tmp2
            tmp2 = common.self_href(lquery,"treewalk"," (%s)"%tmp2 )
        else :
            tmp2 = ""
        line = test_run_line % ( "test_run", cgi.escape(test_run), tmp1, tmp2)
        output.write(line)

    #
    # if a project is selected, show the project here
    # include a link to clear the project selection
    #

    if project != "*" :
        lquery = copy.copy(query)
        lquery["project"] = "*"
        line = s_line % ( 'project', cgi.escape(project), common.self_href(lquery,"treewalk","<-"))
        output.write(line)

    #
    # if a status is selected, blah blah
    #

    if status != "*" :
        lquery = copy.copy(query)
        lquery["status"] = "*"
        line = s_line % ( "status", cgi.escape(status), common.self_href(lquery,"treewalk","<-"))
        output.write(line)


    ### start of "Test Prefix: line"

    #
    # Here is the actual tree browser for test names.  we are at some
    # prefix (specified by test_name), walking down the tree
    #

    output.write( "<h2>Test Prefix: ")

    #
    # show the prefix.  each component of the prefix is a link back
    # up to that level
    #
    lquery = copy.copy(query)

    # get a list of the levels
    t = test_name
    lst = [ ]
    while 1 :
        y = re.search("[/.]",t)
        if not y :
            break
        lst.append(t[0:y.start()+1])
        t = t[y.start()+1:]

    # display each level with the link
    t = ""
    for x in lst :
        t = t + x
        lquery["test_name"] = t+"*"
        line = common.self_href(lquery, 'treewalk', cgi.escape(x))
        output.write(line)

    # if we are not at the very top, also include a link that gets us back
    # to "" (i.e. no prefix at all)
    if test_name != "*" :
        lquery["test_name"]=""
        output.write("&nbsp;&nbsp;&nbsp;")
        output.write(common.self_href(lquery,"treewalk","<-"))
        output.write("&nbsp;")

    output.write("</h2>\n")

    ### end of "Test Prefix: line"


    #
    # display the test names present at this level
    #
    output.write("<h3>Choose test</h3>")

    lquery = copy.copy(query)
    show_all_line = common.self_href(lquery, 'treewalk.linkout', "show all")
    output.write(show_all_line)
    output.write("<br><br>")

    ### begin table of test results

    #
    # first, make a list of the unique prefixes.  This is one of the most
    # potentially painful queries in the system.  It has to look at the
    # record for each test result that is selected, so that it can
    # find the unique set of prefixes for the test names.
    #
    where_clause = common.where_str([ 
        ('test_name', test_name),
        ('test_run', test_run), 
        ('project', project),
        ('host', host),
        ('context', context),
        ('status', status),
        ('attn', attn),
        ])

    if contact is not None :
        c = db.execute("SELECT DISTINCT test_name FROM result_scalar, contact %s ORDER BY test_name" % ( where_clause ) )
    else :
        c = db.execute("SELECT DISTINCT test_name FROM result_scalar %s ORDER BY test_name" % where_clause )

    l = len(test_name)
    prev_one = None

    prefixes = [ ]

    for x in c :
        (r_test_name,) = x

        y = re.search("[/.]",r_test_name[l:])
        if not y :
            # This happens when there is no more hierarchy to follow
            y = len(r_test_name[l:])
            this_one = r_test_name[:l+y+1]
        else :
            # This happens when there are still more levels after this one
            y = y.start()
            this_one = r_test_name[:l+y+1]+"*"

        if this_one != prev_one :
            if prev_one is not None : 
                prefixes.append(prev_one)
            prev_one = this_one

    if prev_one is not None :
        prefixes.append(prev_one)


    #
    # now, make the actual table to display
    #
    lquery = copy.copy(query)
    rownum = 0
    table = text_table.text_table()
    del lquery["status"]
    link=common.selflink(lquery, 'treewalk' )
    table.set_html_table_attributes("border=1")
    table.define_column("test_name")
    table.define_column("count")
    if ( status == '*' )  or ( 'P' in status ) :
        table.define_column("pass",link=link+"&status=P")
    if ( status == '*' )  or ( 'F' in status ) :
        table.define_column("fail",link=link+"&status=F")
    if ( status == '*' )  or ( 'E' in status ) :
        table.define_column("error",link=link+"&status=E")
    if ( status == '*' )  or ( 'M' in status ) :
        table.define_column("missing",link=link+"&status=M")
    if ( status == '*' )  or ( 'D' in status ) :
        table.define_column("disable",link=link+"&status=D")

    total_count = 0
    total_count_pass = 0
    total_count_fail = 0
    total_count_error = 0
    total_count_disable = 0
    total_count_missing = 0

    total_row = rownum
    rownum = rownum + 1

    for this_test_name in prefixes :
        where_clause = common.where_str([ 
            ('test_name', this_test_name),
            ('test_run', test_run), 
            ('project', project),
            ('host', host),
            ('context', context),
            ('attn',attn),
            ])

        lquery['test_name'] = this_test_name
        if "*" in this_test_name :
            linkmode = 'treewalk'
        else :
            linkmode = 'treewalk.linkout'
        lquery['status'] = status;
        link=common.selflink(lquery, linkmode)

        table.set_value(rownum,"test_name",text=this_test_name, link=link)

        count = 0
        count_pass = 0
        count_fail = 0
        count_error = 0
        count_disable = 0
        count_missing = 0

        if ( status == '*') or ( 'P' in status ) :
            c = db.execute("SELECT count(*) FROM result_scalar %s AND status = 'P' ORDER BY test_name" % where_clause)
            (count_pass,) = c.fetchone()
            table.set_value(rownum,"pass",      text=count_pass,    link=link+"&rstatus=P" )

        if ( status == '*') or ( 'F' in status ) :
            c = db.execute("SELECT count(*) FROM result_scalar %s AND status = 'F' ORDER BY test_name" % where_clause)
            (count_fail,) = c.fetchone()
            table.set_value(rownum,"fail",      text=count_fail,    link=link+"&rstatus=F" )

        if ( status == '*') or ( 'E' in status ) :
            c = db.execute("SELECT count(*) FROM result_scalar %s AND status = 'E' ORDER BY test_name" % where_clause)
            (count_error,) = c.fetchone()
            table.set_value(rownum,"error",     text=count_error,   link=link+"&rstatus=E" )

        if ( status == '*') or ( 'M' in status ) :
            c = db.execute("SELECT count(*) FROM result_scalar %s AND status = 'M' ORDER BY test_name" % where_clause)
            (count_missing,) = c.fetchone()
            table.set_value(rownum,"missing",     text=count_missing,   link=link+"&rstatus=M" )

        if ( status == '*') or ( 'D' in status ) :
            c = db.execute("SELECT count(*) FROM result_scalar %s AND status = 'D' ORDER BY test_name" % where_clause)
            (count_disable,) = c.fetchone()
            table.set_value(rownum,"disable",   text=count_disable, link=link+"&rstatus=D" )

        count = count_pass+count_fail+count_error+count_missing+count_disable

        table.set_value(rownum,"count",     text=count )

        total_count += count 
        total_count_pass += count_pass 
        total_count_fail += count_fail 
        total_count_error += count_error 
        total_count_disable += count_disable 
        total_count_missing += count_missing 

        rownum = rownum + 1
    
    table.set_value(total_row,"count",     text=total_count )
    table.set_value(total_row,"pass",      text=total_count_pass )
    table.set_value(total_row,"fail",      text=total_count_fail )
    table.set_value(total_row,"error",      text=total_count_error )
    table.set_value(total_row,"missing",      text=total_count_missing )
    table.set_value(total_row,"disable",      text=total_count_disable )

    output.write(table.get_html())

    output.write("<br>")
    output.write(show_all_line)
    output.write("<br>")

    output.flush()

    #
    # if no test_run specified, give an option to choose one (but only from the
    # test_runs that are in the tests specified)
    #

    if "*" in test_run :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        output.write("<h3>Narrow to test_run</h3>")

        where_clause = common.where_str([ 
            ('test_name', test_name+"*"),
            ('test_run', test_run), 
            ('project', project),
            ('host', host),
            ('context', context),
            ('status', status),
            ('attn',attn),
            ])
        c = db.execute("SELECT DISTINCT test_run FROM result_scalar %s ORDER BY test_run" % where_clause)
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["test_run"] = x
            output.write("<a href='"+pandokia.pcgi.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")


    #
    # if no project specified, give an option to choose one (but only from projects
    # that are in the tests specified)
    #

    if "*" in project :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        output.write("<h3>Narrow to project</h3>")
        where_clause = common.where_str([ 
            ('test_name', test_name+"*"),
            ('test_run', test_run), 
            ('project', project),
            ('host', host),
            ('context', context),
            ('status', status),
            ('attn', attn),
            ])
        c = db.execute("SELECT DISTINCT project FROM result_scalar %s ORDER BY project" % where_clause )
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["project"] = x
            output.write("<a href='"+pandokia.pcgi.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")
        project = "*"


    #
    # if no host specified, give an option to choose one (but only from hosts
    # that are in the tests specified)
    #

    if host == "*" :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        where_clause = common.where_str([ 
            ('test_name', test_name+"*"),
            ('test_run', test_run), 
            ('project', project),
            ('host', host),
            ('context', context),
            ('status', status),
            ('attn', attn),
            ])
        output.write("<h3>Narrow to host</h3>")
        c = db.execute("SELECT DISTINCT host FROM result_scalar %s ORDER BY host" % where_clause)
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["host"] = x
            output.write("<a href='"+pandokia.pcgi.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")
        host = "*"

    #
    # if no context specified, give an option to choose one (but only from contexts
    # that are in the tests specified)
    #

    if context == "*" :
        lquery = { }
        for x in query :
            lquery[x] = query[x]
        where_clause = common.where_str([ 
            ('test_name', test_name+"*"),
            ('test_run', test_run), 
            ('project', project),
            ('host', host),
            ('context', context),
            ('status', status),
            ('attn', attn),
            ])
        output.write("<h3>Narrow to context</h3>")
        c = db.execute("SELECT DISTINCT context FROM result_scalar %s ORDER BY context" % where_clause)
        for x in c :
            (x,) = x
            if x is None :
                continue
            lquery["context"] = x
            output.write("<a href='"+pandokia.pcgi.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")
        context = "*"

    output.write("")

def linkout( ) :
    #
    # linking out of the test walker and into the test display
    #
    # This does not actually display anything.  It makes an entry in the qdb
    # database that contains a list of test results, then redirects to the
    # cgi that displays that.
    #
    # This function is sql safe because it uses where_str() to make the query
    # It is html safe because it only outputs values that are created here.

    output = sys.stdout

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

    if form.has_key("test_name") :
        test_name = form["test_name"].value
    else :
        test_name = "*"
        
    if form.has_key("context") :
        context = form["context"].value
    else :
        context = "*"
        
    if form.has_key("host") :
        host = form["host"].value
    else :
        host = "*"

    if form.has_key("test_run") :
        test_run = form["test_run"].value
    else :
        test_run = "*"
    # handle special names of test runs
    test_run = common.find_test_run(test_run)

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

    if form.has_key("attn") :
        attn = form["attn"].value
    else :
        attn = '*'

    # create a new qid - this is the identity of a list of test results

    now = time.time()

    c = qdb.execute("INSERT INTO query_id ( time ) VALUES ( ? ) ",(now,))
    qid = c.lastrowid
    qdb.commit()

    # find a list of the tests
    where_clause = common.where_str([ 
        ('test_name', test_name),
        ('test_run', test_run), 
        ('project', project),
        ('host', host),
        ('context', context),
        ('status', status),
        ('attn', attn),
        ])

    c1 = db.execute("SELECT key_id FROM result_scalar %s" % where_clause )

    a = [ ]
    for x in c1 :
        (key_id, ) = x
        a.append(key_id)

    # Enter the test results into the qdb with the current qid, then
    # redirect to displaying the qid.  That will get the user the list of
    # all tests.

    # (This used to link directly to the detail display if there was only one,
    # but that makes the checkboxes unavailable in that case.)

    for key_id in a :
        qdb.execute("INSERT INTO query ( qid, key_id ) VALUES ( ?, ? ) ", (qid, key_id ) )
    qdb.commit()

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

