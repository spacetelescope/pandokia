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
import pandokia.pcgi
import pandokia.common as common

import pandokia
from . import PY3

cfg = pandokia.cfg
pdk_db = cfg.pdk_db

#
# Display the detailed test results
#
# This is the page with the heading at the top and the log text at the bottom
#
#


def run():

    sys.stdout.write(common.cgi_header_html)
    sys.stdout.write(common.page_header())

    form = pandokia.pcgi.form

    if "test_name" in form:
        test_name = form.getvalue("test_name")
    else:
        test_name = ""

    if "context" in form:
        context = form.getvalue("context")
    else:
        context = "*"

    if "custom" in form:
        custom = form.getvalue("custom")
    else:
        custom = "*"  

    if "host" in form:
        host = form.getvalue("host")
    else:
        host = "*"

    if "test_run" in form:
        test_run = form.getvalue("test_run")
    else:
        test_run = "*"

    if "project" in form:
        project = form.getvalue("project")
    else:
        project = "*"

    if "status" in form:
        status = form.getvalue("status")
    else:
        status = "*"

    if "test_name" in form:
        cmp_run = form.getvalue("test_name")
        if cmp_run == '':
            cmp_run = common.run_previous(None, test_run)
            if cmp_run is not None:
                cmp_run = common.find_test_run(cmp_run)
            else:
                cmp_run = ''
        else:
            cmp_run = common.find_test_run(cmp_run)
    else:
        cmp_run = ""

    if "key_id" in form:
        key_id = form.getvalue("key_id")
    else:
        key_id = ""

    if "qid" in form:
        qid = form.getvalue("qid")
    else:
        qid = ""

    #
    # main heading
    #

    sys.stdout.write("<h1>Test detail</h1>\n")

    #
    # this query finds all the test results that are an interesting part of this request
    #

    if key_id != "":
        n = do_result(key_id)
    elif qid != "":
        c1 = pdk_db.execute("SELECT key_id FROM query WHERE qid = :1 ", (qid,))
        l = []
        for x in c1:
            l.append(x[0])
        del c1
        n = 0
        for key_id in l:
            n = n + do_result(key_id)
    else:
        c1 = pdk_db.execute(
            "SELECT key_id FROM result_scalar WHERE test_run = :1 AND project = :2 AND host = :3 AND test_name = :4 AND context = :5 AND custom = :6 ",
            (test_run,
             project,
             host,
             test_name,
             context,
             custom))
        n = 0
        for x in c1:
            (key_id, ) = x
            n = n + do_result(key_id)

    if n == 0:
        sys.stdout.write("no tests match\n")
        d_in = {
            'project': project,
            'host': host,
            'context': context,
            'custom': custom,
            'test_run': test_run,
            'test_name': test_name}
        t = next_prev(d_in, test_run)
        if t != '':
            sys.stdout.write(t)


def next_prev(d_in, test_run):
    tmp = ''
    tmp1 = common.run_previous(None, test_run)
    if tmp1 is not None:
        d_in["test_run"] = tmp1
        tmp = tmp + " &nbsp;&nbsp;(<a href=%s>%s</a>)" % (
            common.selflink(d_in, linkmode='detail'), tmp1)
    tmp2 = common.run_next(None, test_run)
    if tmp2 is not None:
        d_in["test_run"] = tmp2
        tmp = tmp + " &nbsp;&nbsp;(<a href=%s>%s</a>)" % (
            common.selflink(d_in, linkmode='detail'), tmp2)
    return tmp


