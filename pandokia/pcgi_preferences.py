#
# pandokia - a test reporting and execution system
# Copyright 2010, Association of Universities for Research in Astronomy (AURA) 
#
# User Preference page
#

import sys
import cgi
import urllib
import pandokia
import pandokia.text_table as text_table
import pandokia.pcgi
import common

cfg = pandokia.cfg

output = sys.stdout

def run( ) :
    # 
    # all the user preference cgi entry points come here
    #

    # The common page header:
    output.write(common.cgi_header_html)
    output.write(common.page_header())

    #

    form = pandokia.pcgi.form

    # find out whose preferences we are handling
    user = common.current_user()

    if user is None :
        output.write('This web server does not perform authentication, so pandokia does not know about user names.<br>')
        output.write('Using the user name "nobody" for testing, but do not expect it to be useful.<br>')
        user='nobody'

    # dispatch this to the relevant subtype
    if 'subtype' in form :
        x = form['subtype'].value
    else :
        x = 'show'

    if x == 'show' :
        show(user)
    elif x == 'save' :
        if ( 'newuser' in form ) and ( user in cfg.admin_user_list ) :
            if form['submit'].value == 'newuser' :
                newuser = form['newuser'].value
                save(newuser)
            else :
                save(user)
        else :
            save(user)
    elif x == 'add_project' :
        add_project(user)
    elif x == 'list' :
        if user in cfg.admin_user_list :
            list_users()

    if user in cfg.admin_user_list :
        output.write('<p><a href=%s?query=prefs&subtype=list>list all</a></p>'%common.get_cgi_name())
        sys_report()

def sys_report() :
        output.write('<p>You are admin.</p>')
        output.write(__file__)

# show the user preferences as an input form
def show(user) :

    form = pandokia.pcgi.form

    #
    output.write('<h1>User Preferences: %s</h1>'%cgi.escape(user))

    # write the start of form, including hidden fields needed to dispatch
    # to the save() function after we submit the form.
    output.write('<form action=%s method=GET>'%common.get_cgi_name())
    output.write('<input type=hidden name=query value=prefs>')
    output.write('<input type=hidden name=subtype value=save>')

    # show the user's email address
    c = cfg.pdk_db.execute('SELECT email FROM user_prefs WHERE username = :1',(user,))
    x = c.fetchone()
    if x is None :
        email = user
    else :
        email, = x

    output.write('<h3>Email address</h3>')
    output.write('Email address: <input type=text name=email value="%s">'%email)
    output.write('<br>\n')

    # make a table of what the user has selected for each project
    output.write('<h3>Email Preferences</h3>')

    tb = text_table.text_table()
    tb.define_column("project",showname='Project')
    tb.define_column("none",showname='None')
    tb.define_column("contact",showname='Contact')
    tb.define_column("summ",showname='Summary')
    tb.define_column("full",showname='Full')
    tb.define_column("all", showname='Always')
    tb.define_column("line",showname='Max')

    row = 0

    def ckif(x) :
        if format == x :
            return 'checked'
        else :
            return ''

    c = cfg.pdk_db.execute('SELECT username, project, format, maxlines FROM user_email_pref WHERE username = :1 ORDER BY project', (user,))

    c = [ x for x in c ]

    if len(c) == 0 :
        try :
            x = cfg.default_user_email_preferences
        except :
            x = [ ]
        c = [ ( user, x[0], x[1], x[2] ) for x in x ]

    for username, project, format, maxlines in c :
        if not project_name_ok :
            output.write('bad project name in table<br>')
            continue
        tb.set_value(row, 'project', project)

        project = urllib.quote(project)
        # projects will be a list of all the projects we are submitting in the form
        output.write('<input type=hidden name=projects value="%s">'%project)

        # radio.%s will be the radio button for that project name 
        tb.set_value(row, 'none', html='<input type=radio name="radio.%s" value="n" %s>'%(project, ckif('n')))
        tb.set_value(row, 'contact', html='<input type=radio name="radio.%s" value="c" %s>'%(project, ckif('c')))
        tb.set_value(row, 'summ', html='<input type=radio name="radio.%s" value="s" %s>'%(project, ckif('s')))
        tb.set_value(row, 'full', html='<input type=radio name="radio.%s" value="f" %s>'%(project, ckif('f')))
        tb.set_value(row, 'all', html='<input type=radio name="radio.%s" value="F" %s>'%(project, ckif('F')))

        # maxlines is an integer, but 0 means no limit.  display it as a blank field
        if (maxlines == 0) :
            maxlines = ''

        # radio.%s will be the radio button for that project name 
        tb.set_value(row, 'line', html='<input type=text name="line.%s" value="%s" size=5>' % (project,maxlines))
        row = row + 1

    tb.set_html_table_attributes('border=1')
    output.write(tb.get_html())

    # some explanatory text
    output.write('''<p>None=no email about that project<br>
     Contact=email only tests you are a contact for<br>
     Summary=email contains only a count<br>
     Full=show all tests with problems, skip projects with none<br>
     Always=show all tests with problems, show all projects with problems or not<br>
     Max=list at most max tests in the email</p>''')
    output.write('<input type=submit name=submit value=save>')

    if user in cfg.admin_user_list :
        output.write('<br>')
        output.write('<input type=text name=newuser>')
        output.write('<input type=submit name=submit value=newuser>')
    output.write('</form>')

    # this is a different form - it just adds a project to the list of
    # projects that the user has preferences for
    output.write('<form action=%s method=GET>'%common.get_cgi_name())
    output.write('<input type=hidden name=query value=prefs>')
    output.write('<input type=hidden name=subtype value=add_project>')
    output.write('<input type=text name=project>')
    output.write('<input type=submit name=submit value="Add Project">')
    output.write('</form>')

    # done
    

