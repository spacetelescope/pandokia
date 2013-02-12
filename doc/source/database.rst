Pandokia Database Administration
--------------------------------

Initial Setup
...........................................



Running Tests
...........................................

TODO: fix this to know the current state of the implementation

 - XX_latest , XX_yesterday recognizes if XX is in cfg.recurring_prefix

 - common.looks_like_a_date() to show day names

 - common.run_previous(), common.run_next()

See doc/pdk_aware.txt for details on running tests.  The result of
running a test with pdkrun is one or more pdk log files.  You somehow
need to get those to your pandokia server where you can import them
into the database with the 'pdk import' command.

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
If you do not complete an import, you can run it again; you just
get a lot of warnings about records that already exist.

Expected / Missing Tests
...........................................

The database keeps a list of expected tests according to a class
of test runs.

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

Contacts are handled separately from the test results.  On any `one`
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


Deleting Old Test Data
...........................................

When you have test runs to delete from the database:

Delete the primary records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    pdk delete -test_run daily_2009-03-10
        # deletes just that one day's results

You can use "*" as a wild card if it is at the beginning or end of a name: ::

    pdk delete -test_run 'user_xyzzy_2012-07-*'

You can use SQL wild cards: ::

    pdk delete -test_run 'user_xyzzy_2012-07-%'

You can specify multiple parameters to delete only a portion of a
test run.  It will delete only that portion that matches all the
parameters listed: ::

    pdk delete -test_run 'user_xyzzy_*' -project 'pyetc' -context 'trunk'
        -host 'etcbrady' -status 'M'

This will not delete records that are part of any test run marked
"valuable".

Delete secondary records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The initial delete only removes enough of the data to make the
test no longer appear on the reports.  There is a second step
that is not performed at this stage because it is much slower.

Clean up related records::

    pdk clean

Because of the large volume (easily many millions of records for a
single day's test runs), this step can take a long time.  Instead
of requiring this to happen during `pdk delete`, we provide it as
a separate step.

`pdk clean` does the delete in groups of a few hundred tests at a
time.  You can interrupt it whenever you get tired of waiting, then
restart it again later.

It is not necessary to run the clean step every time you delete
records.  In a normal system, an administrator will run the clean
step from time to time.

Notes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- If you will delete several test runs, it is convenient to 'pdk delete'
  each of them, then use a single `pdk clean` command afterwards.  We
  commonly allow anyone to run `pdk delete` alone, then run a scheduled
  `pdk clean` during off hours.

- The database files do not necessarily get smaller when you delete
  data, but space in the file is available to be re-used.

- 'pdk clean' does a lot of work.  In sqlite, it tries not to keep
  the database locked for too long, but that is hard to achieve.
  If using sqlite, it is best to run it when the database is not
  otherwise busy.


STScI Routine Database Cleaning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pandokia.cfg.pdk_db.table_usage() returns the current database size
as best it can for the database you are using.  Part of our continuous
integration system uses this call to generate a report when the
database exceeds our current limit.

When it does, we have somebody identify the oldest daily test runs
in the database and delete them with a command like ::

    pdk delete -test_run 'daily_2012-10-%'

We repeat that command for each type of daily test runs (we have
several), and then run ::

    pdk clean

We usually delete a month at a time.  Because of our high test
volume (several million records per month), both of these steps
take a very long time.


Deleting Old QID data
...........................................

The system stores data relating to some queries in the database.
You should clean this out now and then with just::

    pdk clean_queries


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

    pdk email daily_latest

Of course, we also have scripts that first install the software to be tested.


Some Database Notes
..................................................

Here are some database notes:

Mysql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    mysql -p
    create database pandokia;
    use pandokia;

    drop database pandokia;

::

    set password [ for user ] = password("xyzzy") ;

::

    use mysql;
    update user set password=PASSWORD("xyzzy") where user = 'dude' ;
    flush privileges;


