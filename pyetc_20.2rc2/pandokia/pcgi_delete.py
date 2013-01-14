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
import pandokia.cleaner as cleaner

import pandokia
import pandokia.common as common

pdk_db = pandokia.cfg.pdk_db

import pandokia.pcgi

######

def delete_are_you_sure(  ) :

    form = pandokia.pcgi.form
    test_run = form["test_run"].value
    project  = form.getfirst('project','*')
    context  = form.getfirst('context','*')
    host     = form.getfirst('host','*')

    sys.stdout.write(common.cgi_header_html)
    sys.stdout.write(common.page_header())

    if pandokia.cleaner.check_valuable(test_run) :
        print "valuable test run - There should not be a link that comes here"
        return

    print "Delete data for:<br>"
    tt = text_table.text_table()
    tt.set_html_table_attributes("border=1")
    tt.set_value(0,0,'test_run')
    tt.set_value(0,1,test_run)
    tt.set_value(1,0,'project')
    tt.set_value(1,1,project)
    tt.set_value(2,0,'host')
    tt.set_value(2,1,host)
    tt.set_value(3,0,'context')
    tt.set_value(3,1,context)
    print tt.get_html()
    print "<br>"

    where_str, where_dict = pdk_db.where_dict( [ ( 'test_run', test_run ),  ('project', project), ('context', context), ('host', host) ] )

    print where_str,"<br>"
    print where_dict,"<br>"
    c = pdk_db.execute('SELECT count(*) FROM result_scalar %s'%where_str, where_dict)
    (x,) = c.fetchone()
    print x, "records<br>"

    print '<a href="%s">Confirm delete</a>'%common.selflink( { 'test_run' : test_run,
        'project' : project, 'context' : context, 'host' : host }, 'delete_run.conf' )


def delete_confirmed( ) :

    form = pandokia.pcgi.form
    test_run = form["test_run"].value
    project  = form.getfirst('project','*')
    context  = form.getfirst('context','*')
    host     = form.getfirst('host','*')


    where_str, where_dict = pdk_db.where_dict( [ ( 'test_run', test_run ),  ('project', project), ('context', context), ('host', host) ] )

    sys.stdout.write(common.cgi_header_html)
    sys.stdout.write(common.page_header())

    if pandokia.cleaner.check_valuable(test_run) :
        print "valuable test run - There should not be a link that comes here"
        return

    my_run_prefix = 'user_' + common.current_user()

    admin = common.current_user() in common.cfg.admin_user_list

    if not ( admin or test_run.startswith(my_run_prefix) ) :
        print "You (%s) can't do that"%common.current_user()

    else :

        print "Deleteing..."
        sys.stdout.flush()

        # make a dummy record, so we know that we can never delete the
        # last record created.
        pandokia.cleaner.block_last_record()

        # delete_run is chatty, so we <pre> around it
        print "<pre>"

        print "working..."
        sys.stdout.flush()

        cleaner.delete_by_query( where_str, where_dict )

        if project == '*' and context == '*' and host == '*' :
            print "delete from index"
            pdk_db.execute("DELETE FROM distinct_test_run WHERE test_run = :1",(test_run,))
            pdk_db.commit()

        print "done."

        print "</pre>"
        sys.stdout.flush()
