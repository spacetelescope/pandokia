"""This is the new means to email test reports to contacts.  As it takes shape
users will be able to select which reports they like and the level of verbosity
associated with said reports.
"""
TEST = False
import pandokia.common
import pandokia.contact_notify
import text_table
from collections import defaultdict
import subprocess

db = pandokia.common.open_db()

#A dictionary of test runs for easy storage.
test_runs = {}
test_summary = {}


#Let us insert some test data into the user_prefs table.
if False:
    query = 'INSERT INTO user_prefs VALUES (?,?)'
    for i in range(0,100):
        db.execute(query,('name_'+str(i),'email_'+str(i)))
    db.commit()

# insert pref if it exists
# format takes 'n', 's', 'f', or 'int'
def add_user_pref(username,project,format,maxlines=0):
    query = 'INSERT INTO user_email_pref VALUES (?,?,?,?)'
    check_query = "SELECT username FROM user_email_pref WHERE username=? AND project = ? AND format = ? AND maxlines = ?"
    has_entry = db.execute(check_query,(username,project,format,maxlines))
    if has_entry.fetchone():
        return 'has entry'
    else:
        db.execute(query,(username,project,format,maxlines))
        db.commit()
        return "Pref commited"

#Grabs the test runs that users are associated with.
def get_user_projects(username):
    query = """SELECT project, format, maxlines FROM user_email_pref WHERE username=? AND format <> 'N' ORDER BY project"""
    res = db.execute(query,(username,))
    res = [ (project, format, maxlines) for project, format, maxlines in res ]
    return res

#Let us get feed back on this
def project_test_run(test_run, project):
    hosts_q = """SELECT DISTINCT(host) FROM result_scalar WHERE test_run = ? AND project = ?
             ORDER BY host, context, test_name"""
    context_q = """SELECT DISTINCT(context) FROM result_scalar WHERE test_run = ? AND project = ?
            AND status <> 'P' ORDER BY host, context, test_name"""

    host_res = db.execute(hosts_q,(test_run,project))
    hosts = len([host for host, in host_res])

    context_res = db.execute(context_q,(test_run,project))
    contexts = len([context[0] for context in context_res])

    tests = {}
    res_ary = {}
    if (test_run,project) in test_runs :
        return test_runs[(test_run,project)]

    query = """SELECT host, test_name, context, status FROM result_scalar WHERE test_run = ? AND project = ?
            AND status <> 'P' ORDER BY host, context, test_name """
    res = db.execute(query,(test_run,project))
    #res_ary = [ (host, test_name, context, status) for host, test_name, context, status in res]

    for host, test_name, context, status in res:
        tests[test_name] = tests.get(test_name,{'h' : [], 'c' : [], 's' : []})
        tests[test_name]['h'].append(host)
        tests[test_name]['c'].append(context)
        tests[test_name]['s'].append(status)

    #tests[test_name].sort()
    for test_name, test in tests.iteritems():
        if len(test['h']) < hosts or len(set(test['c'])) < contexts:
            for i in range(0,len(test['h'])):
                #print test['h'][i], hosts
                res_ary[test['h'][i]] =  res_ary.get(test['h'][i],[])
                res_ary[test['h'][i]].append((test['c'][i],test_name,test['s'][i]))
        elif len(test['h']) == hosts and len(set(test['c'])) == contexts:
            res_ary['All'] =  res_ary.get('All',[])
            res_ary['All'].append((test['c'][0],test_name,test['s'][0]))
    #Build up array of tuples
    test_runs[(test_run,project)] = res_ary
    return res_ary


#summarize test with counts of pass fail error disabled and missing
# access dictionary with test_summary[(test_run,project)][host][status] host can be specific or all
def get_test_summary(test_run,project):
    sum_dict = {}
    all_hosts = {}
    if (test_run, project) in test_summary:
        return test_summary[(test_run,project)]
    query = """SELECT status,context, host FROM result_scalar WHERE test_run = ? AND project = ? """
    res = db.execute(query,(test_run,project))

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

#create user emails based on format in user_email_pref
#THIS IS UGLY
def create_email(username, test_run) :
    user_email_q = """SELECT email FROM user_prefs WHERE username = ?"""
    user_email_res = db.execute(user_email_q,(username,))
    user_email = [email for email, in user_email_res]
    email = "Test report for %s:\n\n" % test_run
    projects = get_user_projects(username)
    num_proj = len(projects)
    send_notice = False

    for project in projects:
        project, format, maxlines = project

        # no need to compute anything if the user does not want to look at it
        if format == 'n' :
            continue

        # Do not print the project header yet.  format 'c' does not say anything at all
        # if there is nothing to report.

        if format == 'c' :
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

            all_hosts, some_hosts = build_report_table(test_run,project,maxlines)

            if ( ( all_hosts is None ) and ( some_hosts is None ) ) :
                if (format == 'F') :
                    email += "Project: "+ project + "\n\n    No problems to report\n\n"
                    send_notice = True
                continue

            email += "Project: "+ project + "\n\n"

            if all_hosts is not None :
                email += "These tests failed on all hosts and on all contexts\n"
                email += all_hosts.get_rst()
                email += "\n"
                send_notice = True

            if some_hosts is not None :
                email += "These tests failed on some hosts\n"
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

    email += '\n\nThis email created for %s\n' % username

    return email

