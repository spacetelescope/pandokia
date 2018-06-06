# Pandokia

[![Documentation Status](https://readthedocs.org/projects/pandokia/badge/?version=latest)](https://pandokia.readthedocs.io/en/latest/?badge=latest)

**"All your test are belong to us!"**

# What is Pandokia?

Pandokia is a test reporting system.  It organizes test results
obtained from other testing systems, such as nose, py.test, or
similar testing systems for other languages.

The tests are organized in to test runs, projects, contexts (e.g.
for different execution environments), and a hierarchy based on
their location in the file system.  There is a web interface to
examine the test results.

There is a simple text import format, and any testing system that
can be persuaded to write data in that format can be used with
Pandokia.

It is not required to use Pandokia to run your tests, but there is
a mechanism for Pandokia to run tests from a directory tree.  It
uses glob patterns to recognize files containing different types
of tests and uses an appropriate test runner for each file.  For
example, our continuous integration system has a mixture of tests
written for nose, py.test, bourne shell, and a legacy system for
IRAF tasks.

Pandokia was begun in 2009 at the Science Software Branch of the
Space Telescope Science Institute.  It has been in use continuously
since then, but it is still a work in progress.

One of the first projects to use it was the Pysynphot Commissioning,
which had 25,000 tests of the new software.  As of January 2014,
we have many different projects, with totals in the range of 100,000
to 300,000 tests per day.  We routinely store a few months of test
results, so our test database is currently on the order of 500 GB.

Pandokia uses either MySQL or SQLite for a database.  SQLite is a
serverless SQL database that is normally included with Python.  We
used SQLite until our database grew above 50 GB.  It might well
have continued to work, but SQLite has performance problems when
many concurrent users make large transactions.

More details are at:

http://ssb.stsci.edu/testing/pandokia


## General Warning

Since Pandokia is primarly developed for internal use, we are
often working on some of the more peripheral features.  The
fact that this is marked as a production quality release indicates
that the core of the system has been shown to be fairly reliable.
It does not indicate that every feature works well or that it is
commercial quality software.


# Installing Pandokia

Pandokia operates in two major modes:

TEST-ONLY refers to a machine that will run tests.

SERVER refers to a machine that runs the pandokia web application.  If
you install the necessary third party softare, this machine can also
run tests.

The outline is:

- install third party software  [both]
- run setup.py                  [both]
- edit config.py                [SERVER only]
- initialize the database       [SERVER only]
- configure web server          [SERVER only]


# Third-Party Software to run tests

Pandokia has native ability to run tests in Python, shell scripts,
and in any program that can indicate pass/fail with an exit status.
It can also use tests written for various test frameworks, if you have
those frameworks installed.

It is not necessary to install these first (Pandokia will find them at
run time), but you may find it helpful to have some of:

## nose

For running tests in Python that are based on nose.

http://pypi.python.org/pypi/nose/

## py.test

For running tests in Python that are based on py.test.

http://www.pytest.org
http://pypi.python.org/pypi/pytest/

## FCTX

For running tests in C.  The bare minimum necessary to
compile and execute tests is included with Pandokia,
but there is also quite good documentation and example
code available on their web site.

http://fctx.wildbearsoftware.com/

## shunit2

**As modified to work with pandokia**

For running tests in bourne shell and relates shells
such as bash.  As of this writing, the stock shunit2
does not work with Pandokia, but a patched version is
available.

http://ssb.stsci.edu/testing/shunit2/

You can find the original patches in the pandokia source
code in the directory patches/

## unittest2

For running tests in Python that are based on unittest2.
The Pandokia support for this is not extensively tested,
but it seems to work.

http://pypi.python.org/pypi/unittest2


# Requirements

For a server machine, you will need a web server and a database system.

Pandokia is a single CGI script that should (in principle) work with
any CGI-capable web server.  Not surprisingly, we use Apache.  There is
a baby web server included; you can use it to try out pandokia, but I
really wouldn't recommend it for production use.


## Supported Databases

### sqlite3

The sqlite3 python package is included with the python
source code, but the python package is only present if
you have the sqlite3 libraries on your system.

```
$ python
>>> import sqlite3
```

If you get an error, you do not have sqlite support in your
python interpreter. You need to get it from somewhere.

- Many linux distributions have a sqlite package and sqlite support in their python distribution.

- You can install the library from sqlite.org and re-compile your python interpreter.

- In principle, you can install the library from sqlite.org and then re-build only the sqlite3 python module, but I never tried this.

- You can use the "pysqlite2" package available from pypi.python.org

### mysql

Support for mysql requires the MySQLdb python package.

http://mysql-python.sourceforge.net/

### postgres

Support for postgres requires the psycopg2 python package.

http://initd.org/psycopg/

There are some minimal notes on setting up pandokia
with postgres on Ubuntu at the end of the file
pandokia/db_psycopg2.py


## Run setup.py

Pandokia has a standard python setup.py.  Here are two ways to
use it:

```bash
python setup.py -q install
```

This installs in the default location.

```bash
python setup.py -q install --home /some/path
```

This installs pandokia in `/some/path`.  The scripts will be
in `/some/path/bin` and the python files will be in
`/some/path/lib/python`.

You must set your `PATH` and `PYTHONPATH` environment variables
to include these directories.


## Edit config.py on the SERVER

```bash
pdk config
```

to find the location of the configuration file.  Edit it for your
specific site.  The defaults are suitable for most of the values,
but you will want to change these for your site:

Select the database driver you want to use.  Enter the relevant access
        information.

### user_list

This is a list of user names that are allowed access to the
application.  Your web server must implement authentication
for this to work.

This feature is not well-tested.

### admin_user_list
Admin users have some extended access, such as the ability to delete test runs belonging to other users.

### pdk_url
This is the URL provided in the email reports as a shortcut for users to access the browsable reports.

## Edit config.py on the TEST-ONLY systems

Most of the default values in the config file are sufficient for
a TEST-ONLY system, but:

### exclude_dirs

Directories with these names are ignored when looking for tests.

## Initialize the Database

You only need a database on a SERVER machine.

**.... tbd ....**


## Configure Web Server

**If you're using the pandokia test web server, skip this section.**

You only need a web server on a SERVER machine.

The pandokia web app is a single CGI.

We expect that the web server will perform any access control that
is necessary.  For example, our pandokia server uses SSL and HTTP
BasicAuth to restrict access to authorized users.  We also have
firewall rules in place. Pandokia itself provides no access control
mechanisms.

To copy the pandokia application into the web server, you can use

```bash
which pdk
```

to find the name of the pdk program, then

```bash
cp /where/ever/it/was/pdk /your/web/server/cgi-bin/pdk.cgi
```

NB: The file you are copying from is named "pdk" and the file
you are copying to is named "pdk.cgi" or whatever other name is
necessary for your web server to run it as a CGI.

During the setup.py phase, the location of the pandokia software
and the config file were written into this file, so it does not
need any further configuration.  At this point, you should be able
to access it through your web server.


## Using the pandokia test web server

The pandokia web server is a baby web server that is just barely
capable of serving static files and running CGI programs.  To use
it to run pandokia:

```bash
mkdir tmp
cd tmp
cp `which pdk` pdk.cgi
pdk webserver
```

then point your browser at `localhost:7070`.  Click on `pdk.cgi` to
access the pandokia server.

This is a very primitive web server.  Notably. it has no logging
and no authentication.  You can use this to try out pandokia, but
if you plan to use pandokia for any kind of servious application,
you should get a real web server.


### Notes on Configuring Web Servers

I can't help you with web server configuration.  Most web servers
are very complicated, and I don't even run my own web server.  (I
have an IT department that handles that.)

You can find information about authentication in Apache at:
http://httpd.apache.org/docs/2.0/howto/auth.html

You can find information about authentication in thttpd at:
http://acme.com/software/thttpd/thttpd_man.html


# What next?

Pandokia is now installed on your system. Next, read:

- `doc/READMEFIRST.txt` for information about the system

- `doc/demo.txt` to see how to import some demo data into the database.

- `doc/pdk_aware.txt` to see how to run your own tests

