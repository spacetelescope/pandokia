-- POSTGRES SUPPORT DOES NOT WORK!
--
-- Pandokia assumes that inserts into a table with a SERIAL PRIMARY
-- KEY will return the inserted value of the key as cursor.lastrowid;
-- In fact, that is not what pyscopg2 does.  You need to do something
-- different from how you do it in sqlite and mysql, which is not
-- yet implemented.
--

-- postgres does not have auto-increment, so we use an explicit sequence
-- for the key_id in result_scalar.
CREATE SEQUENCE sequence_key_id ;



-- ok_transactions:
--  each row corresponds to one transaction (one mouse click on "Flag OK")

CREATE TABLE ok_transactions (
    trans_id        INTEGER PRIMARY KEY,
    username        VARCHAR,
    user_comment    VARCHAR(100),
    ip_address      VARCHAR,
    status          VARCHAR,
    qid             INTEGER
);

-- ok_items:
--  each row is a test result that has been OK'd

CREATE TABLE ok_items (
    trans_id    INTEGER,
    key_id      INTEGER,
    status      VARCHAR
);




-- result_scalar:
--	each row represents a single test result

CREATE TABLE result_scalar (
	key_id 		INTEGER,
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
	status CHAR(1),
		-- 'P' = pass
		-- 'E' = error (could not complete test)
		-- 'F' = fail
		-- 'M' = missing
		-- 'D' = disabled (told not to run)
		-- lower case reserved for any user defined status
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
	attn VARCHAR,
		-- blank or "Y" for "needs attention"
		-- "N" for "not a problem"
		-- "R" for "problem resolved"
        has_okfile CHAR(1),
                -- 0 or 1 indicating whether this test had a tda_okfile attribute
        chronic CHAR(1)
                -- 0 or 1 indicating whether this test is a chronic problem
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

-- this particular query is used to look up each line of the day_report
CREATE INDEX result_scalar_day_report
        ON result_scalar ( context, status, host, project, test_run ) ;

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
	ON expected ( test_run_type, project, host, test_name, context );
		-- we only need one entry

-- distinct_test_run:
-- 	It is getting too slow to find all the projects by "select
-- 	distinct test_run from result_scalar".  So, I'm going to
--	make a table that just contains the distinct values.

CREATE TABLE distinct_test_run (
	test_run VARCHAR UNIQUE,
	valuable CHAR(1),
		-- boolean, but portable; use 1 or 0
		-- valuable means that we should not refuse to delete
		-- this test run.
	record_count INTEGER,
		-- how many records in this test run
		-- if 0 or NULL, we dont know
        note VARCHAR(100)
                -- a brief note about this test run
		-- set first char to '*' to mark read-only
	);


-- user preferences:

CREATE TABLE user_prefs (
	username VARCHAR,	-- user name as authenticated by web server
	email VARCHAR	-- email address where notices should be sent
	-- add whatever else we need here
	);

CREATE UNIQUE INDEX user_prefs_username_index 
	ON user_prefs ( username );

CREATE TABLE user_email_pref (
	username VARCHAR,
	project VARCHAR,
	format CHAR(1),
		-- format is one of:
		-- 'n' = none; send no email about this project
		-- 's' = send only a summary of what happened in this project
		-- 'f' = send full list of non-passing tests
	maxlines INTEGER
		-- if full list, show at most N tests
	);


-- query_id:
--	qid is integer primary key to generate unique query numbers
--	time is used to know when we can purge the record

CREATE SEQUENCE sequence_qid;

CREATE TABLE query_id (
	qid 	INTEGER,		-- unique number of query
	time	VARCHAR,		-- time_t a cgi last touched this query
	expires	INTEGER,		-- time_t when it is ok to delete this query
	username VARCHAR,		-- who claimed this qid
	notes    VARCHAR
	);

CREATE INDEX query_id_index 
	ON query_id ( qid ) ;

-- query:
--	The rows in this table are a list of "interesting" results for a
--	particular query.
--		qid = query number
--		key_id matches a record in result_scalar in pdk.db 

CREATE TABLE query (
	qid	INTEGER,		-- query number
	key_id	INTEGER			-- identity of a thing in the list
	);

CREATE INDEX query_index 
	ON query ( qid ) ;

-- delete_queue:
--	deleting stuff in pandokia is very slow.  We have multiple tables
--	to update for every deletion, and there is no good way to make
--	that happen fast.  So, when you delete a test run, copy the key_ids 
--	to delete_queue.  Later, a background process goes around deleting
--	those key_ids from tda/tra/log tables.  You dont have to wait
--	for it.
--

CREATE TABLE delete_queue (
	key_id INTEGER
	);

CREATE INDEX delete_queue_key_id ON 
	delete_queue ( key_id ) ;

-- hostinfo:
--      descriptions of various hosts
CREATE TABLE hostinfo (
        hostname        VARCHAR(64),
        os              VARCHAR(64),
        description     VARCHAR(10240)
        );

CREATE INDEX hostinfo_index
        ON hostinfo ( hostname );


-- chronic problem tests:
--      this is a lot like expected:  it has the test identity and
--      a type of test run.  The "when" field is a date/time of
--      when it first went bad.  The difference between the time
--      of today's test run and "when" tells us whether a test is
--      chronic or not.

CREATE TABLE chronic (
        test_run_type VARCHAR,
                -- this "daily_" or something like that; the information
                -- that connects the test_run_type to an actual test_run
                -- comes from outside the database.
        project VARCHAR,
        host VARCHAR,
        test_name VARCHAR,
        context VARCHAR,
                -- project, host, test_name, context as in result_scalar
        xwhen VARCHAR
                -- indicator of when the test first went bad
        );

CREATE UNIQUE INDEX chronic_u ON chronic ( test_run_type, project, host, test_name, context );

