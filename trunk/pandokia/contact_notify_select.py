#
# implements 'pdk email'
#
"""This is the new means to email test reports to contacts.  As it takes shape
users will be able to select which reports they like and the level of verbosity
associated with said reports.
"""
TEST = False

import pandokia
pdk_db = pandokia.cfg.pdk_db

import pandokia.helpers.easyargs as easyargs

import pandokia.common
import text_table
from collections import defaultdict
import subprocess

#A dictionary of test runs for easy storage.
test_runs = {}
test_summary = {}


if False:
    # Insert some fake test data into the user_prefs table.
    for i in range(0,100):
        pdk_db.execute( "INSERT INTO user_prefs VALUES ( :1 , :2 )", ('name_'+str(i),'email_'+str(i)))
    pdk_db.commit()

# insert pref if it exists
# format takes 'n', 's', 'f', or 'int'
def add_user_pref(username,project,format,maxlines=0):
    has_entry = pdk_db.execute(
        "SELECT username FROM user_email_pref WHERE username= :1 AND project = :2 AND format = :3 AND maxlines = :4 ",
        (username,project,format,maxlines)
        )
    if has_entry.fetchone():
        return 'has entry'
    else:
        pdk_db.execute(
            "INSERT INTO user_email_pref VALUES ( :1 , :2, :3, :4 )",
            (username,project,format,maxlines)
        )
        pdk_db.commit()
        return "Pref commited"

# For projects that a user is interested in, find the name/format/maxlines preferences
def get_user_projects(username):
    query = """SELECT project, format, maxlines FROM user_email_pref WHERE username= :1 AND format <> 'N' ORDER BY project"""
    res = pdk_db.execute(query,(username,))
    res = [ (project, format, maxlines) for project, format, maxlines in res ]
    return res

# The return value is a tuple:
#   first value is an array indexed by (host,context).  Each element is a list of (test_name, status) 
#   second value is a list of tests that "not pass" on all host/context pairs
def project_test_run(test_run, project):

    if (test_run,project) in test_runs :
        return test_runs[(test_run,project)]

    c = pdk_db.execute("SELECT DISTINCT host, context FROM result_scalar WHERE test_run = :1 AND project = :2 ORDER BY host, context ",
        ( test_run, project) )
    host_context = [ ]
    for host, context in c :
        host_context.append( (host, context) )

    # If we did not find any host/context, that means there is no report
    # in the database for this test_run/project.  Therefore, we don't need
    # to count the failed tests.  The caller will see None as our result,
    # and know it doesn't need to report anything about this case.
    if len(host_context) == 0 :
        test_runs[(test_run,project)] = (None, None)
        return (None, None)

    query = """SELECT host, test_name, context, status FROM result_scalar WHERE test_run = :1 AND project = :2
            AND status <> 'P' ORDER BY host, context, test_name """
    res = pdk_db.execute(query,(test_run,project))

    # we make an array where
    #   tests[name] is a dict
    #       ['hc'] is a list of host/contexts where that test "not pass"
    #       ['s'] is the status
    tests = {}
    for host, test_name, context, status in res:
        tests[test_name] = tests.get(test_name,{'hc' : [], 's' : []})
        tests[test_name]['hc'].append( (host,context) )
        tests[test_name]['s'].append(status)

    # Now convert that into the actual result

    res_ary = { }
    all_list = [ ]
    for test_name in tests:
        test = tests[test_name]

        # if it affected all of the host/context, list it in the all_list
        # otherwise, list it under the host/context

        if len(test['hc']) == len(host_context) :
            all_list.append(test_name)
        else :
            for hc in test['hc'] :
                res_ary[hc] = res_ary.get(hc,[])
                res_ary[hc].append( ( test_name, test['s'][0] ) )

    test_runs[(test_run,project)] = res_ary, all_list

    return res_ary, all_list
        
#summarize test with counts of pass fail error disabled and missing
# access dictionary with test_summary[(test_run,project)][host][status] host can be specific or all
def get_test_summary(test_run,project):
    sum_dict = {}
    all_hosts = {}
    if (test_run, project) in test_summary:
        return test_summary[(test_run,project)]
    query = """SELECT status,context, host FROM result_scalar WHERE test_run = :1 AND project = :2 """
    res = pdk_db.execute(query,(test_run,project))

    for status, context, host in res:
        sum_dict[host] = sum_dict.get(host,{})
        sum_dict[host][context] = sum_dict[host].get(context,{})
        sum_dict[host][context][status] = sum_dict[host][context].get(status,0) + 1

    for host in sum_dict.keys():
        for context in sum_dict[host].keys():
            for status in sum_dict[host][context].keys():
                all_hosts[status] = all_hosts.get(status,0) + sum_dict[host][context][status]
    sum_dict['All'] = all_hosts

    for host in sum_dict.keys():
        if host == 'All':
            sum_dict[host]['T'] = sum(sum_dict[host].values())
        else:
            for context in sum_dict[host].keys():
                sum_dict[host][context]['T'] = sum(sum_dict[host][context].values())
    test_summary[(test_run,project)] = sum_dict
    #print sum_dict
    return sum_dict

