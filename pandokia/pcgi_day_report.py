#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
import sys
import cgi
import re
import copy
import time

import pandokia.text_table as text_table
import urllib

import pandokia
import pandokia.common as common

import pandokia.pcgi

######
#
# day_report.1
#   show a list of test_run values that we can make a day_report for
#
# CGI parameters:
#   test_run = wild card pattern for test_run
#

def rpt1(  ) :

    db = common.open_db()

    form = pandokia.pcgi.form

    if form.has_key("test_run") :
        test_run = form["test_run"].value
    else :
        test_run = '*'

    if test_run == '-me' :
        test_run = 'user_' + common.current_user() + '_*'

    # c = db.execute("SELECT DISTINCT test_run FROM result_scalar WHERE test_run GLOB ? ORDER BY test_run DESC ",( test_run,))
    c = db.execute("SELECT name FROM distinct_test_run WHERE name GLOB ?  ORDER BY name DESC ",( test_run,))

    table = text_table.text_table()

    # day report, tree walk, problem list
    dquery = { }
    lquery = { 'project' : '*', 'host' : '*', 'status' : '[FE]' }
    tquery = { 'project' : '*', 'host' : '*' }

    row = 0
    for x in c :
        (x,) = x
        if x is None :
            continue
        dquery["test_run"] = x
        lquery["test_run"] = x
        tquery["test_run"] = x

        table.set_value(row, 0, text=x, link=common.selflink(dquery,"day_report.2") )
        table.set_value(row, 2, text='(tree display)', link=common.selflink(tquery,"treewalk") )
        table.set_value(row, 3, text='(problem tests)', link=common.selflink(lquery,"treewalk.linkout") )
        row = row + 1

    if pandokia.pcgi.output_format == 'html' :
        sys.stdout.write(common.cgi_header_html)
        sys.stdout.write('<h2>%s</h2>'%cgi.escape(test_run))
        sys.stdout.write(table.get_html(headings=1))
    elif pandokia.pcgi.output_format == 'csv' :
        sys.stdout.write(common.cgi_header_csv)
        sys.stdout.write(table.get_csv())

    return

######
#
# day_report.2
#   show the actual day report: 
#       for each project show a table containing pass/fail/error for each host
#
# parameters:
#   test_run = name of test run to show data for
#       no wild cards permitted, but we allow special names
#

def rpt2( ) :

    form = pandokia.pcgi.form

    if form.has_key("test_run") :
        test_run = form["test_run"].value
    else :
        # no parameter?  I think somebody is messing with us...
        # no matter - just give them a the list of all the test_runs
        rpt1()
        return

    #
    test_run = common.find_test_run(test_run)

    # create list of projects
    projects = None

    if form.has_key("project") :
        projects = form.getlist("project")

    # create the actual table
    [ table, projects ] = gen_daily_table( test_run, projects )

# # # # # # # # # # 
    if pandokia.pcgi.output_format == 'html' :
        header = "<h1>"+cgi.escape(test_run)+"</h1>\n"

        if test_run.startswith('daily_') :
            # 
            # If we have a daily run, create a special header.

            # show the day of the week, if we can
            try :
                import datetime
                t = test_run[len('daily_'):]
                t = t.split('-')
                t = datetime.date(int(t[0]),int(t[1]),int(t[2]))
                t = t.strftime("%A")
                header = header+ "<h2>"+str(t)+"</h2>"
            except :
                pass

            # Include links to the previous / next day's daily run.
            # It is not worth the cost of looking in the database to make sure the day that
            # we link to really exists.  It almost always does, and if it doesn't, the user
            # will find out soon enough.
            # 

            prev = common.previous_daily( test_run )
            back = common.self_href( query_dict = {  'test_run' : prev } , linkmode='day_report.2', text=prev )
            header = header + '( prev ' + back

            latest = common.find_test_run('daily_latest') 
            if test_run != latest :
                next = common.next_daily( test_run )
                header = header + " / next " + common.self_href( query_dict={  'test_run' : next } , linkmode='day_report.2', text=next )
                if next != latest :
                    header = header + " / latest " + common.self_href( query_dict={  'test_run' : latest } , linkmode='day_report.2', text=latest )

            header = header + ' )<p>\n'

        sys.stdout.write(common.cgi_header_html)
        sys.stdout.write(header)
        sys.stdout.write(table.get_html(headings=0))
    elif pandokia.pcgi.output_format == 'csv' :
        sys.stdout.write(common.cgi_header_csv)
        sys.stdout.write(table.get_csv())


