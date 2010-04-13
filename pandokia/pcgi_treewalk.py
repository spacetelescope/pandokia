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


# the left-pointing arrow that appears where we offer to remove a
# constraint
remove_arrow = '<'

debug_cmp = 0

#
# walk the test tree
#
#

def get_form( form, value, default ) :
    if value in form :
        return form[value].value
    else :
        return default

def treewalk ( ) :

    form = pandokia.pcgi.form

    output = sys.stdout

    output.write(common.cgi_header_html)

    global db
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

    context = get_form(form,'context',  '*')
    host    = get_form(form,'host',     '*')
    test_run= get_form(form,'test_run', '*')
    project = get_form(form,'project',  '*')
    status  = get_form(form,'status',   '*')
    contact = get_form(form,'contact',  None)
    attn    = get_form(form,'attn',     '*')

    debug_cmp = get_form(form,'debug_cmp', 0)

    cmp_test_run = get_form(form,'cmp_test_run', test_run)
    cmp_context  = get_form(form,'cmp_context',  context)
    cmp_host     = get_form(form,'cmp_host',     host)

    if cmp_test_run != test_run or cmp_context != context or cmp_host != host :
        comparing = 1
    else :
        comparing = 0

    # not implemented yet
    contact = None

    if form.has_key("rstatus") :
        # rstatus is us overriding our own parameter; instead of changing the cgi parameter
        # string for each field, we just append "rstatus=value" to the link text.
        # status still comes in as "*" or whatever, but we ignore it.
        status = form["rstatus"].value

    # handle special names of test runs
    test_run = common.find_test_run(test_run)

    #
    # query values we will always pass back to the next instantion of ourself
    #

    query = { 
        'test_name' : test_name,
        'test_run' : test_run,
        'project' : project,
        'host': host,
        'status': status,
        'attn': attn,
        'context':context,
        'cmp_test_run' : cmp_test_run,
        'cmp_context' : cmp_context,
        'cmp_host' : cmp_host,
        'contact' : contact,
    }

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

    for var, label in [
        ( 'project', 'project' ),
        ( 'context', 'context' ),
        ( 'host', 'host' ),
        ( 'status', 'status' ),
        ] :

        if query[var] != '*' :
            lquery = copy.copy(query)
            lquery[var] = "*"
            line = s_line % ( label, cgi.escape(query[var]), common.self_href(lquery,"treewalk",remove_arrow)  )
            output.write(line)

    #
    # if a test_run is selected, show the test_run here
    # include a link to clear the test_run selection
    #

    if test_run != "*" :
        lquery = copy.copy(query)
        lquery["test_run"] = "*"
        test_run_line = "<h2>%s = %s &nbsp;&nbsp;&nbsp; %s &nbsp;&nbsp;&nbsp; %s </h2>\n"
        tmp1 = common.self_href(lquery,"treewalk",remove_arrow)
        tmp2 = common.previous_daily(test_run)
        if tmp2 is not None :
            lquery["test_run"] = tmp2
            tmp2 = common.self_href(lquery,"treewalk"," (%s)"%tmp2 )
        else :
            tmp2 = ""
        line = test_run_line % ( "test_run", cgi.escape(test_run), tmp1, tmp2)
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
        output.write(common.self_href(lquery,"treewalk",remove_arrow))
        output.write("&nbsp;")

    output.write("</h2>\n")

    ### end of "Test Prefix: line"

    ### If we are comparing to another test run, show which it is.
    
    if comparing:
        
        lquery = query.copy()

        lquery['cmp_test_run'] = None
        lquery['cmp_context'] = None
        lquery['cmp_host'] = None

	    # Include a link to switch to looking at the other test
	    # run, comparing to this test run.
        # Include a link to stop comparing and just show this one.

        swap_query = query.copy()

        for x in ( 'test_run', 'context', 'host' ) :
            swap_query[x] = query['cmp_'+x]
            swap_query['cmp_'+x] = query[x]

        output.write("<h2>comparing: this - %s %s</h2>\n"% (
            common.self_href(swap_query, "treewalk", cmp_test_run),
            common.self_href(lquery,"treewalk",remove_arrow),
            ) )

    ### show the table

    # "show all" line before the table

    lquery = copy.copy(query)
    show_all_line = common.self_href(lquery, 'treewalk.linkout', "show all")
    output.write(show_all_line)
    output.write("<br><br>")

    ### begin table of test results


    # Gather the names of the rows

    prefixes = collect_prefixes( query )

    table = collect_table( prefixes, query )

    if comparing :
        query_2 = query.copy()
        query_2['test_run'] = cmp_test_run
        t2 = collect_table( prefixes, query_2 )
    
        # This part is very delicate.  We know that both tables
        # have the same dimensions because the parameters that we
        # used to deterimine the number of rows/cols are the same;
        # from that, we also know that the meaning of each cell is
        # the same.
        #
        # So, for each cell, if it appears to contain an int in
	    # both cells, subtract them.
        #
	    # We know that column 1 contains the test name, so we don't
	    # even try to handle those.
        #
        for row in range(0, len(table.rows) ):
            for col in range(1,len(table.rows[row].list)) :
                # pick the table cell out of each table
                c1 = table.get_cell(row,col)
                c2 = t2   .get_cell(row,col)

                # see if we can convert both of them to integers.
                # if not, go on to the next cell
                try :
                    c1v = int(c1.text)
                    c2v = int(c2.text)
                except ValueError :
                    continue

                diff = c1v - c2v
                # poke the new string directly back into the table cell;
                # this preserves the html attributes and such
                if debug_cmp :
                    c1.text="%d - %d = %+d"%(c1v,c2v,diff)
                else :
                    diff = "%+d"%diff
                    if diff == '+0' :
                        diff = '0'
                    c1.text=diff

    ###

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


