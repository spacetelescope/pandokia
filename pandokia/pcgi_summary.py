#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import cgi
import re
import copy
import time

import pandokia.text_table as text_table

import urllib
import pandokia.pcgi
import common

import pandokia

pdk_db = pandokia.cfg.pdk_db


def form_to_dict( f ) :
    d = { }
    for x in f :
        l = f.getlist(x)
        if len(l) > 0 :
            d[x] = l
    return d

#
#
#

def run ( ) :

    global any_attr

    output = sys.stdout

    any_attr = { }

    #
    # gather up all the expected parameters
    #

    input_query = form_to_dict(pandokia.pcgi.form)

    # print "context-type: text/plain\n\n"

    qid = int(input_query["qid"][0])
    #print qid

    # some fields are the names of submit buttons that we do not look
    # at and that we do not want to accumulate in the URL
    for x in ( 'col_show', ) :
        if x in input_query :
            del input_query[x]

    #
    if 'cmp_run' in input_query :
        cmp_run = input_query["cmp_run"][0]
        if cmp_run == '' :
            cmp_run = 'daily_yesterday'
        cmp_run = common.find_test_run(cmp_run)
    else :
        cmp_run = ''

    cmptype = 'c'

    if 'x_submit' in input_query :
        x = input_query['x_submit'][0]
        if x == 'same' :
            cmptype = 's'
        elif x == 'different' :
            cmptype = 'd'

    show_attr = 0
    if "show_attr" in input_query :
        show_attr = int(input_query["show_attr"][0])

    # generate a link to click on to sort.  use sort_link+"thing" to sort
    # on thing.  thing must be "+xyz" or "-xyz" to sort on column xyz
    # either ascending or descending.
    #
    sort_query = { }
    for x in input_query :
        if x != 'sort' and x != 'query' :
            sort_query[x] = input_query[x]

    sort_link = common.selflink( sort_query, 'summary' ) + "&sort="

    # Sorting is a little weak right now.  We only generate links to sort
    # ascending, and we don't draw little arrows or anything.  We really
    # need for text_table to offer html text for the column heading
    # instead of just link text.


    # generate the table - used to be written inline here
    result_table, all_test_run, all_project, all_host, all_context, rowcount, different, expires, claimant, notes = get_table( qid, sort_link, cmp_run, cmptype, show_attr )

    if pandokia.pcgi.output_format == 'html' :
        # HTML OUTPUT

        print "content-type: text/html\n\n"

        print common.page_header()

        #
        # main heading
        #

        output.write("<h1>Test summary</h1>")

        # 
        #  Offer to compare to a previous run
        #
        # should we make clickable links of other runs or a drop list?  It
        # would be nice, but I discoverd that finding the list would slow 
        # this cgi a _lot_
        output.write("""
    Compare to:
    <form action=%s id=compare_form name=compare_form>
    <input type=hidden name=qid value='%d'>
    <input type=hidden name=show_attr value='%d'>
    <input type=hidden name=query value='summary'>
    <input type=text name=cmp_run value='%s'>
    <br>
    <input type=submit name=x_submit value='compare'>
    <input type=submit name=x_submit value='same'>
    <input type=submit name=x_submit value='different'>
    </form>
    """ % ( pandokia.pcgi.cginame, qid, show_attr, cgi.escape(cmp_run) ) )

        # 
        output.write("""
    <form action=%s id=attribute_form name=attribute_form>
    <input type=hidden name=qid value=%d>
    <input type=hidden name=show_attr value=1>
    <input type=hidden name=query value=summary>
    <input type=hidden name=cmp_run value='%s'>
    <input type=submit name=x_submit value='Add Attributes'>
    </form>
    """ % ( pandokia.pcgi.cginame, qid, cgi.escape(cmp_run) ) )

        output.write('<h3>QID = %d</h3>'%int(qid))
        if expires == 0 :
            output.write('<b>never expires</b>')
        else :
            if expires is not None :
                expires = float(expires)
                e = time.localtime(expires)
                output.write('expires %4d-%02d-%02d'%(e.tm_year, e.tm_mon, e.tm_mday))
            else :
                output.write('expires someday')

            qdict = { "qid" : qid, "valuable_qid" : 1  }
            output.write( " ( <a href='"+common.selflink(qdict, linkmode = "action")+"'>" )
            output.write( "never expire</a> )" )

        qdict = { "qid" : qid, "valuable_qid" : 0  }
        output.write( " ( <a href='"+common.selflink(qdict, linkmode = "action")+"'>" )
        output.write( "normal expire</a> )" )

        output.write(', ')
        qdict = { "qid" : qid, "claim_qid" : 1  }

        if claimant != None :
            output.write( "owner %s\n" % claimant )
        else :
            output.write( " ( <a href='"+common.selflink(qdict, linkmode = "action")+"'>" )
            output.write( "Claim this qid</a> ) <br>" )

        if notes is None :
            notes = 'None'

        qdict = { "qid" : qid, "edit_comment" : 1  }
        output.write( "<br><a href='"+common.selflink(qdict, linkmode = "action")+"'>" )
        output.write('Comment:</a><br><pre>%s</pre>\n'%cgi.escape(notes))

        
        qdict = { "qid" : qid }
        output.write( "<a href='"+common.selflink(qdict, linkmode = "treewalk")+"'>" )
        output.write( "tree walk this qid </a>, " )

        qdict = { "qid" : qid }
        output.write( "<a href='"+common.selflink(qdict, linkmode = "qid_op")+"'>" )
        output.write( "edit this qid </a><br>" )

        # suppose you have 
        #   d = { 'A' : 1 }
        # how do you find out the name of the single index value?
        #   x = [tmp for tmp in d]
        # makes a list of all the index values
        #   [tmp for tmp in d][0]
        # is the first (and only) value in that list

        if len(all_test_run) == 1 :
            result_table.suppress("test_run")
            output.write("<h3>test_run: "+cgi.escape([tmp for tmp in all_test_run][0])+"</h3>")
        if len(all_project) == 1 :
            result_table.suppress("project")
            output.write("<h3>project: "+cgi.escape([tmp for tmp in all_project][0])+"</h3>")
        if len(all_host) == 1 :
            result_table.suppress("host")
            output.write("<h3>host: "+cgi.escape([tmp for tmp in all_host][0])+"</h3>")
        if len(all_context) == 1 :
            result_table.suppress("context")
            output.write("<h3>context: "+cgi.escape([tmp for tmp in all_context][0])+"</h3>")


        # suppressing columns that the user did not ask for
        if 'S' in input_query :
            column_select_values = input_query['S']
            column_select_values = set(column_select_values)
            for x in result_table.colmap :
                if x in ( 'line #', 'checkbox' ) :
                    continue
                if not x in column_select_values :
                    result_table.suppress(x)
        else :
            column_select_values = set( [ x  for x in result_table.colmap ] )

        # show the table to choose the columns that the user wants to see
        output.write("""<a href='javascript:toggle_visibility("selectform")'>[<span id='selectform_plus'></span> Column selector]</a>""")

        output.write('<div id=selectform>')
        output.write('<form action=%s method=get name=colselectform id=colselectform>' % pandokia.pcgi.cginame )
        for n, x in sorted( [ ( result_table.colmap[x], x) for x in result_table.colmap ] ) :
            t = result_table.titles[n]
            if t == '&nbsp;' :
                continue
            if t in column_select_values :
                checked=' checked '
            else :
                checked = ''
            output.write( '<label><input type=checkbox name=S %s value=%s>%s</label><br>'%(checked, urllib.quote(t),urllib.quote(t)) )
        for x in input_query :
            if x != 'S' :
                for y in input_query[x] :
                    output.write('<input type=hidden name=%s value=%s>'%(x,urllib.quote(y)))
        output.write('<input type=submit name="col_show" value="Show Checked">')
        # output.write('<input type=button name="col_hide" value="Hide Checked" onclick="vis_hide()">')
        output.write('<input type=button name="toggle" value="Toggle" onclick="vis_toggle()">')
        output.write('<input type=button name="all" value="All" onclick="vis_all(1)">')
        output.write('<input type=button name="none" value="None" onclick="vis_all(0)">')
        output.write('''<input type=button name="tda" value="tda" onclick="vis_some('tda_')">''')
        output.write('''<input type=button name="tra" value="tra" onclick="vis_some('tra_')">''')
        output.write('''<input type=button name="tra" value="core" onclick="vis_some('')">''')
        output.write('</form>')
        output.write('</div>')
        
        # javascript to 
        output.write("""
<script type="text/javascript">
    function toggle_visibility(id) {
       var e = document.getElementById(id);
       if(e.style.display == 'block') {
          e.style.display = 'none';
          plus = '+';
       } else {
          e.style.display = 'block';
          plus = '-';
        }
        e = document.getElementById(id+'_plus');
        e.innerHTML = plus;
    }
    toggle_visibility("selectform");
    toggle_visibility("selectform");

    function vis_hide() {
        vis_toggle();
        f = document.colselectform;
        // Why doesn't this work?
        f.submit();
    }

    // yeah, I know, but I'm in a hurry
        function vis_toggle()
            {
            len = document.colselectform.elements.length;
            ele = document.colselectform.elements;
            for (n=0; n<len; n++)
                ele[n].checked= ! ele[n].checked;
            }

        function vis_all(value)
            {
            len = document.colselectform.elements.length;
            ele = document.colselectform.elements;
            for (n=0; n<len; n++)
                ele[n].checked= value;
            }

        function vis_some(value)
            {
            len = document.colselectform.elements.length;
            ele = document.colselectform.elements;
            if ( value == '' ) {
                for (n=0; n<len; n++) {
                    if ( ele[n].value.search('t.a_') == 0 )
                        return;
                    ele[n].checked= 1
                    }
                return;
                }
            for (n=0; n<len; n++)
                if ( ele[n].value.search(value) == 0 )
                    ele[n].checked= 1
            }

</script>
""")



        # suppressing the columns that are the same for every row
        same_table = suppress_attr_all_same( result_table )

        if same_table.get_row_count() > 0 :
            output.write( "<ul><b>attributes same for all rows:</b>" )
            output.write( same_table.get_html() )
            output.write( "</ul><br>" )

        if 'sort' in input_query :
            sort_order = input_query["sort"][0]
        else :
            sort_order = 'Utest_name'

        reverse_val = sort_order.startswith("D")

        result_table.set_sort_key( sort_order[1:], float )

        result_table.sort([ sort_order[1:] ], reverse=reverse_val)
        rows = len(result_table.rows)
        for i in range(0,rows):
            result_table.set_value(i,"line #",i+1)  

        output.write('''
    <script language=javascript>
        function set_all(value)
            {
            len = document.testform.elements.length;
            ele = document.testform.elements;
            for (n=0; n<len; n++)
                ele[n].checked=value;
            }
        function set_range(value)
            {
            begin=document.getElementById("begin").value-1;
            end=document.getElementById("end").value-0;
            ele=document.testform.elements;
            for(n=begin; n<end; n++)
                ele[n].checked=value;
            }
        function toggle(value)
            {
            len = document.testform.elements.length;
            ele = document.testform.elements;
            for (n=0; n<len; n++)
                ele[n].checked= ! ele[n].checked;
            }
        function condclear(name)
            {
            n = document.getElementById(name);
            if ( n.value.substr(0,1) == '*' )
                n.value='';
            }
    </script>
    ''')

        # show the table, which contains a form
        output.write('''
        <form action=%s method=post name=testform>
        ''' % ( pandokia.pcgi.cginame,) )


        # alter the column headers - violates the interface of text_table
        # for x in result_table.colmap :
        #     n = result_table.colmap[x]
        #     t = result_table.titles[n]
        #     result_table.title_html[n] = '<input type=checkbox name=S value=%s><br>'%t + t

        output.write(result_table.get_html(color_rows=5))
        output.write('''
        <input type=hidden name=query value='action'>
        <input type=hidden name=qid value=%d>
        '''% (qid, ) )
        output.write('Actions:<br>')
        output.write("""<input type=text name=begin id=begin value="*Begin line" onfocus='condclear("begin")'size=10> """)
        output.write("""<input type=text name=end id=end value="*End line" onfocus='condclear("end")' size=10> """)
        output.write('<input type=button name="setrange" value="Set Range" onclick="set_range(true)">')
        output.write('<br>')
        output.write('<input type=button name="setall"   value="Select All"   onclick="set_all(true)">')
        output.write('<input type=button name="clearall" value="Clear All" onclick="set_all(false)">')
        output.write('<input type=button name="clearall" value="Toggle"    onclick="toggle()">')
        output.write('<br>')
        output.write('<input type=submit name="action_remove" value="Remove">')
        output.write('<input type=submit name="action_keep"   value="Keep">')
        output.write(' on this report page<br>')
        output.write('<input type=submit name="action_flagok" value="Flag OK">')
        output.write('<input type=submit name="action_flagok_rem" value="Flag OK + Remove">')
        output.write('<input type=submit name="action_cattn" value="Clear Attn">')
        output.write('<input type=submit name="action_sattn" value="Set Attn">')
        output.write('<br>')
        output.write('<input type=submit name="not_expected" value="Not Expected"> in <input type=text name=arg1 value="daily" size=10> test runs')
        output.write('</form>')

        output.write( "<br>rows: %d <br>"%rowcount )
        if cmp_run != "" :
            output.write( "different: %d <br>"%different )

        qdict = { "qid" : qid }
        output.write( "<a href='"+common.selflink(qdict, linkmode = "detail")+"'>" )
        output.write( "detail of all</a>" )
        return

        # end HTML

    if pandokia.pcgi.output_format == 'csv' :
        # CSV OUTPUT
        result_table.suppress('checkbox')
        if 'suppress_same' in input_query :
            suppress_attr_all_same( result_table )
        print "content-type: text/plain\n\n"
        print result_table.get_csv(headings=1)

    if pandokia.pcgi.output_format == 'rst' :
        # RST OUTPUT
        result_table.suppress('checkbox')
        print "content-type: text/plain\n\n"
        if 'suppress_same' in input_query :
            suppress_attr_all_same( result_table )
        print result_table.get_rst(headings=1)

    if pandokia.pcgi.output_format == 'awk' :
        # AWK OUTPUT
        result_table.suppress('checkbox')
        print "content-type: text/plain\n\n"
        if 'suppress_same' in input_query :
            suppress_attr_all_same( result_table )
        print result_table.get_awk(headings=1)


