===============================================================================
Database Programming in Pandokia
===============================================================================

:abstract:

	Pandokia uses a SQL-based database.  It uses it directly through DBAPI,
	not through an ORM.  There are some conventions to follow to implement
	more portable SQL.

.. contents::

DBAPI limitations
-------------------------------------------------------------------------------

DBAPI defines something that looks like a standard interface to databases,
but you can't quite write a program assuming DBAPI and expect it to work
with any database that offers a DBAPI interface.

One big problem comes in parameter passing.  If you look at PEP 249
( http://www.python.org/dev/peps/pep-0249/ ), you can see 5 possible
values for paramstyle.  None of them are available in every database.

Notably, mysqldb and pyscopg2 offer only 'format' and 'pyformat', while
sqlite3 offers 'qmark', 'named', and some parameter formats that are not 
part of DBAPI.

Solution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The solution is an SQL execute that converts a standard format for parameters
to whatever the database engine wants.

cursor = pdk_db.execute( statement, parameters )

	perform a database action with named parameters

	statement contains an instance of :AAA for each named parameter.
	The parameter name has to match the regular expression pattern [a-zA-Z0-9\_]+

	If parameters is a dict, it will be used as-is.

	If parameters is a list or tuple, it will be converted into
	a dict with keys '1', '2', '3', ..., so you can write your
	query using :1, :2, :3, etc.

	If parameters is any other type, it is an error.

	It IS NOT permitted to have the character ':' in your sql,
	even if it occurs inside a string literal.

	It IS NOT permitted to have the character '%' in your sql,
	even if it occurs inside a string literal.  (This limitation
	is inherited from some of the DBAPI implementations.)

The return value is a cursor 

Why this interface?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is easy and fast for regex substition to convert this to something
that any dbapi database can use.

I would like your sql to be allowed to say " where a like 'arf%' ",
but the % will not correctly pass through some of the dbapi
implementations.  Since this interface is intended to be portable,
you can't have the %.

Stylistically, I like ":arf" better than "%(arf)s"

General Usage
-------------------------------------------------------------------------------

Within pandokia ::

	import pandokia
	pdb_db = pandokia.cfg.pdk_db

	cursor = pdk_db.execute( query, parameters )

Always fully specify the columns to retrieve; never use "SELECT \*".

Use :1, :2, ... for parameters when you have only a fixed set of parameters. ::

	c = pdk_db.execute("select a, b from tbl where a = :1 and b = :2",('a_value','b_value'))
	for x in c :
		print c[0],c[1]


If you want to use this database access layer with another system:

 - using MySQLdb: ::

	import pandokia.db_mysql

	db = pandokia.db_mysql.PandokiaDB( access_arg )
		# access_arg is the same as you would use with MySQLdb

 - using sqlite3 or pysqlite2: ::

	import pandokia.db_sqlite as dbdriver

	db = pandokia.db_sqlite.PandokiaDB( filename )

The object does not connect to the database when you create it.
You can call db.open() to explicitly connect, or it will connect
to the database the first time it needs the connection.


Schemas
-------------------------------------------------------------------------------

If you use database-specfic features in your schema, you just have
to write a separate schema for each database engine.  This is not
so bad if you have a small number of tables.

Dynamically constructed WHERE clauses
-------------------------------------------------------------------------------

The parameter to where_dict is a list of ( column_name, value ),
where column_name is a required column name and value is a value
to match.  All the columns are ANDed together.  If the value for
a column is a list, the possible values are ORed together.

The value may contain "\*x", "x\*", or "\*x\*", which will be converted
to "%x", "x%", or "%x%".  Other glob-like characters are not
permitted.

The value may contain '%' to cause a LIKE expression.  The '_'
character does NOT create a LIKE expression because it is too common
in our data values.

There is no good way to search for literals containing \*, %, [, or ?

Example: ::

	where_text, where_dict = pdk_db.where_dict( [ 
		( 'a', 1 ), 
		( 'b', [ 'x', 'y' ] ),
		( 'c', 'z*' )
		]

	c = pdk_db.execute("SELECT a,b FROM tb %s"%where_text, where_dict)

is equivalent to ::

	where_text = "WHERE ( a = :1 ) AND ( b = :2 OR b = :3 ) AND ( c LIKE :4 )"
	where_dict = { 
		'1' : 1,
		'2' : 'x',
		'3' : 'y',
		'4' : 'z%'
		}
	c = pdk_db.execute("SELECT a,b FROM tb %s"%where_text, where_dict)


COMMIT / ROLLBACK
-------------------------------------------------------------------------------

Commit and rollback work the same; use the pandokia database object: ::

	pdk_db.commit()

	pdk_db.rollback()


Exceptions
-------------------------------------------------------------------------------

IntegrityError happens when you violate a database constraint. ::

	db = xxx.PandokiaDB( args )

	try :
		c = db.execute('INSERT INTO ...')
	except db.IntegrityError as e :
		...

ProgrammingError is a problem such as a syntax error in your SQL. ::

	try :
		c = db.execute('...')
	except db.ProgrammingError as e :
		...


Table Usage
-------------------------------------------------------------------------------

You can ask the database for the amount of space used by the data.
There is not always a clear answer to this question, but this
function returns the best available answer in a database specific
way: ::

	i = db.table_usage()
	print "using %d bytes"%i

In mysql, this is the sum of the table and index sizes from "SHOW TABLE STATUS".

In sqlite3, this is the size of the database file.

EXPLAIN QUERY
-------------------------------------------------------------------------------

You can get a description of how the database will evaluate the query with: ::

	s = pdk_db.explain_query( text, qhere_dict )
	print s

This is highly database dependent.
