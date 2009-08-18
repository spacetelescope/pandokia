-- pdk_query.db
--
-- This database only contains information about queries from currently
-- active web clients.
--
-- Since we are running the database in mode that risks corruption in a
-- crash (but is faster), these tables are in a separate database.  If
-- we crash, we delete this database.  People lose some of their bookmarked
-- queries, but nothing else.

-- query_id:
--	qid is integer primary key to generate unique query numbers
--	time is used to know when we can purge the record

CREATE TABLE query_id (
	qid 	INTEGER PRIMARY KEY, 	-- unique number of query
	time	VARCHAR			-- last time a cgi touched this query
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