# turn the summary into table content
def create_summary(test_run,project):
    sum_str = "Project summary for " + project + " and test_run " + test_run + "\n\n"
    cols = ['Host','Context','Total', 'Pass', 'Fail', 'Error', 'Disabled', 'Missing']
    stat_keys_sorted = ['T','P','F','E','D','M']
    sum_table = text_table.text_table()
    for col_name in cols:
        sum_table.define_column(col_name)
    test_summary = get_test_summary(test_run, project)
    hosts = test_summary.keys()
    hosts.sort()
    #for i, host in enumerate(hosts):
    #if host == 'All':
    sum_table.set_value(0, 0, 'All')
    sum_table.set_value(0, 1, 'All')
    for i, status in enumerate(stat_keys_sorted):
        sum_table.set_value(0,i+2, test_summary['All'].get(status,0))
    for i, host in enumerate(hosts):
        if host != 'All':
            contexts = test_summary[host].keys()
            contexts.sort()
            sum_table.set_value(i,0,host)
            for j, context in enumerate(contexts):
                sum_table.set_value(i+j,1,context)
                for k, status in enumerate(stat_keys_sorted):
                    sum_table.set_value(i+j,2+k,test_summary[host][context].get(status,0))

    #contexts  = test_summary[host].keys()
    #for context in context.sort():
    #print context
    #make up tables for this email.

    return sum_table

# create user emails based on format specified in the user_email_pref table

def create_email(username, test_run) :

    email = "Test report for %s:\n\n" % test_run

    email += 'For more detail see %s?query=day_report.2&test_run=%s\n\n' % ( pandokia.common.cfg.pdk_url, test_run )

    projects = get_user_projects(username)

    num_proj = len(projects)

    # For some of the formats, we may not send the email if there is
    # nothing to say.  Set this flag any time you know that you need to
    # actually send the email.
    send_notice = False

    # For each project the user is interested in
    for project in projects:
        project, format, maxlines = project

        # no need to compute anything if the user does not want to look at it
        if format == 'n' :
            continue

        # Do not print the project header yet.  format 'c' does not say anything at all
        # if there is nothing to report.

        if format == 'c' :
            email += 'format c no longer supported'
            format = 'f'

            if 0 :
                # show only the test that the user is listed as a contact for.
                # (this needs work; see get_contact_report() for details)
                #
                r = pandokia.contact_notify.get_contact_report(username, project, test_run)
                if r is not None :
                    email += "Project: "+ project + "\n\n"
                    email += pandokia.contact_notify.get_contact_report(username, project, test_run)
                    email += '\n'
                    send_notice = True
                continue


        # format 'f' skips the report if there is nothing to say.
        # format 'F' does it every time

        if format.capitalize() == 'F':

            # anything is True/False for whether there was anything in
            # the test_run/project (passing or not).  This is used to
            # suppress the report when the project does not exist in this
            # test run.
            anything, all_hosts, some_hosts = build_report_table(test_run,project,maxlines)

            if anything :
                if ( ( all_hosts is None ) and ( some_hosts is None ) ) :
                    if (format == 'F') :
                        email += "Project: "+ project + "\n\n    No problems to report\n\n"
                        send_notice = True
                    continue

                email += "Project: "+ project + "\n\n"

                if all_hosts is not None :
                    email += "These tests had a problem on all hosts and on all contexts\n"
                    email += all_hosts.get_rst()
                    email += "\n"
                    send_notice = True

                if some_hosts is not None :
                    email += "These tests had a problem on some hosts\n"
                    email += some_hosts.get_rst()
                    email += "\n"
                    send_notice = True
            continue

        # format 's' always displays a result

        if format.capitalize() == 'S':
            email += "Project: "+ project + "\n\n"
            summary = create_summary(test_run,project)
            email += summary.get_rst()
            email += '\n'
            send_notice = True
            continue

    if not send_notice :
        return None

    return email

# Make some tables for a particular user.  test_run is the test run
# we are interested in. project is which project we are interested in.
# maxlines is the max number of lines to put in a table that lists specific
# test results.