#   #   #   #   #   #   #   #   #   #


def gen_daily_table( test_run, projects ) :

    db = common.open_db()

    # convert special names, e.g. daily_latest to the name of the latest daily_*
    test_run = common.find_test_run(test_run)

    if projects is None :
        projects = [ ]
        c = db.execute("SELECT DISTINCT project FROM result_scalar WHERE test_run = ? ORDER BY project ", (test_run, ) )
        for x in c :
            (x,) = x
            if x is None :
                continue
            projects.append(x)

    # this is the skeleton of the cgi queries for various links
    query = { "test_run" : test_run }

    # This is a single table for all projects, because we want the
    # pass/fail/error columns to be aligned from one to the next
    #
    table = text_table.text_table()

    # The texttable object doesn't understand colspans, but we hack a
    # colspan into it anyway.  Thee result is ugly if you have borders.

    table.set_html_table_attributes("cellpadding=2")

    row = 0
    table.define_column("host")
    table.define_column("context")
    table.define_column("os")
    table.define_column("total")
    for x in common.cfg.statuses :
        table.define_column(x)
    table.define_column("note")

#   #   #   #   #   #   #   #   #   #
    for p in projects :

        # values common to all the links we will write in this pass through the loop
        query["project"] = p
        query["host"] = "*"

        # this link text is common to all the links for this project
        link = common.selflink(query_dict = query, linkmode="treewalk" )

        # the heading for a project subsection of the table
        table.set_value(row, 0, text=p, html="<big><strong><b>"+p+"</b></strong></big>", link=link)
        table.set_html_cell_attributes(row,0,"colspan=8")
        row += 1

        # the column headings for this project's part of the table
        table.set_value(row, "total", text="total", link=link )
        for x in common.cfg.statuses :
            xn = common.cfg.status_names[x]
            table.set_value(row, x, text=xn, link = link + '&status='+x )
        table.set_value(row, "note", text="" )  # no heading for this one
        row += 1

        # This will be the sum of all the tests in a particular project.
        # It comes just under the headers for the project, but we don't
        # know the values until the end.
        status_types = common.cfg.statuses
        project_sum = { 'total' : 0 }
        for status in status_types :
            project_sum[status] = 0

        project_sum_row = row
        row += 1

        # loop across hosts
        c = db.execute("SELECT DISTINCT host, context FROM result_scalar WHERE test_run = ? AND project = ?", (test_run, p))
        for host, context in c :
            query["host"] = host
            link = common.selflink(query_dict = query, linkmode="treewalk" )
            table.set_value(row,0,    text=host,        link=link)
            table.set_value(row,1,    text=context,        link=link)
            table.set_value(row,2,    text=pandokia.cfg.os_info.get(host,'?') )
            total_results = 0
            for status in status_types :
                c1 = db.execute("SELECT COUNT(*) FROM result_scalar WHERE  test_run = ? AND project = ? AND host = ? AND status = ? AND context = ?",
                    ( test_run, p, host, status, context ) )
                (x,) = c1.fetchone()
                total_results += x
                project_sum[status] += x
                table.set_value(row, status, text=str(x), link = link + "&rstatus="+status )

            project_sum['total'] += total_results

            # x is the value from the _last_ column we processed, which is 'missing'
            if x == total_results :
                # if it equals the total, then everything is missing; we make a note of that
                table.set_value(row, 'note', 'all')
            elif x != 0 :
                # if it is not 0, then we have a problem
                table.set_value(row, 'note', 'some')

            table.set_value(row, 'total', text=str(total_results), link=link )

            row = row + 1

        for status in status_types :
            table.set_value(project_sum_row, status, project_sum[status] )

        table.set_value(project_sum_row, 'total', project_sum['total'] )

        # insert this blank line between projects - keeps the headings away from the previous row
        table.set_value(row,0,"")
        row = row + 1

    return [ table, projects ]