def do_result(key_id):

    c = pdk_db.execute(
        "SELECT key_id, test_run, project, host, context, custom, test_name, status, attn, start_time, end_time, location, test_runner FROM result_scalar WHERE key_id = :1 ",
        (key_id,
         ))
    result_count = 0
    for x in c:
        result_count = result_count + 1
        (key_id, test_run, project, host, context, custom, test_name, status,
         attn, start_time, end_time, location, test_runner) = (x)

        linkback_dict = {
            'project': project,
            'host': host,
            'context': context,
            'custom': custom,
            'test_run': test_run,
            'test_name': test_name}
        prevday_dict = {
            'project': project,
            'host': host,
            'context': context,
            'custom': custom,
            'test_run': test_run,
            'test_name': test_name}

        row = 0
        tb = text_table.text_table()
        tb.set_html_table_attributes("border=1")

        tb.set_value(row, 0, "test_run")

        tmp = next_prev(prevday_dict, test_run)

        if tmp != '':
            tb.set_value(row, 1, test_run, html=test_run + tmp)
        else:
            tb.set_value(row, 1, test_run)

        row += 1

        tb.set_value(row, 0, "key_id")
        tb.set_value(row, 1, key_id)
        row += 1

        tb.set_value(row, 0, "project")
        tb.set_value(row, 1, project)
        row += 1

        tb.set_value(row, 0, "host")
        tb.set_value(row, 1, host)
        row += 1

        tb.set_value(row, 0, "context")
        tb.set_value(row, 1, context)
        row += 1

        tb.set_value(row, 0, "custom")
        tb.set_value(row, 1, custom)
        row += 1

        tb.set_value(row, 0, "test_name")
        tb.set_value(row, 1, test_name)
        row += 1

        tb.set_value(row, 0, "contact")
        tb.set_value(row, 1, common.get_contact(project, test_name))
        row += 1

        tb.set_value(row, 0, "status")
        if status != "P":
            tb.set_value(
                row,
                1,
                text=status,
                html="<font color=red>" +
                status +
                "</font>")
        else:
            tb.set_value(row, 1, status)
        row += 1

        tb.set_value(row, 0, "attn")
        tb.set_value(row, 1, attn)
        row += 1

        tb.set_value(row, 0, "test_runner")
        tb.set_value(row, 1, test_runner)
        row += 1

        try:
            # ignoring exceptions here because we don't know how good the values in
            # the database are.  some preliminary software does not fill them in
            # correctly, for example.
            tb.set_value(row, 1, float(end_time) - float(start_time))
            tb.set_value(row, 0, "duration")
            row += 1
        except:
            pass

        # merge all of this into a generalized "get the times" function that
        # can be used anywhere
        if start_time == '0':
            st = 'unknown'
        else:
            try:
                # you might think that you could use .%f in strftime, but you would be wrong
                # the documentation describes it, but it isn't implemented
                st = datetime.datetime.fromtimestamp(float(start_time))
                st = st.strftime("%Y-%m-%d %H:%M:%S") + "." + \
                    "%03d" % (st.microsecond / 1000)
            except:
                # it is some non-time_t format - just display it
                st = start_time

        if end_time == '0':
            et = 'unknown'
        else:
            try:
                # you might think that you could use .%f in strftime, but you would be wrong
                # the documentation describes it, but it isn't implemented
                et = datetime.datetime.fromtimestamp(float(end_time))
                et = et.strftime("%Y-%m-%d %H:%M:%S") + "." + \
                    "%03d" % (et.microsecond / 1000)
            except:
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

        c1 = pdk_db.execute(
            "SELECT name, value FROM result_tda WHERE key_id = :1 ORDER BY name ASC",
            (key_id,
             ))
        for y in c1:
            (name, value) = y
            tb.set_value(row, 0, "tda_" + name)
            tb.set_value(row, 1, value)
            row += 1

        c1 = pdk_db.execute(
            "SELECT name, value FROM result_tra WHERE key_id = :1 ORDER BY name ASC",
            (key_id,
             ))
        for y in c1:
            (name, value) = y
            tb.set_value(row, 0, "tra_" + name)
            if 'xception' in name:
                tb.set_value(row, 1, value, code=True)
            else:
                tb.set_value(row, 1, value)
            row += 1

        sys.stdout.write(tb.get_html())

        sys.stdout.write(
            "<a href=%s>back to treewalk</a><br>\n" %
            common.selflink(
                linkback_dict,
                linkmode='treewalk'))
        sys.stdout.write(
            "<a href=%s>status history</a><br>\n" %
            common.selflink(
                linkback_dict,
                linkmode='test_history'))

        c1 = pdk_db.execute(
            "SELECT log FROM result_log WHERE key_id = :1 ", (key_id, ))

        for y in c1:
            if not PY3:
                if isinstance(y, tuple):
                    y = tuple(x.decode() for x in y)

            (y, ) = y

            if y != "":
                if getattr(cfg, 'enable_magic_html_log'):
                    if '<!DOCTYPE' in y or '<html' in y:
                        sys.stdout.write(
                            "<a href=%s>HTML block in a single page</a><br>" %
                            common.selflink(
                                {
                                    'magic_html_log': key_id,
                                },
                                linkmode='magic_html_log'))


                sys.stdout.write("Log:<br><pre>")
                sys.stdout.write(cgi.escape(y))
                sys.stdout.write("</pre>\n")

        sys.stdout.write("<br>\n")

        sys.stdout.write("<br><hr>\n")

    return result_count


