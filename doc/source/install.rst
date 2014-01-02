===================
Installing Pandokia
===================

Pandokia works on Unix/Linux and Macintosh machines.  The procedure is
the same in all cases.  There has been some effort toward Windows support,
but it is incomplete.

The sequence is to first install the software, then configure the
resulting system.

Initial Install
---------------

Download either the tar or zip file from
http://ssb.stsci.edu/testing/pandokia/

Extract the file:

::

    tar xf pandokia-1.2.tar.gz

::

    unzip pandokia-1.2.zip


Install the software:

::

    cd pandokia-1.2
    python setup.py install

If you want to install it somewhere other than the default python
site-packages, you can use regular setup.py options.  For example:

::

    cd pandokia-1.2
    python setup.py install --home $HOME/my_python

In case you chose a non-standard location for your install, the
setup.py will print example shell commands that you can use to set
up your environment.  If you did not, you can ignore that output.


Web Application
-----------------------------

To install the web application, you need to:

 - install the CGI

 - configure and initialize the database

The CGI
~~~~~~~~~~~~

You can install Pandokia in any web server that can run CGI scripts.
We use Apache for our normal usage.

When you run setup.py, one of the things it will say is something like:

::

    Get the CGI from  /Users/sienkiew/test_install/python/bin/pdk

Copy that file into the appropriate place in the DocumentRooot for
your web site, so that your web server can run it as a CGI.  If
your server allows symlinks (Options FollowSymLinks in Apache), you
can use a symlink:

::

    cd /var/www/html/cgi-bin
    ln -s /Users/sienkiew/test_install/python/bin/pdk pandokia.cgi

Otherwise, you can copy the file:

::

    cd /var/www/html/cgi-bin
    cp /Users/sienkiew/test_install/python/bin/pdk pandokia.cgi

This file is the only part of Pandokia that must be in the DocumentRoot
of the web server, but it requires the rest of Pandokia to be
installed on the system.  You cannot just copy *pdk* to another
machine.

Once you have done this, the pandokia application will be present
on your web server.  In the example above, the URL would be something
like http://www.example.com/cgi-bin/pandokia.cgi


The Development Web Server
............................

Pandokia comes with a mini development web server that you can use for testing.
You can run it from the *bin* directory where Pandokia commands
were installed.  For example, if the setup.py said:

::

    scripts went to /Users/sienkiew/mypython/python/bin

Then you could start the development web server with:

::

    cd /Users/sienkiew/mypython/python/bin
    cp pdk pdk.cgi
    pdk webserver

It will state the IP address and port number that it is listening
at.  Load that page and click on pdk.cgi.

We do not recommend using this web server for serious use, but it
is good enough for preliminary tests.


The Database
~~~~~~~~~~~~

Initializing the database : sqlite
...........................................

The advantages of Sqlite are:

    - It does not need a database server.

    - It is usually already built in to python.

    - It very easy to create a new database.

The disadvantage is:

    - It has very coarse write locking.  If you run a big transaction, other users may get timeout errors.

Sqlite3 support is normally built into Python.  You can look for it
by ::

    python
    import sqlite3

If there is no error, you already have sqlite support.  If
you do not have sqlite, you can re-compile python with sqlite support, or you
can install pysqlite from http://pypi.python.org/pypi/pysqlite/

Get the name of the Pandokia configuration file by entering the command:

::

    pdk config

Edit that file.  In the section marked "# Database: SQLITE", change
"if 0 :" to "if 1 :" and set the value of *db_arg* to the name of the
database file.

The database file and the directory that it is in must be writable to

  - the user that runs the CGI (e.g. "apache")
  - the database administrator
  - any user that imports data with "pdk import"

Apparently, some NFS servers still have buggy file locking, which
you can avoid by storing the data files locally.  

Create the database tables and indexes with the command:

::

    pdk sql sqlite.sql

Pandokia uses "pragma synchronous = normal;" for speed.  Certain
types of crashes can cause your database to be corrupted.  See
http://sqlite.org/pragma.html#pragma_synchronous for more information.
Pandokia does not have a configuration to change this, but you can
change the setting in pandokia/db_sqlite.py


Initializing the database : MySQL
...........................................

MySQL provides good performance.  The only significant disadvantage
is that you need to know (or find someone who knows) how to do MySQL
database administration.  This is mostly only an issue for the
initial setup.

To use MySQL, the machine hosting your web server will need the
MySQL client libraries and the MySQLdb python package.  You need
to have a machine running a MySQL database server, but it does not
need to be the same machine as your web server.

MySQL is available from http://www.mysql.com/

MySQLdb ( also known as "MySQL for Python") is available from
http://sourceforge.net/projects/mysql-python/ ; we are using version
1.2.3 at STScI.

Create the database and a database user for the pandokia application.
Pandokia needs a database user with the permissions USAGE, SELECT,
INSERT, UPDATE, DELETE, and CREATE TEMPORARY TABLES. 

Here is what SHOW GRANTS says for our pandokia user: ::

    GRANT USAGE ON *.* TO 'pandokia'@'%.stsci.edu' IDENTIFIED BY PASSWORD 'XXXXX'                       
    GRANT SELECT, INSERT, UPDATE, DELETE, CREATE TEMPORARY TABLES, SHOW VIEW ON `pandokia`.* TO 'pandokia'@'%.stsci.edu'

Get the name of the Pandokia configuration file by entering the command:

::

    pdk config

Edit that file.  In the section marked "# Database: MySQL", change
"if 0 :" to "if 1 :" and set the values in *db_arg* to the access
credentials.  *host* is the machine that runs the database server.
*user* is the user name to use to log into the database.  *passwd*
is the password to use to log in to the database, *db* is the name
of the database.

You can use the readpass() function to store the password in a file
or you can just write the password in the config file as a string
literal.

Create the database tables and indexes with the command:

::

    pdk sql mysql.sql


Initializing the database : Postgres
...........................................

Postgres provides good performance.  The only significant disadvantage
is that you need to know (or find someone who knows) how to do Postgres
database administration.  This is mostly only an issue for the
initial setup.

To use Postgres, the machine hosting your web server will need the
Postgres client libraries and the psycopg2 python package.  You
need to have a machine running a Postgres database server, but it
does not need to be the same machine as your web server.

Postgres is available from http://www.postgresql.org/

pyscopg2 is available from http://initd.org/psycopg/ or http://pypi.python.org/pypi/psycopg2

TODO: describe using postgres - this is roughly the same as MySQL.
See the comment at the bottom of pandokia/db_psycopg2.py for some
notes on using postgres .

::

    pdk sql postgres.sql



Machines that will run tests
----------------------------

On a machine that will only use Pandokia to run tests, you do not
need to make any configuration changes.  You may find it convenient
to install some supporting test frameworks.

None of this support software is required to install Pandokia.  You
can install Pandokia without any of this, then add it later.

 -  nose (Python) - http://readthedocs.org/docs/nose/

 -  py.test (Python) - http://pytest.org/

 -  unittest2 (Python) - http://pypi.python.org/pypi/unittest2

 -  fctx (C, C++) - http://fctx.wildbearsoftware.com/

    All necessary parts of fctx are included in pandokia, so it is not
    necessary to install anything to use fctx.

    Their web server has been down for a while.  You can find a
    copy of the fctx documentation at http://ssb.stsci.edu/testing/fctx/
    

 -  pyraf (IRAF) - http://www.stsci.edu/institute/software_hardware/pyraf 

    pyraf is used only to run IRAF tasks in the stsci_regtest runner.

 -  shunit2 (sh) - specially modified version from http://ssb.stsci.edu/testing/shunit2/

