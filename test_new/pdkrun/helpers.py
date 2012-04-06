import os
import pandokia.helpers.test_in_db as test_in_db

test_in_db.query['test_name'] = 'pdkrun_test_data/pytest/*'

expected_results = [
    #  test_name,
    #       dict of values for equivalence
    #
    # remember the db access library automatically converts things that look like numbers to float

	( 'pdkrun_test_data/helpers/file_age.f_older_p',
		{ 'status' : 'P' } ),
	( 'pdkrun_test_data/helpers/file_age.f_newer_p',
		{ 'status' : 'P' } ),
	( 'pdkrun_test_data/helpers/file_age.f_newer_f',
		{ 'status' : 'F' } ),
	( 'pdkrun_test_data/helpers/file_age.f_older_f',
		{ 'status' : 'F' } ),
	( 'pdkrun_test_data/helpers/file_age.hour_older_p',
		{ 'status' : 'P' } ),
	( 'pdkrun_test_data/helpers/file_age.hour_older_f',
		{ 'status' : 'F' } ),
	( 'pdkrun_test_data/helpers/file_age.day_older_p',
		{ 'status' : 'P' } ),
	( 'pdkrun_test_data/helpers/file_age.day_older_f',
		{ 'status' : 'F' } ),

test_in_db.perform_db_tests( test_in_db.query , expected_results )