def test_history():

    sys.stdout.write(common.cgi_header_html)
    sys.stdout.write(common.page_header())

    form = pandokia.pcgi.form

    test_name = form.getvalue("test_name")
    context = form.getvalue("context")
    custom = form.getvalue("custom")
    host = form.getvalue("host")
    test_run = form.getvalue("test_run")
    project = form.getvalue("project")

    tb = text_table.text_table()
    tb.set_html_table_attributes("border=1")

    row = 0

    tb.set_value(row, 0, "project")
    tb.set_value(row, 1, project)
    row += 1

    tb.set_value(row, 0, "host")
    tb.set_value(row, 1, host)
    row += 1

    tb.set_value(row, 0, "context")
    tb.set_value(row, 1, context)
    row += 1

    tb.set_value(row, 0, "custom")
    tb.set_value(row, 1, custom)
    row += 1

    tb.set_value(row, 0, "test_name")
    tb.set_value(row, 1, test_name)
    row += 1

    print(tb.get_html())

    print("<br>")

    tb = text_table.text_table()
    tb.set_html_table_attributes("border=1")

    c = pdk_db.execute(
        "SELECT test_run, status, key_id FROM result_scalar WHERE "
        "test_name = :1 AND context = :2 AND custom = :3 AND host = :4 AND project = :5 ORDER BY test_run DESC",
        (test_name,
         context,
         custom,
         host,
         project))

    row = 0
    for x in c:
        r_test_run, status, key_id = x
        tb.set_value(row, 1, r_test_run, link=common.selflink(
            {'key_id': key_id}, linkmode='detail'))
        tb.set_value(row, 2, status)
        if test_run == r_test_run:
            tb.set_value(row, 0, '->')
        row = row + 1
    print(tb.get_html())


##
# This is a tremendous hack, but it is helpful for pyetc.  If <!DOCTYPE
# occurs in the log (as from a django stack trace captured by the test
# and then printed), we make a link to this "magic_html_log" report.  Just
# emit from the <!DOCTYPE to the </html> as a web page.
#
# This has all kinds of opportunity for the test author to run arbitrary
# javascript/whatever in the browser of somebody who looks at the test
# report.  Decide if you trust your collaborators before using this feature.

def magic_html_log():
    if not getattr(cfg, 'enable_magic_html_log'):
        return

    # common header
    sys.stdout.write(common.cgi_header_html)

    # key_id of the log
    form = pandokia.pcgi.form
    key_id = int(form.getvalue('magic_html_log', -1))

    if key_id < 0:
        sys.stdout.write('Invalid magic_html_log key identifier.')
        return

    # get it
    c1 = pdk_db.execute(
        "SELECT log FROM result_log WHERE key_id = :1 ", (key_id, ))

    # fetch the log
    log, = c1.fetchone()
    if isinstance(log, bytes):
        log = log.decode()

    # split on the magic recognition string
    if '<!DOCTYPE' in log:
        t = log.split('<!DOCTYPE')
        sys.stdout.write('<!DOCTYPE')

    elif '<html' in log:
        t = log.split('<html')
        sys.stdout.write('<html')

    # keep the part after the string
    t = t[1]

    # show the rest up to /html
    if '</html>' in t:
        sys.stdout.write(t.split('</html>')[0])
        sys.stdout.write('</html>')
    else:
        sys.stdout.write(t)
