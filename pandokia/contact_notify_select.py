"""This is the new means to email test reports to contacts.  As it takes shape 
users will be able to select which reports they like and the level of verbosity 
associated with said reports.
"""
import pandokia.common
from collections import defaultdict

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

#No ugly sql anymore.
#Grabs the test runs that users are associated with.
def get_user_projects(username):
	query = "SELECT project, format, maxlines FROM user_email_pref WHERE user_email_pref.username=? AND format <> 'N'"
	res = db.execute(query,(username,))
	return [ (project, format, maxlines) for project, format, maxlines in res ]

#Let us get feed back on this
def project_test_run(test_run, project):
	if (test_run,project) in test_runs :
		return test_runs[(test_run,project)]
	query = """SELECT test_name, host, context, status FROM result_scalar WHERE test_run = ? AND project = ? 
			AND status <> 'P' ORDER BY host, context, test_name """
	res = db.execute(query,(test_run,project))
	#Build up array of tuples 
	res_ary = [ (test_name, host, context, status) for test_name, host, context, status in res ]
	test_runs[(test_run,project)] = res_ary
	return res_ary
	
#summarize test with counts of pass fail error disabled and missing
# access dictionary with test_summary[(test_run,project)][host][status] host can be specific or all
def get_test_summary(test_run,project):
	sum_dict = {}
	if (test_run, project) in test_summary:
		return test_summary[(test_run,project)]
	query = """SELECT status, host FROM result_scalar WHERE test_run = ? AND project = ? """
	res = db.execute(query,(test_run,project))
	for status, host in res:
		sum_dict[host] = sum_dict.get(host,{})
		sum_dict[host][status] = sum_dict[host].get(status,0) + 1
	sum_dict['all'] = {}
	for host in sum_dict.keys():
		for status in sum_dict[host].keys():
			sum_dict['all'][status] = sum_dict['all'].get(status,0) + sum_dict[host][status]
	test_summary[(test_run,project)] = sum_dict
	return sum_dict

def create_summary(test_run,project):
	sum_str = "Project summary for " + project + " and test_run " + test_run + "\n\n"
	s_keys = ['P','F','E','D','M']
	for host in get_test_summary(test_run, project).keys():
		stats = get_test_summary(test_run,project)[host]
		sum_str += host + "\n\n"
		sum_str += "Pass, Fail, Error, Disabled, Missing\n"
		for status in s_keys:
			sum_str += str(stats.get(status,0)) + ', '
		sum_str += '\n\n'
	return sum_str
	
#create user emails based on format in user_email_pref
#THIS IS UGLY
def create_email(username, test_run) :
	email = "TEST REPORT EMAILS\n\n"
	email_str = "%s, %s, %s, %s\n"
	projects = get_user_projects(username)

	for project in projects:
		project_email =	"TestName, Host, Context, Status\n"
		project, format, maxlines = project
		if format.capitalize() == 'N':
			continue
		elif format.capitalize() == 'F':
			email += project + "\n"
			if maxlines == 0:
				email += create_summary(test_run,project)
				for  project_run in project_test_run(test_run,project):
					project_email += (email_str % project_run)
			else:
				email += create_summary(test_run,project)
				for  i, project_run in enumerate(project_test_run(test_run,project)):
					if i + 1 > maxlines: continue
					
					project_email += (email_str % project_run)
			email += project_email
		elif format.capitalize() == 'S':
			email += project + "\n"
		 	email += create_summary(test_run,project)
		email += '\n'
	return email


#add_user_pref('user1','proj1','f','5')
#add_user_pref('user1','proj2','s','42')
#add_user_pref('user1','proj3','n')
#print test_runs['run2']
print create_email('user1','run1')