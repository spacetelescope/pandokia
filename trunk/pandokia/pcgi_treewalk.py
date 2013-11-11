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
pdk_db = pandokia.cfg.pdk_db

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

    output.write(common.page_header())

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
    attn    = get_form(form,'attn',     '*')
    qid     = get_form(form,'qid',      None)

    debug_cmp = get_form(form,'debug_cmp', 0)

    # look for input from the compare form
    cmp_test_run = get_form(form,'cmp_test_run', None )
    cmp_context  = get_form(form,'cmp_context',  None )
    cmp_host     = get_form(form,'cmp_host',     None )

    test_run     = common.find_test_run(test_run)
    if cmp_test_run :
        cmp_test_run = common.find_test_run(cmp_test_run)

    # look for whether the query asks for a comparison; we assume not
    comparing = 0
    if 'compare' in form :
        # ok, it explicitly says one of the 3 comparison values
        comparing = 1
        x = get_form(form,'compare','0')

        if x == '' or x == '0' or x.startswith('Turn Off') :
            # if it is a special value that ends the compare, 
            comparing = 0

        if x.startswith('Reverse') :
            t = cmp_test_run
            cmp_test_run = test_run
            test_run = t

            t = cmp_host
            cmp_host = host
            host = t

            t = cmp_context
            cmp_context = context
            context = t

            comparing = 1


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
        'compare' : comparing,
    }

    if qid is not None :
        qid = int(qid)
        query['qid']= qid

    if cmp_test_run is not None :
        query['cmp_test_run'] =  cmp_test_run

    if cmp_context is not None :
        query['cmp_context'] = cmp_context

    if cmp_host is not None :
        query['cmp_host'] = cmp_host


    #
    # show the narrowing parameters
    #

    header_table = text_table.text_table()
    header_table.set_html_table_attributes( ' style="font-size: large; font-weight: bold" ' )

    row = 0

    #
    # if a test_run is selected, show the test_run here
    # include a link to clear the test_run selection
    #

    if test_run != "*" :
        lquery = copy.copy(query)
        lquery["test_run"] = "*"
        test_run_line = "<h2>%s = %s &nbsp;&nbsp;&nbsp; %s &nbsp;&nbsp;&nbsp; %s &nbsp;&nbsp;&nbsp; %s</h2>\n"
        header_table.set_value( row, 0, 'test_run' )
        header_table.set_value( row, 1, '=' )
        header_table.set_value( row, 2, cgi.escape(test_run) )
        header_table.set_value( row, 3, html=common.self_href(lquery,"treewalk",remove_arrow) )
        tmp2 = common.run_previous(None,test_run)
        tmp3 = common.run_next(None,test_run)

        if tmp2 is not None :
            lquery["test_run"] = tmp2
            tmp2 = common.self_href(lquery,"treewalk"," (%s)"%tmp2 )
            header_table.set_value( row, 4, html=tmp2 )
        else :
            tmp2 = ""

        if tmp3 is not None :
            lquery["test_run"] = tmp3
            tmp3 = common.self_href(lquery,"treewalk"," (%s)"%tmp3 )
            header_table.set_value( row, 5, html=tmp3 )
        else :
            tmp3 = ""

        row = row + 1

    for var, label in [
        ( 'project', 'project' ),
        ( 'host', 'host' ),
        ( 'context', 'context' ),
        ( 'status', 'status' ),
        ] :

        if query[var] != '*' :
            lquery = copy.copy(query)
            lquery[var] = "*"
            header_table.set_value( row, 0, label )
            header_table.set_value( row, 1, '=' )
            header_table.set_value( row, 2, cgi.escape(query[var]) )
            header_table.set_value( row, 3, html=common.self_href(lquery,"treewalk",remove_arrow) )
            row = row + 1

    if qid is not None :
        header_table.set_value( row, 0, 'QID' )
        header_table.set_value( row, 2, str(qid) )
        row = row + 1


    print header_table.get_html()

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

    ### offer the form to compare with other runs
    print cmp_form(query, comparing)
    print "<p>"

    ### show the table

    # "show all" line before the table

    lquery = copy.copy(query)
    if comparing :
        t = 'show all (not just different)'
    else :
        t = 'show all'
    show_all_line = common.self_href(lquery, 'treewalk.linkout', t) + ' - '
    lquery['add_attributes'] = 1
    show_all_line += common.self_href(lquery, 'treewalk.linkout', 'with attributes')
    lquery['add_attributes'] = 2
    show_all_line += ' - ' + common.self_href(lquery, 'treewalk.linkout', 'Column Selector')
    output.write(show_all_line)
    output.write("<br>")

    ### begin table of test results


    # Gather the names of the rows

    prefixes = collect_prefixes( query )

    # create the table to display; if comparing, we want a link for
    # every table cell; this is because we don't know later which cells
    # we will need to have a link on
    table = collect_table( prefixes, query, comparing )

    if comparing :
        query_2 = query.copy()
        query_2['test_run'] = cmp_test_run
        query_2['host'] = cmp_host
        query_2['context'] = cmp_context
        t2 = collect_table( prefixes, query_2, 1 )
    
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

                # suppress the link in this cell, but only if both
                # parts of the comparison are zero.  If they are equal,
                # you still might follow the link and see something.
                if c1v == 0 and c2v == 0 :
                    c1.link = None

                # compute the difference and poke the value directly back
                # into the table cell; this preserves the html attributes
                # and such
                diff = c1v - c2v
                if debug_cmp :
                    c1.text="%d - %d = %+d"%(c1v,c2v,diff)
                else :
                    if diff == 0 :
                        c1.text='0'
                    else :
                        c1.text = "%+d"%diff

    ###

    ### If we are comparing to another test run, show which it is.
    
    if comparing:
        

        output.write("<p>Net difference in counts, this - other</p>")


    output.write(table.get_html())

    output.write("<br>")
    output.write(show_all_line)
    output.write("<br>")

    output.flush()

    #
    # if no test_run specified, give an option to choose one (but only from the
    # test_runs that are in the tests specified)
    #

    if 'qid' in query :
        return  # bug: temporary work-around.  the narrow-to query is really slow, but doesn't really help the tree walker in qid mode
        more_where = ' qid = %d AND result_scalar.key_id = query.key_id ' % int(query['qid'])
    else :
        more_where = None

    # bug: This whole thing could happen early.  Then, when you find
    # exactly 1 item in the choices to narrow, you could automatically
    # include that in all the links.
    for field in ( 'test_run', 'project', 'context', 'host' ) :
        if not '*' in query[field] :
            continue
        lquery = { }
        for x in query :
            if query[x] is not None :
                lquery[x] = query[x]
        output.write("<h3>Narrow to %s</h3>" % field)

        tn = test_name
        if not tn.endswith("*") :
            tn = tn + "*" 
        where_text, where_dict = pdk_db.where_dict([ 
            ('test_name', tn),
            ('test_run', test_run), 
            ('project', project),
            ('host', host),
            ('context', context),
            ('status', status),
            ('attn',attn),
            ], more_where )

        if more_where is None :
            c = pdk_db.execute("SELECT DISTINCT %s FROM result_scalar %s GROUP BY %s ORDER BY %s" % ( field, where_text, field, field ), where_dict)
        else :
            c = pdk_db.execute("SELECT DISTINCT %s FROM result_scalar, query %s GROUP BY %s ORDER BY %s" % ( field, where_text, field, field ), where_dict)
        for x, in c :
            if x is None :
                continue
            lquery[field] = x
            output.write("<a href='"+pandokia.pcgi.cginame+"?query=treewalk&"+urllib.urlencode(lquery)+"'>"+x+"</a><br>")


    output.write("")

