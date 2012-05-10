Pandokia Database Administration
--------------------------------

- Overview
- Initializing the Database
- Running Tests
- Importing Test Results
- Expected / Missing Tests
- Emailed Announcements
- Sample Nightly Scripts
- Purging Old Data


Overview
........

The CGI app needs a database to store its data.  For each supported
database, there is a file of SQL statements in pandokia/sql that
will create the necessary tables and indexes.  

Initializing the database : sqlite
...........................................

Sqlite3 support is normally built into Python.  You can look for it
by ::

    python
    import sqlite3

If you do not get an error, you already have sqlite support.  If
you do not, you can re-compile python with sqlite support, or you
can install pysqlite from http://pypi.python.org/pypi/pysqlite/

Sqlite3 does not use a server itself; it only needs a directory to
store the database file in.  It requires working file locking.  Some
NFS servers have buggy file locking, which you can avoid by storing
the data files locally.

The directory and the database files must be writable to

  - the uid that runs the CGI
  - the database administrator
  - any user that imports data with "pdk import"

Enter the name of the database in config.py, then ::

    sqlite3 /path/to/database/file.db < pandokia/sql/sqlite.sql

TODO: ref to editing config file

Sqlite3 generally does not require any direct maintenance, but note
that Pandokia uses "pragma synchronous = normal;" for speed.  Certain
types of crashes can cause your database to be corrupted.  

See http://sqlite.org/pragma.html#pragma_synchronous for more
information.  There is not a configuration for this, but it only
happens once in pandokia/db_sqlite.py


Initializing the database : MySQL
...........................................

TODO: describe using mysql

TODO: describe grants

Initializing the database : Postgres
...........................................

TODO: describe using mysql

TODO: describe grants

Running Tests
...........................................

See doc/pdk_aware.txt for details on running tests.  The result of
running a test with pdkrun is one or more pdk log files.  You somehow
need to get those to your pandokia server where you can import them
into the database.

There is a special set of test run names that follow the pattern
'daily_YYYY-MM-DD' where Y/M/D are the year/month/day of the test.
These names get special treatment in the display software.  We run
that test run each day and automatically import the results into
our system.

For example, last night it ran 'daily_2009-08-17'.  I can query
this through the web interface either by that name or by 'daily_latest',
which is converted to today's date internally.

If you run daily tests (e.g. for continuous integration), it is
helpful to use this naming convention.


Importing Test Results
...........................................

When you have you pdk log files on the server host, use::

    pdk import filename

to import each one into the database.  

At STScI, many machines write their pdk log files to a common
directory on a file server.  On the pdk server host, we have a cron
job that is essentially ::

    cd /server/that_directory
    pdk import *

to import the data after all the tests are run.

When a test result is already in the database, it prints a warning.

Expected / Missing Tests
...........................................

The database keeps a list of expected tests according to a class
of test runs.  You can populate the table with SQL INSERT statements,
but it is easier to just update from an existing test run.

In our system, the morning cron job imports the results from the
previous night's tests, then executes these commands::

    pdk gen_expected daily daily_latest

In this example, "daily" is the class of tests and "daily_latest"
is translated into the name of last night's test run.

You can have as many types of expected test as you like, and you
can update the expected list from whatever test run you like.
For example::

    pdk gen_expected marks_tests mark-25

would find all the tests currently listed for test run mark-25 and
add them to the "marks_tests" class.  In this operation, expected
tests are added only, never removed.  If you run gen_expected several
times, you get the union of all the tests identified.

Once you have a class of expected tests defined, you can check if
all of them are present in a test run::

    pdk check_expected daily daily_latest

finds any "daily" tests that are not present in the latest daily
test run::

    pdk check_expected marks_tests mark-26

checks that mark-26 contains all of the expected marks_tests tests.
Any that are missing will be entered in the database with status M
(for missing).

If a missing test is imported later, the imported data replaces the
M record.

When a test is no longer expected, you can remove that expectation
in two ways:

 * When viewing a list of tests in the web UI, you can select tests
   and use the "Not Expected" button.

 * You can remove records from the database table directly. ::

    sqlite3 /where/ever/pdk.db
    DELETE FROM expected WHERE test_run_type = 'whatever';


Importing Contacts
...........................................

Contacts are handled separately from the test results.  On any _one_
of the test machines::

    pdk_gen_contact projectname /where/ever/it/is > file.contact

    scp file.contact my_pandokia_server:

then on the server, run::

    pdk import_contact < file.contact

This adds contacts only.  To remove contacts, delete records from
the table "contact".  For example, you can delete all contacts with
the SQL command::

    DELETE FROM contact;

and then import them all again.


Emailed Announcements
...........................................

This section TBD.

Sample Nightly Scripts
...........................................

These sample scripts give you an idea of how we use Pandokia.  There
are a set of coordinated cron jobs that run our tests overnight:

on each test machine: ::

    cd /where/my/tests/are
    proj=my_project
    testrun=daily_`date '+%Y-%m-%d'`
    logname=/fileserver/pdk_logs/$hostname.$testrun
    pdk run -parallel 4 -log $logname -test_run $testrun -project $proj -r .

on the server: ::

    cd /fileserver/pdk_logs
    mkdir -p old
    pdk import /fileserver/pdk_logs/*
    mv * old

    pdk gen_expected   daily daily_latest
    pdk check_expected daily daily_latest

    pdk email

TODO: shouldn't the 'pdk email' command need to know the test run name?

Of course, we also have scripts that install the software to be tested.


Purging Old Data
...........................................

The system stores data relating to some queries in the database.
You should clean this out now and then with just::

    pdk clean_queries

When you have test runs to delete from the database:

TODO: This is obsolete

1. Delete the primary records::

    pdk delete_run daily_2009-03-10
        # deletes just that one day's results

    pdk delete_run ...........................................wild 'daily_2009-03-*'
        # deletes everything from March

2. Clean up related records::

    pdk clean

If you will delete several test runs, it is faster to 'pdk delete_run'
each of them, then use a single 'pdk clean' command afterwards.

Note that the database files do not necessarily get smaller when
you delete data, but space in the file is available to be re-used.

Notes:

- 'pdk clean' does a lot of work.  In sqlite, it tries not to keep the database
  locked for too long, but it is best to run it when the database is
  not otherwise busy.  Especially do not do this during an import,
  though you could do it immediately before you start importing data::

    pdk clean
    pdk import /directory/*

