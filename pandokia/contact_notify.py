#
# This is the obsolete version
#

"""This module supports the 'pdk notify' verb to send notification
emails to the designated contacts for any tests that failed, had errors,
or are missing. If some tests have contact='unknown', the report for those
tests will be printed to stdout and the return status will be set to 1.

In addition to the run routine, the module contains helper functions that
query the database, construct the email from the database results, and
send the email.
"""

TEST = True

import pandokia
import pandokia.common #should do try/except too

sqlite3 = pandokia.common.get_db_module()

import subprocess
from collections import defaultdict
import sys, os
import getpass #used for TESTing

def extract_info(testrun=None, status=None, project=None):
    """Extract contact, name, and status info from the database.
    This information can then be used to create contact-specific emails.

    testrun = string specifying the test run to use; defaults to daily_latest
    status = string specifying match pattern for status; defaults to [EFM]
    project = not presently used; hook for future feature
    """

    #Update default values
    if testrun is None:
        testrun = 'daily_latest'
    if status is None:
        status = "[EFM]" #Problems: failed, error, missing

    # cdict[contact] is a list of tests relevant to contact.  Each
    # list item is (hostname, project, name, status).  We will return
    # cdict to the caller

    cdict=defaultdict(list)

    # failcount[(project,name)] is how many tests matching (project,name)
    # had a problem.  This is not just status=F.

    failcount=defaultdict(int)
    
    # lookup[(project,name)] is the list of contacts for the test
    # identified by (project,name).  This is worth caching because
    # the same (project,name) occurs on multiple hosts.
    lookup=dict()
    
    #Open the database
    db = pandokia.common.open_db()

    #Get the list of failed tests
    f = db.execute("""SELECT test_name, status, project, host
                      FROM result_scalar
                      WHERE (test_run = ? AND
                             status GLOB ?)""",
                   (pandokia.common.find_test_run(testrun), status))
    
    #Populate dictionary
    for item in f:
        name, status, project, hostname = item

        #Failure bookkeeping
        failcount[(project,name)]+=1

        # Find the list of contacts for this test; first try our cache,
        # then look it up in the database.
        try:
            contact=lookup[(project, name)]
        except KeyError:
            lookup[(project,name)]= [ ]
            c = db.execute("""SELECT email, test_name
                              FROM contact
                              WHERE project = ? AND test_name = ?""",
                              (project, name))
            for m in c:
                email, testname = m
                if not email in lookup[(project, name)] :
                        lookup[(project, name)].append(email)

            contact=lookup[(project, name)]
            
        # Add this result to the list for each contact
        for c in contact :
            cdict[c].append((hostname, project, name, status))

        # ... and for unknown if we don't have any contacts
        if len(contact) == 0 :
            cdict['unknown'].append((hostname, project, name, status))

        # ... and for the generic "receives all notices" message
        cdict['*'].append((hostname, project, name, status))
        

    #clean up & return dict
    return cdict, failcount

def extract_stats(testrun=None):
    """Extract some overall statistics from the database for a given
    testrun; defaults to daily-latest.
    This information can then be used to organize useful reports."""
    
    #Update default values
    if testrun is None:
        testrun = 'daily_latest'
    testrun = pandokia.common.find_test_run(testrun)
    
    #Open the database
    db = pandokia.common.open_db()

    #Extract the total hostcount for each test, regardless of status,
    #subdivided by project
    hostcount=dict()
    c = db.execute("""SELECT project, test_name, count(distinct host)
                      FROM result_scalar
                      WHERE test_run = ?
                      GROUP BY project, test_name""",
                   (testrun,))

    #Parse the result
    for k in c:
        project, test, total = k
        hostcount[(project,test)]=total

    #Extract all the hosts that were used for this test run,
    #to initialize the hostfail dictionary
    c = db.execute("""SELECT distinct host
                      FROM result_scalar
                      WHERE test_run = ?""",
                   (testrun,))
    hostfail=list()
    for k in c:
        hostfail.append(k[0])


    #Extract the set of hosts with statuses
    c = db.execute("""SELECT host, status, count(distinct test_name)
                      FROM result_scalar
                      WHERE test_run = ? 
                      GROUP BY host, status""",
                   (testrun,))
    
    #parse the result
    for k in c:
        host, status, count = k
        if status == 'P':
            try:
                hostfail.remove(host)
            except ValueError:
                pass #ok, already removed


    #Return the answers
    return hostfail, hostcount


def write_email(addy, rows, testrun, hdr=None):
    """Write the file that will be sent by email.
    addy = email address
    rows = report content
    hdr = report header; defaults to something generic.
    """
    if hdr is None:
        if addy == '*' :
            hdr = "The test run had these anomalous test results:"
        else :
            hdr = "You are listed as contact for these anomalous test results:"
        hdr = '''
Test Run %s

For more detail see %s?query=day_report.2&test_run=%s

%s
''' % ( testrun, pandokia.cfg.pdk_url, testrun, hdr )


    outname='pdk_%s_eml.txt'%addy
    out=open(outname,'w')
    out.write(hdr)
    out.write("\n")
    for k in rows:
        out.write("%s\n"%str(k))

    out.close()
    return outname


def some_host_sort(a,b) :
    (a_host,a_project,a_test,a_stat) = a
    (b_host,b_project,b_test,b_stat) = b

    if a_project != b_project :
        return cmp(a_project,b_project)
    if a_test != b_test :
        return cmp(a_test,b_test)
    return cmp(a_host,b_host)
    
