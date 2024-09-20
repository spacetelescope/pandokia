#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA)
#

#
# pcgi.py - entry point to the the cgi that implements the web interface
#
# includes functions that are used in various places in the CGI but nowhere else
#

from urllib import parse
import os
import os.path
import sys

import pandokia
import pandokia.common as common

cfg = pandokia.cfg


##########
#

def run():


    if cfg.server_maintenance:
        sys.stdout.write(
            "content-type: text/html\n\n\nWeb page unavailable because of pandokia server maintenance<p>\n\n")
        if isinstance(cfg.server_maintenance, str):
            sys.stdout.write("%s\n" % cfg.server_maintenance)
        sys.exit(0)

    ######
    #
    # check authentication
    #

    #--#--# CGI
    if not common.check_auth():
        # If authentication fails, I'm not concerned about giving
        # a particularly useful message.
        sys.stdout.write(
            "content-type: text/html\n\n\nAUTHENTICATION FAILED\n\n")
        sys.exit(0)

    ######
    #
    # various forms of links to ourself
    #
    # cginame is the name of the cgi, for use in generating html links to ourself.
    # This is NOT the full URL -- it is only the path on this host.  We cannot
    # know the host name part of the URL (e.g. if the web connection is coming
    # through an ssh tunnel).
    #
    #--#--# CGI

    global cginame

    cginame = os.getenv("PDK_SCRIPT_NAME")

    ######
    #
    # fetch the cgi parameters
    #

    global form

    # urllib.parse.parse_qs reads a string and breaks up the fields, returning a
    # dictionary of names; each value is a list.
    form = parse.parse_qs(os.getenv("QUERY_STRING"), keep_blank_values=True)
    #form = cgi.FieldStorage(keep_blank_values=1)

    ######
    #
    # output_format is the output format requested; each query type must
    # either know what to do for each possible format
    # possible values are:
    #   'html'  (MUST be default)
    #   'csv'

    global output_format

    if 'format' in form:
        output_format = form["format"][0]
    else:
        output_format = "html"

    ######
    #
    # if we don't have a query field, show the top-level menu and we are done.
    #

    #--#--# CGI
    if "query" not in form:
        import re
        sys.stdout.write("Content-type: text/html\n\n")
        f = os.path.dirname(os.path.abspath(__file__)) + '/top_level.html'
        header = common.page_header()
        f = open(f, "r")
        x = f.read()
        f.close()

        user = common.current_user()

        if common.current_user() in common.cfg.admin_user_list:
            x = re.sub(
                "ADMINLINK",
                '(<a href=CGINAME?query=admin>admin</a>)',
                x)
        else:
            x = re.sub("ADMINLINK", '', x)

        x = re.sub("CURRENTUSER", user, x)
        x = re.sub("CGINAME", cginame, x)
        x = re.sub("PAGEHEADER", header, x)

        sys.stdout.write(x)
        sys.exit(0)

    ######
    #
    # if we get here, we are processing a query.
    #
    # There various modules to implement the known query types.

    #--#--# CGI

    query = form["query"][0]

    if query == "treewalk":
        import pandokia.pcgi_treewalk as x
        x.treewalk()
        sys.exit(0)

    if query == "qid_op":
        import pandokia.pcgi_qid_op as x
        x.run()
        sys.exit(0)

    if query == 'qid_list':
        import pandokia.pcgi_qid_op as x
        x.qid_list()
        sys.exit(0)

    if query == "treewalk.linkout":
        import pandokia.pcgi_treewalk as x
        x.linkout()
        sys.exit(0)

    if query == "summary":
        import pandokia.pcgi_summary as x
        x.run()
        sys.exit(0)

    if query == "detail":
        import pandokia.pcgi_detail as x
        x.run()
        sys.exit(0)

    if query == "test_history":
        import pandokia.pcgi_detail as x
        x.test_history()
        sys.exit(0)

    if query.startswith("day_report."):
        import pandokia.pcgi_day_report as x
        if query == "day_report.1":
            x.rpt1()
        if query == "day_report.2":
            x.rpt2()
        if query == "day_report.3":
            x.rpt3()
        sys.exit(0)

    if query.startswith("delete_run."):
        import pandokia.pcgi_delete as x
        if query == "delete_run.ays":
            x.delete_are_you_sure()
        if query == "delete_run.conf":
            x.delete_confirmed()
        sys.exit(0)

    if query == 'flagok':
        import pandokia.pcgi_flagok as x
        x.flagok()
        sys.exit(0)

    if query == 'action':
        import pandokia.pcgi_action as x
        x.run()
        sys.exit(0)

    if query == 'prefs':
        import pandokia.pcgi_preferences as x
        x.run()
        sys.exit(0)

    if query == 'killproc':
        print("content-type: text/html")
        print("")
        pid = form['pid']
        sig = form['sig']
        if common.current_user() in common.cfg.admin_user_list:
            os.kill(int(pid), int(sig))
        print("done")
        sys.exit(0)

    if query == 'hostinfo':
        import pandokia.pcgi_misc as x
        x.hostinfo()
        sys.exit(0)

    if query == 'set_hostinfo':
        import pandokia.pcgi_misc as x
        x.set_hostinfo()
        sys.exit(0)

    if query == 'magic_html_log':
        import pandokia.pcgi_detail as x
        x.magic_html_log()
        sys.exit(0)

    if query == 'expected':
        import pandokia.pcgi_misc as x
        x.expected()
        sys.exit(0)

    if query == 'new':
        import pandokia.pcgi_reports as x
        x. cluster_report()
        sys.exit(0)

    if query == 'latest':
        import pandokia.pcgi_misc as x
        x.latest()
        sys.exit(0)

    error_1201()
    #
    # You can't get here by following links, so you must have typed in the
    # url directly.  In that case, you are messing with us and you get no
    # friendly response.

    if cfg.debug or (common.current_user() in common.cfg.admin_user_list):
        print("YOU ARE ADMIN, DEBUG FOLLOWS")
        for x in form:
            if isinstance(form[x], list):
                for y in form[x]:
                    print("%s %s<br>" % (x, y))
            else:
                print("%s %s<br>" % (x, form[x][0]))

#


def error_1201():
    sys.stdout.write(
        "content-type: text/html\n\n\n<font color=red><blink>1201</blink></font>\n")
