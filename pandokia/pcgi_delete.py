#
# pandokia - a test reporting and execution system
# Copyright 2010, Association of Universities for Research in Astronomy (AURA) 
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

pdk_db = pandokia.cfg.pdk_db

import pandokia.pcgi

######
#
# day_report.1
#   show a list of test_run values that we can make a day_report for
#
# CGI parameters:
#   test_run = wild card pattern for test_run
#

def check_valuable(test_run) :
    c = pdk_db.execute("SELECT valuable FROM distinct_test_run WHERE test_run = :1",(test_run,))

    # this trick discovers valuable=0 even if it is not in the distinct_test_run table
    valuable = 0
    for x in c :
        valuable, = x

    valuable = int(valuable)
    if valuable > 0 :
        print "<em>This is a valuable test run - not deleted</em>"
    return valuable

def delete_are_you_sure(  ) :

    form = pandokia.pcgi.form

    test_run = form["test_run"].value

    sys.stdout.write(common.cgi_header_html)
    sys.stdout.write(common.page_header())

    if check_valuable(test_run) :
        return

    print '<a href="%s">Confirm delete:</a> %s'%(common.selflink( { 'test_run' : test_run }, 'delete_run.conf' ), cgi.escape(test_run) )

    c = pdk_db.execute('SELECT count(*) FROM result_scalar WHERE test_run = :1', (test_run,) )
    (x,) = c.fetchone()
    print x, "records"


def delete_confirmed( ) :

    form = pandokia.pcgi.form

    test_run = form["test_run"].value

    sys.stdout.write(common.cgi_header_html)
    sys.stdout.write(common.page_header())

    if check_valuable(test_run) :
        return

    my_run_prefix = 'user_' + common.current_user()

    admin = common.current_user() in common.cfg.admin_user_list

    if not ( admin or test_run.startswith(my_run_prefix) ) :
        print "You (%s) can't do that"%common.current_user()

    else :

        print "Deleteing..."
        sys.stdout.flush()

        import pandokia.cleaner as cleaner

        # delete_run is chatty, so we <pre> around it
        print "<pre>"

        # delete_run expects sys.argv[1:], so we pass a list
        cleaner.delete_run( [ test_run ] )

        print "</pre>"