def build_report_table(test_run,project,maxlines):
    # There are two tables: one for tests that had a problem on all hosts,
    # and one that had a problem on only some hosts.  Initialize both
    # tables now.
    some_hosts = text_table.text_table()
    for col_name in ( 'Host', 'Context', 'Test Name', 'Status' ) :
        some_hosts.define_column(col_name)

    all_hosts  = text_table.text_table()
    all_hosts.define_column('Test Name')

    # we want to say "N more" when there are more than maxlines in the
    # table.  These are the counts of N for the two tables
    all_hosts_more_count = 0
    some_hosts_more_count = 0

    # Pick up the data
    hc_array, all_list = project_test_run(test_run,project);

    if hc_array is None and all_list is None:
        return (False, None, None)

    ## construct the table of tests that had problems in some places

    # sorted list of affected host/context names
    hc_list = hc_array.keys()
    hc_list.sort()

    # process the data for each host
    for hc in hc_list:

        # sort by the test name
        hc_array[hc].sort()

        # stuff the material into that table
        for val in hc_array[hc] :

            # find the next row in the table
            row = some_hosts.get_row_count()

            # just count it if the table is too full
            if row >= maxlines and maxlines > 0:
                some_hosts_more_count += 1
                continue

            # separate the host/context from the index tuple
            host, context = hc

            # insert a row
            test_name, status = val
            some_hosts.set_value(row,'Host',     host)
            some_hosts.set_value(row,'Test Name',test_name[0:75])
            some_hosts.set_value(row,'Context',  context)
            some_hosts.set_value(row,'Status',   status)

    ## construct the table of tests that had problems everywhere

    for x in all_list :
        row = all_hosts.get_row_count()

        # just count it if the table is too full
        if row >= maxlines and maxlines > 0:
            all_hosts_more_count += 1
            continue

        all_hosts.set_value(row,'Test Name', x[0:75])

    # if we cut off either table for going over the maxlines, add a line
    # at the end showing how many lines we cut off.  This happens after
    # the end of the loop so we can have a correct total

    if all_hosts_more_count > 0 :
        all_hosts.set_value( all_hosts.get_row_count() , 'Test Name' , '%d more' % all_hosts_more_count )

    if some_hosts_more_count > 0 :
        some_hosts.set_value( some_hosts.get_row_count() , 'Test Name' , '%d more' % some_hosts_more_count )

    # if either table didn't have anything in it, return None for that one.

    if all_hosts.get_row_count() == 0 :
        all_hosts = None

    if some_hosts.get_row_count() == 0 :
        some_hosts = None

    return (True, all_hosts, some_hosts)


#actually send the email
def sendmail(addy, subject, text):
    """Interface to the mail system is sequestered here. Presently just
    uses the shell mail command."""
    if TEST:
        import getpass
        addy = getpass.getuser()
        #then don't irritate people by sending test emails; send them
        #all to the user running the test instead
    print "mail to ",addy
    sub = subprocess.Popen( [ 'mail', '-s', subject, addy ], shell=False, stdin=subprocess.PIPE)
    sub.stdin.write(text)
    sub.stdin.close()

    sub.wait()
    return sub.returncode


def run(args):
    argspec = {
        '-r' :  '=+',
        '-s' :  '=',
        '--help'    : '',
        '--test_run' :  '-r',
        '--subject' :   '-s',
        }
    opt, args = easyargs.get( argspec, args )

    if opt['--help'] :
        print """
-r
--test_run
    specify a list of test runs to report on

-s
--subject
    specify a subject for the email

other parameters are users to send email to (not email addresses)
"""
        return 0

    if '-r' in opt :
        test_runs = [ pandokia.common.find_test_run(x) for x in opt['-r'] ]
    else :
        test_runs = [ pandokia.common.find_test_run("daily_latest") ]

    if args:
        # for each user name, look it up the email address in the table
        users = [ ]
        for user in args :
            found = 0
            c = pdk_db.execute("SELECT email FROM user_prefs WHERE username = :1", (user,))
            for email, in c :
                users.append( (user, email) )
                found=1
            if not found :
                print "No email address known for user",user
    else:
        # get a list of all the (user, email) from the user prefs
        query = """SELECT username, email FROM user_prefs"""
        user_res = pdk_db.execute(query)
        users = [(user,email) for user,email in user_res]

    if '-s' in args :
        subject = args['-s']
    else :
        subject = 'Test Results: %s' % ', '.join([ x for x in test_runs ])

    # compute the email to send to each user; send it.
    for user, email in users:
        if email is None :
            continue
        msg = ''
        for x in test_runs :
            newmsg = create_email(user, x)
            if newmsg is not None :
                msg = msg + newmsg
        if len(msg) > 0 and email :
            sendmail(email, subject, '%s\n\n\nThis report created for %s'%(msg, email))
        else :
            print "suppress blank email to ", email

#add_user_pref('user1','proj1','f','5')
#add_user_pref('user1','proj2','s','42')
#add_user_pref('user1','proj3','n')
#print test_runs['run2']
#print create_email('user1','run1')
