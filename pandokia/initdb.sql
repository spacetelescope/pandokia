-- pdk.db
--
-- This is the schema for the main database.  It contains all
-- there is to know about the test results.
--

-- result_scalar:
--	each row represents a single test result

CREATE TABLE result_scalar (
	key_id 		INTEGER PRIMARY KEY, 
		-- primary key is assigned by database; this is a
		-- unique identifier
	test_run 	VARCHAR,
	project 	VARCHAR,
	context		VARCHAR,
	test_name 	VARCHAR,
		-- this is the tuple that identifies a specific test
		-- results
	host VARCHAR,
		-- what computer did this test run on.  You might
		-- argue that this should be a TDA, but it seems
		-- important enough to institutionalize
	status VARCHAR,
		-- 'P' = pass
		-- 'E' = error (could not complete test)
		-- 'F' = fail
		-- 'M' = missing
		-- 'D' = disabled (told not to run)
		-- 'Uxxx' for any user defined status
	test_runner VARCHAR,
		-- what type of test runner ran this test
	start_time VARCHAR,
	end_time VARCHAR,
		-- times in the database are like 
		-- '2009-03-06 12:22:57.752' 
		-- represented in local time.  The pdk log can
		-- contain a floating point time_t ( time.time() ) in UTC.
	location VARCHAR,
		-- where can I find this test that was run
	attn VARCHAR
		-- blank or "Y" for "needs attention"
		-- "N" for "not a problem"
		-- "R" for "problem resolved"
	);

CREATE UNIQUE INDEX result_scalar_test_identity 
	ON result_scalar ( test_run, project, host, test_name, context );

CREATE INDEX result_scalar_test_run_only 
	ON result_scalar ( test_run ) ;

CREATE INDEX result_scalar_host
	ON result_scalar ( host );

CREATE INDEX result_scalar_project
	ON result_scalar ( project );

CREATE INDEX result_scalar_test_name 
	ON result_scalar ( test_name );

-- result_tda:
--	one row for each Test Definition Attribute
--	rows belong to records in result_scalar with matching key_id

CREATE TABLE result_tda (
	key_id INTEGER,
	name VARCHAR,
	value VARCHAR
	);

CREATE INDEX result_tda_key_id
	ON result_tda ( key_id ) ;

CREATE INDEX result_tda_index 
	ON result_tda(name) ;

CREATE INDEX result_tda_full
	ON result_tda ( key_id, name, value);

-- result_tra:
--	one row for each Test Result Attribute
--	rows belong to records in result_scalar with matching key_id

CREATE TABLE result_tra (
	key_id INTEGER,
	name VARCHAR,
	value VARCHAR
	);

CREATE INDEX result_tra_key_id
	ON result_tra ( key_id ) ;

CREATE INDEX result_tra_index 
	ON result_tra(name) ;

CREATE INDEX result_tra_full
	ON result_tra ( key_id, name, value ) ;


-- result_log:
--	one row for each test: separate because logs might be big; also
--		maybe move to a separate db
--	row belongs to record in result_scalar with matching key_id

CREATE TABLE result_log (
	key_id INTEGER,
	log VARCHAR
	);


CREATE INDEX result_log_index
	ON result_log ( key_id ) ;

-- contact:
--	convert a project/test_run/host to a list of email addresses

CREATE TABLE contact (
	project	VARCHAR,
	test_name VARCHAR,
	email VARCHAR
	);

CREATE INDEX contact_index 
	ON contact ( project, test_name );

-- expected:
--	which tests are expected in various types of test_runs
--	You can use the check_expected script if you populate this
--	table for your test_run_type.

CREATE TABLE expected (
	test_run_type VARCHAR,
		-- this "daily_" or something like that; the information
		-- that connects the test_run_type to an actual test_run
		-- comes from outside the database.
	project VARCHAR,
	host VARCHAR,
	test_name VARCHAR,
	context VARCHAR
		-- project, host, test_name, context as in result_scalar
	);

CREATE UNIQUE INDEX expected_unique 
	ON expected ( test_run_type, project, host, test_name );
		-- we only need one entry

-- projects:
-- 	It is getting too slow to find all the projects by "select
-- 	distinct test_run from result_scalar".  So, I'm going to
--	make a table that just contains the distinct values.

CREATE TABLE distinct_test_run (
	name VARCHAR UNIQUE
	);


-- user preferences:

CREATE TABLE user_prefs (
	username VARCHAR,	-- user name as authenticated by web server
	email VARCHAR	-- email address where notices should be sent
	-- add whatever else we need here
	);

CREATE TABLE user_email_pref (
	username VARCHAR,
	project VARCHAR,
	format VARCHAR
		-- format is one of:
		-- 'n' = none; send no email about this project
		-- 's' = send only a summary of what happened in this project
		-- 'f' = send full list of non-passing tests
		-- integer = send a full list, but at most N tests
	);