def load_in_table( tt, row, cursor, prefix, sort_link ) :
    for x in cursor :
        ( name, value ) = x
        name = prefix + name
        # bug: only sorts up - would like it to be up/down depending on what it was last.
        tt.define_column(name,link=sort_link+"U"+name)
        tt.set_value(row, name, value)
        any_attr[name]=1

def get_table( qid, sort_link, cmp_run, cmptype , show_attr):

    #if cmp_run != '' :
    #    output.write("<h3>Compare to: "+cgi.escape(cmp_run)+"</h3>")

    result_table=text_table.text_table()
    result_table.set_html_table_attributes("border=1")

    tda_table = text_table.text_table()
    tda_table.set_html_table_attributes("border=1")

    tra_table = text_table.text_table()
    tra_table.set_html_table_attributes("border=1")

    #
    # this query finds all the test results that are an interesting part of this request
    #

    c = pdk_db.execute("SELECT expires, username, notes FROM query_id WHERE qid = :1", (qid,))
    x = c.fetchone()

    if x is not None :
        expires = x[0]
        claimant = x[1]
        if claimant == '' :
            claimant = None
        notes = x[2]
    else :
        expires = None
        claimant = None
        notes = ''

    now = time.time()
    pdk_db.execute("UPDATE query_id SET time = :1 WHERE qid = :2", (now, qid) )
    if expires > 0 and expires < now + ( 30 * 86400 ) :
        expires = now + ( 30 * 86400 )
        pdk_db.execute("UPDATE query_id SET expires = :1 WHERE qid = :2", (expires, qid) )

    pdk_db.commit()

    c = pdk_db.execute("SELECT key_id FROM query WHERE qid = :1", (qid,) )

    result_table.define_column("line #", showname='&nbsp;')
    result_table.define_column("runner")
    result_table.define_column("checkbox",  showname='&nbsp;')
    result_table.define_column("attn",      link=sort_link+"Uattn")
    result_table.define_column("test_run",  link=sort_link+"Utest_run")
    result_table.define_column("project",   link=sort_link+"Uproject")
    result_table.define_column("host",      link=sort_link+"Uhost")
    result_table.define_column("context",   link=sort_link+"Ucontext")
    result_table.define_column("test_name", link=sort_link+"Utest_name")
    result_table.define_column("contact",   link=sort_link+"Ucontact")
    if cmp_run != "" :
        result_table.define_column("diff",  link=sort_link+"Udiff")
        result_table.define_column("other", link=sort_link+"Uother")

    result_table.define_column("stat",      link=sort_link+"Ustat")

    # these are used to suppress a column when all the results are the same
    all_test_run = { }
    all_project = { }
    all_host = { }
    all_context = { }

    different = 0
    rowcount = 0
    for x in c :
        ( key_id, ) = x

        #
        # find the result of this test
        #

        c1 = pdk_db.execute("SELECT test_run, project, host, context, test_name, status, attn, test_runner FROM result_scalar WHERE key_id = :1 ", (key_id,) )

        y = c1.fetchone()   # unique index

        if y is None :
            # this can only happen if somebody deletes tests from the database after we populate the qid
            continue

        (test_run, project, host, context, test_name, status, attn, runner) = y

        # if we are comparing to another run, find the other one; 
        # suppress lines that are different - should be optional
        if cmp_run != "" :
            c2 = pdk_db.execute("SELECT status, key_id FROM result_scalar WHERE test_run = :1 AND project = :2 AND host = :3 AND test_name = :4 AND context = :5",
                ( cmp_run, project, host, test_name, context ) )
            other_status = c2.fetchone()   # unique index
            if other_status is None :
                pass
            else :
                (other_status, other_key_id) = other_status
                # if the other one is the same, go to next row
                if other_status == status :
                    if cmptype == 'd' :
                        continue
                else :
                    if cmptype == 's' :
                        continue
                    result_table.set_value(rowcount, "diff", text=">")
                other_link = common.selflink( { 'key_id' : other_key_id }, linkmode="detail")
                if other_status == "P" :
                    result_table.set_value(rowcount,"other",other_status, link=other_link)
                else :
                    result_table.set_value(rowcount,"other",other_status, html="<font color=red>"+str(other_status)+"</font>", link=other_link)
                result_table.set_html_cell_attributes(rowcount,"other","bgcolor=lightgray")
                if other_status != status :
                    different = different + 1

        all_test_run[test_run] = 1
        all_project[project] = 1
        all_host[host] = 1
        all_context[context] = 1

        detail_query = { "key_id" : key_id }
        result_table.set_value(rowcount,"runner",runner)
        result_table.set_value(rowcount,"checkbox",'',html='<input type=checkbox name=%s>'%key_id)
        result_table.set_value(rowcount,"attn",attn)
        result_table.set_value(rowcount,"test_run",test_run)
        result_table.set_value(rowcount,"project",project)
        result_table.set_value(rowcount,"host",host)
        result_table.set_value(rowcount,"context",context)
        this_link = common.selflink(detail_query, linkmode="detail")
        result_table.set_value(rowcount,"test_name",text=test_name, link=this_link )

        result_table.set_value(rowcount,"contact",common.get_contact(project, test_name, 'str'))

        if status == "P" :
            result_table.set_value(rowcount,"stat",status, link=this_link)
        else :
            result_table.set_value(rowcount,"stat",status, html="<font color=red>"+str(status)+"</font>", link=this_link)

        if show_attr :
            c3 = pdk_db.execute("SELECT name, value FROM result_tda WHERE key_id = :1 ORDER BY name ASC", ( key_id, ) )
            load_in_table( tda_table, rowcount, c3, "tda_", sort_link )
            del c3

            c3 = pdk_db.execute("SELECT name, value FROM result_tra WHERE key_id = :1 ORDER BY name ASC", ( key_id, ) )
            load_in_table( tra_table, rowcount, c3, "tra_", sort_link )
            del c3


        rowcount += 1

        del c1

    if show_attr:
        result_table.join(tda_table)
        result_table.join(tra_table)

    return result_table, all_test_run, all_project, all_host, all_context, rowcount, different, expires, claimant, notes

def suppress_attr_all_same( result_table ) :

        # try to suppress attribute columns where all the data values are the same
        global any_attr
        any_attr = list(any_attr)
        any_attr.sort()

        same_table = text_table.text_table()
        same_table.set_html_table_attributes("border=1")
        same_row = 0

        rowcount = result_table.get_row_count()

        for x in any_attr :
            all_same = 1
            txt = result_table._row_col_cell(0,x).text
            for y in range(1, rowcount) :
                ntxt = result_table._row_col_cell(y,x).text
                if txt != ntxt :
                    all_same = 0
                    break

            if all_same :
                same_table.set_value(same_row,0,x)
                same_table.set_value(same_row,1,txt)
                same_row = same_row + 1
                result_table.suppress(x)

        return same_table