##########
#
# link out to summary page
#

def linkout( ) :
    #
    # linking out of the test walker and into the test display
    #
    # This does not actually display anything.  It makes an entry in the
    # poorly named "query" table database that contains a list of test
    # results, then redirects to the cgi that displays that.
    #
    # It is html safe because it only outputs values that are created here.

    output = sys.stdout

    output.write(common.cgi_header_html)
    output.write(common.page_header())

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

    context = get_form(form,'context',  '*')
    host    = get_form(form,'host',     '*')
    test_run= get_form(form,'test_run', '*')
    project = get_form(form,'project',  '*')
    status  = get_form(form,'status',   '*')
    attn    = get_form(form,'attn',     '*')
    oldqid  = get_form(form,'qid',      None)
    test_name=get_form(form,'test_name','*')

    # handle special names of test runs
    test_run = common.find_test_run(test_run)

    # create a new qid - this is the identity of a list of test results

    now = time.time()
    expire = now+common.cfg.default_qid_expire_days*86400

    if pdk_db.next :
        newqid = pdk_db.next('sequence_qid')
        c = pdk_db.execute("INSERT INTO query_id ( qid, time, expires ) VALUES ( :1, :2, :3 ) ", 
            ( newqid, now, expire ) )
    else :
        c = pdk_db.execute("INSERT INTO query_id ( time, expires ) VALUES ( :1, :2 ) ", 
            ( now, expire ) )
        newqid = c.lastrowid

    print "content-type: text/plain\n"
    print "QID ",newqid
    pdk_db.commit()

    if oldqid is not None :
        print "WITH QID=",oldqid
        more_where = ' qid = %d AND result_scalar.key_id = query.key_id ' % int(oldqid)
    else :
        more_where = None

    # find a list of the tests
    where_text, where_dict = pdk_db.where_dict([ 
        ('test_name', test_name),
        ('test_run', test_run), 
        ('project', project),
        ('host', host),
        ('context', context),
        ('status', status),
        ('attn', attn),
        ], more_where = more_where )

    if oldqid is None :
        c1 = pdk_db.execute("SELECT key_id FROM result_scalar "+where_text, where_dict )
    else :
        c1 = pdk_db.execute("SELECT result_scalar.key_id FROM result_scalar, query %s" % where_text, where_dict )

    a = [ ]
    for x in c1 :
        (key_id, ) = x
        a.append(key_id)

    # Enter the test results with the current qid, then redirect to
    # displaying the qid.  That will get the user the list of all tests.

    # (This used to link directly to the detail display if there was only one,
    # but that makes the checkboxes unavailable in that case.)

    for key_id in a :
        pdk_db.execute("INSERT INTO query ( qid, key_id ) VALUES ( :1, :2 ) ", (newqid, key_id ) )
    pdk_db.commit()

    url = pandokia.pcgi.cginame + ( '?query=summary&qid=%s' % newqid )

    if form.has_key('add_attributes') :
        x = int(form['add_attributes'].value)
        if x :
            url += ('&show_attr=%d'%x)

    if not no_redirect :
        output.write(
            "<html><head><meta http-equiv='REFRESH' content='0;%s'>\n</head><body>\n" % url
            )
    output.write( 
        "redirecting: <a href='%s'> qid = %s </a><br>\n" % ( url, newqid )
        )