def formatlist(inlist,failcount,hostcount,hostfail,limit_to_project=None):
    """Reformat a list of failed tests into a semi-smart report
    that groups out special cases

    inlist = list of tests that did not pass
    failcount = dict {(project,test): number of hosts on which it did not pass}
    hostcount = dict {(project,test): number of hosts on which it was run}
    hostfail = list of hosts on which all tests did not pass
    """

    #Get the max width for each case so we can prettyprint
    cols=zip(*inlist)

    # ???
    maxwid=[str(max([len(x) for x in c])) for c in cols]

    # At this line, maxwid looks like this: ['6', '6', '49', '1']
    # The numbers are the column widths for the report

    efmt = "%-"+"s %-".join(maxwid[1:]) + "s"
    mfmt = "%-"+"s %-".join(maxwid) + "s"

    # At this line, mfmt looks like this: '%-6s %-6s %-49s %-1s'
    # The column order matches the order in a tuple somewhere.
    
    #Do a bit more bookkeeping
    everywhere=list()
    mixed=defaultdict(list)
    myhosts=set()
    myprojects=set()
    
    for h,p,t,s in inlist:
        if limit_to_project and ( not p == limit_to_project ) :
            continue
        if failcount[(p,t)] == hostcount[(p,t)]:
            everywhere.append((p,t,s))  #test failed everywhere it was run
        elif h not in hostfail:
            mixed[(p,t)].append((s,h))  # ?
        myhosts.add(h)
        myprojects.add(p)
                       
    rows=[]

    #Special case 1: all tests failed on a host
    badhost=[h for h in hostfail if h in myhosts]

    if len(badhost)>0:
        rows.append('All tests (not just yours) had a problem on:')
        rows.append('\n'.join(badhost))
        rows.append('')
        
    #Special case 2: tests that failed on all hosts
    if len(everywhere) > 0:
        rows.append('The following tests had a problem on all hosts:')
        for p,t,s in sorted(set(everywhere)):
            rows.append(efmt%(p,t,s))
        rows.append('')
        
    #Now the usual case: tests that failed some places
    if len(mixed) > 0:
        rows.append('The following tests had a problem on some hosts:')
        mixed_list = [ ]
        for x in mixed :
            ( project, test ) = x
            for (stat, host) in mixed[x] :
                mixed_list.append((host,project,test,stat))
        mixed_list = sorted(mixed_list, some_host_sort)
        for (host,project,test,stat) in mixed_list :
            rows.append(mfmt%(host,project,test,stat))


    #Don't send mail if the only content of the message will be
    #the message that all tests failed on some machines
    if (len(badhost) > 0 and
        len(everywhere) == 0 and
        len(mixed) == 0):
        rows=list()
    
    return rows
                   

                            
def sendmail(addy, subject, fname):
    """Interface to the mail system is sequestered here. Presently just
    uses the shell mail command."""

    if TEST:
        #then don't irritate people by sending test emails; send them
        #all to the user running the test instead
        args=(fname, subject+addy, getpass.getuser())
    else:
        args=(fname, subject, addy)
        
    mail_cmd = "cat %s | mail -s '%s' %s"%args
    stat=subprocess.call(mail_cmd, shell=True)
    return stat

def run(args):
    """Entry point for pdk <verb> interface. In our case, the verb is
    "notify". At present it takes one (optional) argument: the name of
    the testrun; if omitted, it will default to daily_latest. """

    flag_file=0
    flag_email=0

    if '-file' in args :
        flag_file = 1
        args.remove('-file')
    if '-email' in args :
        flag_email = 1
        args.remove('-email')

    try:
        testrun=args[0]
    except IndexError:
        testrun = 'daily_latest'
    testrun = pandokia.common.find_test_run(testrun)

    retstat=0
    
    #Get the stats
    hostfail, hostcount=extract_stats(testrun=testrun)
    
    #get the data
    cdict,failcount = extract_info(testrun=testrun)

    #loop through to send the emails

    for contact, tests in cdict.items():

        report=formatlist(tests,failcount,hostcount,hostfail)
        if len(report) > 0:
            outname=write_email(contact, report, testrun)
            if contact != 'unknown':
                if flag_email :
                    stat=sendmail(contact, '%s anomalies'%testrun, outname)
                if not flag_file :
                    os.unlink(outname)
            else:
                retstat=1 #return failure so we know there were unknowns
                f=open(outname)
                for line in f :
                    sys.stdout.write(line)
                f.close()
                if not flag_file :
                    os.unlink(outname)
                

    #All done
    return retstat

if __name__ == '__main__':
    #This is a test interface, not recommended for actual use.
    from pandokia.default_config import *
    retstat = run(sys.argv[1:])


#
# get_contact_report() is used in contact_notify_select.py to send the
# type of email where the user wants to be notified only of those tests
# that they are a contact for.  The basic features in the original
# contact_notify _almost_ do what we need, but not quite.
#
# For efficiency reasons, we want to compute the list of anomalous tests
# for all the contacts at the same time.  So, get_contact_report() computes
# that and forms a cache.
# 
# bug:  This whole file needs to know about the "context" field.

class struct(object):
    pass

gcr_cache = { }

def get_contact_report(username, project,test_run) :

    index = ( project, test_run )
    if not index in gcr_cache :
        gcr_cache[index] = struct()
        gcr_cache[index].hostfail,  gcr_cache[index].hostcount = extract_stats(testrun=test_run)
        gcr_cache[index].cdict,     gcr_cache[index].failcount = extract_info(testrun=test_run)

    tests = gcr_cache[index].cdict[username]
    report=formatlist(tests,gcr_cache[index].failcount,gcr_cache[index].hostcount,gcr_cache[index].hostfail,limit_to_project=project)
    if len(report) == 0 :
        return None

    return '\n'.join(report)