def build_report_table(test_run,project,maxlines):
    # Make some tables for a particular user.  The data is all in
    # memory in the dictionary test_run.  project is which project we are
    # interested in.

    # There are two tables: one for tests that had a problem on all hosts,
    # and one that had a problem on only some hosts.  Initialize both
    # tables now.
    all_hosts  = text_table.text_table()
    some_hosts = text_table.text_table()

    for col_name in ( 'Host', 'Context', 'Test Name', 'Status' ) :
        all_hosts.define_column(col_name)
        some_hosts.define_column(col_name)

    # we want to say "N more" when there are more than maxlines in the
    # table.  We have no convenient place to keep that value, so I'm
    # stuffing it into the text_table object.  This works in python, though
    # it isn't particularl good practice.
    all_hosts .stash_more_count = 0
    some_hosts.stash_more_count = 0

    # Pick up the data
    test_run = project_test_run(test_run,project);

    # If there is nothing there, we can leave early
    if len(test_run.keys()) == 0:
        return ( None, None )


    # sorted list of affected host names
    hosts = test_run.keys()
    hosts.sort()

    # process the data for each host
    for host in hosts:

        # sort by the test name
        test_run[host].sort()

        # pick which table this is going in
        if host == 'All':
            table = all_hosts
        else:
            table = some_hosts

        # stuff the material into that table
        for val in test_run[host] :

            # find the next row in the table
            row = table.get_row_count()

            # just count it if the table is too full
            if row >= maxlines and maxlines > 0:
                table.stash_more_count += 1
                continue

            # insert a row
            context, test_name, status = val
            table.set_value(row,'Host',     host)
            table.set_value(row,'Test Name',test_name)
            table.set_value(row,'Context',  context)
            table.set_value(row,'Status',   status)

    # if we cut off either table for going over the maxlines, add a line
    # at the end showing how many lines we cut off.  This happens after
    # the end of the loop so we can have a correct total

    if all_hosts.stash_more_count > 0 :
        all_hosts.set_value( all_hosts.get_row_count() , 'Test Name' , '%d more' % all_hosts.stash_more_count )

    if some_hosts.stash_more_count > 0 :
        some_hosts.set_value( some_hosts.get_row_count() , 'Test Name' , '%d more' % some_hosts.stash_more_count )

    # if either table didn't have anything in it, return None for that one.

    if all_hosts.get_row_count() == 0 :
        all_hosts = None

    if some_hosts.get_row_count() == 0 :
        some_hosts = None

    return (all_hosts, some_hosts)


#actually send the email
def sendmail(addy, subject, text):
    """Interface to the mail system is sequestered here. Presently just
    uses the shell mail command."""
    if TEST:
        import getpass
        addy = getpass.getuser()
        #then don't irritate people by sending test emails; send them
        #all to the user running the test instead
    sub = subprocess.Popen( [ 'mail', '-s', subject, addy ], shell=False, stdin=subprocess.PIPE)
    sub.stdin.write(text)
    sub.stdin.close()

    sub.wait()
    return sub.returncode


def run(args):
    user = 'nobody'
    test_run = pandokia.common.find_test_run("daily_latest")
    if args:
        # for each user name, look it up the email address in the table
        users = [ ]
        for user in args :
            found = 0
            c = db.execute("SELECT email FROM user_prefs WHERE username = ?", (user,))
            for email, in c :
                users.append( (user, email) )
                found=1
            if not found :
                print "No email address known for user",user
    else:
        # get a list of all the (user, email) from the user prefs
        query = """SELECT username, email FROM user_prefs"""
        user_res = db.execute(query)
        users = [(user,email) for user,email in user_res]

    subject = 'Test Results: %s' % test_run

    # compute the email to send to each user; send it.
    for user, email in users:
        msg = create_email(user, test_run)
        if msg is not None :
            sendmail(email, subject, msg)

#add_user_pref('user1','proj1','f','5')
#add_user_pref('user1','proj2','s','42')
#add_user_pref('user1','proj3','n')
#print test_runs['run2']
#print create_email('user1','run1')
