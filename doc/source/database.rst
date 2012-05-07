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

The CGI app needs sqlite3 to store its data.

Sqlite3 does not use a server itself; it only needs a directory to
store the database file in.  It requires working file locking.  Some
NFS servers have buggy file locking, which you can avoid by storing
the data files locally.

Sqlite3 generally does not require any direct maintenance, but note
that Pandokia uses "pragma synchronous = off;" for speed, so a
system crash can cause your database to be corrupted.  See
http://sqlite.org/pragma.html for more information.  See the functions
open_db and open_qdb in pandokia/common.py if you want to change
it.

At STScI, we keep old pandokia log files for some time.  If the
database is corrupted, we can delete it and re-import the data for
the last N days.  In light of our server reliability, this is an
acceptable risk.


Initializing the database
...........................................

Sqlite3 stores data in files in a directory.  To update the data,
you must have write access to the directory and the database files.

The directory where the data is stored is specified in pandokia/config.py
in the variable 'dbdir'.  It is a directory that must be writable
to

  - the uid that runs the CGI
  - the database administrator
  - any user that imports data

This release of pandokia uses two databases.  Type these commands
to initialize them both::

        pdk initdb db
        pdk initdb qdb

Note:  There are two databases for historic reasons.  They will
probably be merged in a future release.


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
job that is essentially::

    cd /server/that_directory
    pdk import *

to import the data.

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
add them to the "marks_tests" class.  Expected tests are added only,
never removed.

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

There is currently no direct facility for removing expected tests.
You can delete records from the table "expected" directly through
SQL.  In practice, we find it convenient to delete all of a type
of expected tests with something like::

    sqlite3 /where/ever/pdk.db
    DELETE FROM expected WHERE test_run_type = 'whatever';

then regenerate the data with "pdk gen_expected"


Importing Contacts
...........................................

Contacts are handled separately from the test results.  On any _one_
of the test machines::

    pdk_gen_contact projectname /where/ever/it/is > file.contact

    scp file.contact my_pandokia_server:

then on the server, run::

    pdk import_contact < file.contact


Emailed Announcements
...........................................

This section TBD.

Sample Nightly Scripts
...........................................

These sample scripts give you an idea of how we use Pandokia.  There
are a set of coordinated cron jobs that run our tests overnight:
on each test machines::

    cd /where/my/tests/are
    proj=my_project
    testrun=daily_`date '+%Y-%m-%d'`
    logname=/fileserver/pdk_logs/$hostname.$testrun
    pdk run ...........................................parallel 4 ...........................................log $logname ...........................................test_run $testrun ...........................................project $proj -r .

on the server::

    cd /fileserver/pdk_logs
    mkdir -p old
    pdk import /fileserver/pdk_logs/*
    mv * old

    pdk gen_expected daily daily_latest
    pdk check_expected daily daily_latest

    pdk notify -email daily_latest

Of course, we also have scripts that install the software to be tested.


Purging Old Data
...........................................

The system stores data relating to some queries in the database.
You should clean this out now and then with just::

    pdk clean

When you have test runs to delete from the database:

1. Delete the primary records::

    pdk delete_run daily_2009-03-10
        # deletes just that one day's results

    pdk delete_run ...........................................wild 'daily_2009-03-*'
        # deletes everything from March

2. Clean up related records::

    pdk clean

If you will delete several test runs, it is faster to 'pdk delete_run'
each of them, then use a single 'pdk clean' command afterwards.

Note that the database files do not get smaller when you delete
data, but space in the file is available to be re-used.

Notes:

- 'pdk clean' does a lot of work.  It tries not to keep the database
  locked for too long, but it is best to run it when the database is
  not otherwise busy.  Especially do not do this during an import,
  though you could do it immediately before you start importing data::

    pdk clean
    pdk import /directory/*

- I wonder if this sequence causes a bug::

    pdk delete_run    the_last_test_run_imported
    pdk import   some_file
    pdk clean

