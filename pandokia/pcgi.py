#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
# pcgi.py - entry point to the the cgi that implements the web interface
#
# includes functions that are used in various places in the CGI but nowhere else
#

import cgi
import os
import os.path
import sys
import urllib
import cgitb

import pandokia
import pandokia.common as common

cfg = pandokia.cfg



def run() :

    if cfg.debug :
        cgitb.enable()

    ######
    #
    # check authentication
    #

    #--#--# CGI
    if not common.check_auth() :
        # If authentication fails, I'm not concerned about giving
        # a particularly useful message.
        sys.stdout.write("content-type: text/html\n\n\nAUTHENTICATION FAILED\n\n")
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

    cginame = os.getenv("SCRIPT_NAME")

    ######
    #
    # fetch the cgi parameters
    #

    global form

    form = cgi.FieldStorage(keep_blank_values=1)

    ######
    #
    # output_format is the output format requested; each query type must
    # either know what to do for each possible format
    # possible values are:
    #   'html'  (MUST be default)
    #   'csv'

    global output_format

    if 'format' in form :
        output_format = form['format'].value
    else :
        output_format = "html"

    ######
    #
    # if we don't have a query field, show the top-level menu and we are done.
    #

    #--#--# CGI
    if not form.has_key("query") :
        import re
        sys.stdout.write("Content-type: text/html\n\n")
        f = os.path.dirname(os.path.abspath(__file__)) + '/top_level.html'
        f=open(f,"r")
        for x in f :
            x = re.sub("CGINAME",cginame, x)
            sys.stdout.write(x)
        f.close()
        sys.exit(0)

    ######
    #
    # if we get here, we are processing a query.
    #
    # There various modules to implement the known query types.

    #--#--# CGI

    query = form["query"].value

    if query == "treewalk" :
        import pandokia.pcgi_treewalk as x
        x.treewalk()
        sys.exit(0)

    if query == "vview" :
        import pandokia.vview
        pandokia.vview.testwalk()
        sys.exit(0)

    if query == "treewalk.linkout" :
        import pandokia.pcgi_treewalk as x
        x.linkout()
        sys.exit(0)

    if query == "summary" :
        import pandokia.pcgi_summary as x
        x.run()
        sys.exit(0)

    if query == "detail" :
        import pandokia.pcgi_detail as x
        x.run()
        sys.exit(0)

    if query.startswith("day_report.") :
        import pandokia.pcgi_day_report as x
        if query == "day_report.1" :
            x.rpt1()
        if query == "day_report.2" :
            x.rpt2()
        if query == "day_report.3" :
            x.rpt3()
        sys.exit(0)

    if query == 'flagok' :
        import pandokia.pcgi_flagok as x
        x.flagok()
        sys.exit(0)

    if query == 'settings' :
        import pandokia.pcgi_settings as x
        x.run()
        sys.exit(0)

    #
    # You can't get here by following links, so you must have typed in the
    # url directly.  In that case, you are messing with us and you get no
    # friendly response.
    sys.stdout.write("content-type: text/html\n\n\n<font color=red><blink>1201</blink></font>\n")