# add a project to the user's project list
def add_project(user) :
    form = pandokia.pcgi.form

    project = form['project'].value

    if not project_name_ok(project) :
        output.write('Project names can contain upper/lower case letters, digits, underline, dot, and slash.')

    else :
        cfg.pdk_db.execute("INSERT INTO user_email_pref ( username, project, format, maxlines ) VALUES ( :1, :2, 'n', 0)",(user, project))
        cfg.pdk_db.commit()
        output.write('added %s'%cgi.escape(project))

    output.write('<br>')
    output.write('<a href=%s?query=prefs>Back to preference page</a>'%common.get_cgi_name())


# save the user preferences
def save(user) :
    form = pandokia.pcgi.form

    email = None
    if 'email' in form :
        email = form['email'].value

    if email is None or email == 'None' :
        email = user
    
    # save the email address that they entered
    cfg.pdk_db.execute('DELETE FROM user_prefs WHERE username = :1',(user,))
    cfg.pdk_db.execute('INSERT INTO user_prefs ( email, username ) VALUES ( :1, :2 )',(email,user) )

    # projects is a list of all the projects that the form is submitting
    for project in form.getlist('projects') :
        if not project_name_ok(project) :
            continue

        # pick out the value of the radio button.
        field_name = 'radio.%s'%project
        if field_name in form :
            format = form[field_name].value
        else :
            format = 'n'

        # ignore it if they are messing with us
        if not format in [ 'c', 'n', 'f', 'F', 's' ] :
            format = 'n'


        # pick out the value of the text field that shows how many tests
        # we want reported
        field_name = 'line.%s'%project
        if field_name in form :
            maxlines = form[field_name].value
        else :
            maxlines = ''

        # if it is not blank or an integer, blank it out
        try :
            maxlines = int('0'+maxlines) 
        except ValueError :
            maxlines = ''

        # delete and insert instead of update because we may be adding new projects.
        cfg.pdk_db.execute('DELETE FROM user_email_pref WHERE username = :1 and project = :2',(user, project))
        try :
            maxlines = int(maxlines)
        except :
            maxlines = 0
        cfg.pdk_db.execute('INSERT INTO user_email_pref ( username, project, format, maxlines ) VALUES ( :1, :2, :3, :4 )', (user, project, format, maxlines))


    cfg.pdk_db.commit()
    output.write('Preferences saved.<br>')
    output.write('<a href=%s?query=prefs>Back to preference page</a><br>'%common.get_cgi_name())
    output.write('<a href=%s>Back to top level</a><br>'%common.get_cgi_name())
        

# limit project names to things we can use as field names in a cgi
def project_name_ok(project) :
    import re
    return re.match('^[a-zA-Z0-9_./-]*$',project)

def list_users() :

    # Make sure that every user in he user_email_pref table also has a
    # a user name in user_prefs table.  We can probably find a better place
    # to put this.
    c = cfg.pdk_db.execute(" SELECT DISTINCT username FROM user_email_pref WHERE "
        " username NOT IN ( SELECT username FROM user_prefs ) " )
    for x, in c :
        print "user %s not in user_prefs table - adding<br>"%cgi.escape(x)
        cfg.pdk_db.execute("INSERT INTO user_prefs ( username ) VALUES ( :1 )", (x,))
    cfg.pdk_db.commit()

    # Make a table showing all the user prefs.
    tb = text_table.text_table()
    tb.define_column('username')
    tb.define_column('email')
    row = 0

    # find all the project names that anybody knows about.  This list is
    # only chosen from those projects that somebody has asked to get email
    # about, so it can look in the user preferences instead of searching all
    # the results for project names.
    project = [ ]
    c = cfg.pdk_db.execute("SELECT DISTINCT project FROM user_email_pref ORDER BY project")
    for (x,) in c :
        project.append(x)
        tb.define_column('p.'+x, showname=x)

    # for each user, add a row to the table
    c = cfg.pdk_db.execute("SELECT username, email FROM user_prefs ORDER BY username")
    for user, email in c :
        # stuff the fixed material into the table
        tb.set_value(row, 0, user)
        tb.set_value(row, 1, email)

        # find for each project that this user has a preference about:
        c1 = cfg.pdk_db.execute("SELECT project, format, maxlines FROM user_email_pref WHERE username = :1",(user,))
        for p,f,m in c1 :
            # stuff that preference into the table.
            if m is not None :
                f = '%s %s'%(f,m)
            tb.set_value(row, 'p.'+p, cgi.escape(f))

        row = row + 1

    tb.set_html_table_attributes('border=1')
    output.write(tb.get_html())