def query_to_where_str( query, fields ) :
    l = [ ]
    for x in fields :
        if x in query :
            l.append( ( x, query[x] ) )

    where_clause = common.where_str(l)

    return where_clause
    

def collect_prefixes( query ) :
    #
    # first, make a list of the unique prefixes.  This is one of the most
    # potentially painful queries in the system.  It has to look at the
    # record for each test result that is selected, so that it can
    # find the unique set of prefixes for the test names.
    #
    test_name = query['test_name']

    where_clause = query_to_where_str( query, ( 'test_name', 'test_run', 'project', 'host', 'context', 'status', 'attn' ) )

    # if contact is not None :
    #    c = db.execute("SELECT DISTINCT test_name FROM result_scalar, contact %s ORDER BY test_name" % ( where_clause ) )
    #else :
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

    return prefixes


def collect_table( prefixes, query ) :
    #
    # make the actual table to display
    #
    lquery = copy.copy(query)

    status = query['status']

    rownum = 0

    table = text_table.text_table()

    del lquery["status"]

    link=common.selflink(lquery, 'treewalk' )

    table.set_html_table_attributes("border=1")
    table.define_column("test_name")
    table.define_column("count")
    total_col = { }
    count_col = { }
    for x in common.cfg.statuses :
        if ( status == '*' )  or ( x in status ) :
            table.define_column(x,showname=common.cfg.status_names[x],link=link+"&status="+x)
        total_col[x] = 0
        count_col[x] = 0

    total_count = 0

    total_row = rownum
    rownum = rownum + 1

    for this_test_name in prefixes :
        lquery['test_name'] = this_test_name
        where_clause = query_to_where_str( lquery, ( 'test_name', 'test_run', 'project', 'host', 'context', 'status', 'attn' ) )

        if "*" in this_test_name :
            linkmode = 'treewalk'
        else :
            linkmode = 'treewalk.linkout'
        lquery['status'] = status;
        link=common.selflink(lquery, linkmode)

        table.set_value(rownum,"test_name",text=this_test_name, link=link)

        count = 0

        for x in common.cfg.statuses :
            if ( status == '*') or ( x in status ) :
                c = db.execute("SELECT count(*) FROM result_scalar %s AND status = '%s' ORDER BY test_name" % ( where_clause, x) )
                (count_col[x],) = c.fetchone()
                table.set_value(rownum,x,      text=count_col[x],    link=link+"&rstatus="+x )
                count = count + count_col[x]
                total_count = total_count + count_col[x]

        table.set_value(rownum,"count",     text=count )

        for x in total_col :
            total_col[x] += count_col[x]

        rownum = rownum + 1
    
    table.set_value(total_row,"count",     text=total_count )
    for x in common.cfg.statuses :
        if ( status == '*') or ( x in status ) :
            table.set_value(total_row,x,      text=total_col[x] )

    return table
