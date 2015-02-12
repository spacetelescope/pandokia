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


** Since Pandokia is primarly developed for internal use, we are
** often working on some of the more peripheral features.  The
** fact that this is marked as a production quality release indicates
** that the core of the system has been shown to be fairly reliable.
** It does not indicate that every feature works well or that it is
** commercial quality software.