##########
#
# functions
#

def query_to_where_tuple( query, fields, more_where = None ) :
    l = [ ]
    for x in fields :
        if x in query :
            v = query[x]
            l.append( ( x, v ) )

    return pdk_db.where_dict(l, more_where = more_where)

def collect_prefixes( query ) :
    #
    # first, make a list of the unique prefixes.  This is one of the most
    # potentially painful queries in the system.  It has to look at the
    # record for each test result that is selected, so that it can
    # find the unique set of prefixes for the test names.
    #
    test_name = query['test_name']

    have_qid = 'qid' in query
    if have_qid :
        qid = int(query['qid'])
        more_where = "query.qid = %d  AND query.key_id = result_scalar.key_id" % qid
    else :
        more_where = None

    where_text, where_dict = query_to_where_tuple( query, ( 'test_name', 'test_run', 'project', 'host', 'context', 'status', 'attn' ), more_where )

    if not have_qid :
        c = pdk_db.execute("SELECT DISTINCT test_name FROM result_scalar %s GROUP BY test_name ORDER BY test_name" % where_text, where_dict )
    else :
        sys.stdout.flush()
        c = pdk_db.execute("SELECT DISTINCT test_name FROM result_scalar, query %s GROUP BY test_name ORDER BY test_name" % where_text, where_dict )

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


def collect_table( prefixes, query, always_link ) :
    #
    # make the actual table to display
    #
    # always_link=true means to always create an html link in the table
    #    cell that contains a record count
    # always_link=false means to suppress the link if the record count is 0

    status = query['status']

    rownum = 0

    table = text_table.text_table()

    table.set_html_table_attributes("border=1")
    table.define_column("test_name")
    table.define_column("count")
    total_col = { }
    count_col = { }
    lquery = copy.copy(query)
    for x in common.cfg.statuses :
        if ( status == '*' )  or ( x in status ) :
            lquery['status'] = x
            table.define_column(x,showname=common.cfg.status_names[x],link=common.selflink(lquery, 'treewalk' ))
        total_col[x] = 0
        count_col[x] = 0

    total_count = 0

    total_row = rownum
    rownum = rownum + 1

    have_qid = 'qid' in query
    if have_qid :
        qid = int(query['qid'])
        more_where = ' qid = %d AND result_scalar.key_id = query.key_id ' % qid
    else :
        more_where = None

    for this_test_name in prefixes :
        lquery['test_name'] = this_test_name

        if "*" in this_test_name :
            linkmode = 'treewalk'
        else :
            linkmode = 'treewalk.linkout'

        lquery['status'] = status;

        table.set_value(rownum,"test_name",text=this_test_name, link=common.selflink(lquery, linkmode))

        table.set_html_cell_attributes(rownum, 'test_name', 'align="left"' )

        count = 0

        for x in common.cfg.statuses :
            if ( status == '*') or ( x in status ) :
                lquery['status'] = x
                where_text, where_dict = query_to_where_tuple( lquery, ( 'test_name', 'test_run', 'project', 'host', 'context', 'status', 'attn' ), more_where )
                if not have_qid :
                    ss = ''
                else :
                    ss = ', query'
                c = pdk_db.execute("SELECT count(*) FROM result_scalar%s %s" % (ss, where_text), where_dict )
                datum = c.fetchone()
                if datum is None :
                    count_col[x] = 0
                else :
                    (count_col[x],) = datum
                lquery['status'] = x
                if not always_link and count_col[x] == 0 :
                    table.set_value(rownum,x,      text='0' )
                else :
                    table.set_value(rownum,x,      text=count_col[x],    link=common.selflink(lquery, linkmode) )
                table.set_html_cell_attributes(rownum, x, 'align="right"' )
                count = count + count_col[x]
                total_count = total_count + count_col[x]

        table.set_value(rownum,"count",     text=count )
        table.set_html_cell_attributes(rownum, "count", 'align="right"' )

        for x in total_col :
            total_col[x] += count_col[x]

        rownum = rownum + 1
    
    table.set_value(total_row,"count",     text=total_count )
    table.set_html_cell_attributes(total_row, 'count', 'align="right" style="font-weight:bold"' )
    for x in common.cfg.statuses :
        if ( status == '*') or ( x in status ) :
            table.set_value(total_row,x,      text=total_col[x] )
            table.set_html_cell_attributes(total_row, x, 'align="right" style="font-weight:bold"' )

    return table


def cmp_form( query, comparing ) :
    lquery = query.copy()

    del lquery['compare']
 
    # look for input from the compare form
    lquery['cmp_test_run'] = lquery.get('cmp_test_run', common.run_previous(None,lquery['test_run'])  )
    lquery['cmp_context'] = lquery.get('cmp_context', lquery['context'])
    lquery['cmp_host'] = lquery.get('cmp_host', lquery['host'])

    lquery['query'] = 'treewalk'

    l = [ 
        """<a href='javascript:toggle("cmpform",1)'>[<span id='cmpform_plus'></span> Compare]</a>
        <div id='cmpform'>
        <ul>
        """,
        "<form action=%s method=GET>"%common.get_cgi_name(),
        "<table>"
        ]
    for x in ( 'cmp_test_run', 'cmp_context', 'cmp_host' ) :
        l.append( "<tr><td>%s</td><td> <input type=text name=%s value='%s'></td></tr>"%(x,x,lquery[x]) )
        del lquery[x]
    l.append("</table>")


    l.append( common.query_dict_to_hidden( lquery ) )

    l.append(" <input type=submit name='compare' value='Compare'> ")
    l.append(" <input type=submit name='compare' value='Turn Off Compare'> ")
    l.append(" <input type=submit name='compare' value='Reverse Comparison'>" )

    l.append("</form>")

    ##

    l.append(
        """
        </ul>
        </div>
        <script>
        vis = new Array();
        """ )

    if comparing :
        l.append(""" vis['cmpform']=1; """)

    l.append( """
        function toggle(f) {
            vis[f] = ! vis[f];
            if (vis[f]) v="none"; else v="block";
            if (vis[f]) plus='+'; else plus='-';
            document.getElementById(f).style.display=v;
            document.getElementById(f+'_plus').innerHTML=plus;
        }
        toggle("cmpform")
        </script>
        """ )

    return '\n'.join(l)

