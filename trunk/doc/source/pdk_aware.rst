Using Pandokia with Existing Tests
==================================


Step One: Just use it
---------------------

If you already have existing python tests that can be recognized and
run by nose, then you can take advantage of Pandokia's reporting
features as soon as you have installed and configured it.

Place a file named pandokia_top at the top of your test tree, and then
issue the command::

   pdk run -r <dirname>

This will recursively search through the directory, discovering tests
and running them with nose, and using the included nose plugin to
write the test results to a log file. Default values for the project
(taken from the current directory) and log file (taken from the
user and timestamp) will be used, and printed to stdout. Then::

   pdk import <logfilename>

will import the results into the Pandokia database, and then you can
use the browsable report generator to examine your reports.


Step Two: Environment, notification, and disabling
--------------------------------------------------

To take advantage of more of Pandokia's features, add some special
files to your test tree.

.. index: single: environment variables

Customizing the environment
...........................

A file named pdk_environment can be placed in test directories
to define the environment in which your tests will run.

A [default] section defines environment variables applicable to all
test environments, and optional named [osver], [mach], and [hostname]
sections can customize the environment to be used when the tests
are run on different machines. These customizations will override
the values in the default section.

For example, suppose Arthur has a set of tests that require a resource
that is located in different places on different machines. Then his
pdk_environment file would look something like this::

   [default]
   PDK_PROJECT = odyssey
   monolith = black
   doors = $podbay/doors/open.com

   [hostname=hal]
   podbay = /data/discovery/podbay

   [hostname=mycroft]
   podbay = /usr/local/moonbase/podbay


Now the tests that run on *hal* will run in an environment that
includes the variables::

  PDK_PROJECT = odyssey
  monolith = black
  podbay = /data/discovery/podbay
  doors = /data/discovery/podbay/doors/open.com

while the tests that run on *mycroft* will run in an environment that
includes the variables::

  PDK_PROJECT = odyssey
  monolith = black
  podbay = /usr/local/moonbase/podbay
  doors = /usr/local/moonbase/podbay/doors/open.com


Note that the default section may refer to variables defined in the
custom sections.

Environment files are applied hierarchically. Suppose Arthur has a
test directory tree laid out like this::

  odyssey
      earth
      moon
      jupiter

Arthur can place the file described above in the odyssey
directory, and its values will apply to all tests in the tree. But he
can place an additional pdk_environment file in odyssey/jupiter
that contains only the following::

  [default]
  doors=$podbay/doors/closed.com

and this value will override the value of $doors for tests in the
jupiter directory only (and any subdirectories it may have).

.. index:: running tests; disabling tests

Disabling tests
...............

The presence of a file named sometest.disable will prevent a
corresponding sometest.py file in the same directory from being
examined for tests. This can be useful to disable chronically failing
tests (although this feature should be used with caution!), or in
test-driven development mode, to disable tests that you know will
fail because you haven't fixed the bug or written the code for them
yet.

You can also disable a test for just one context by creating a \*.CONTEXT.disable file.  For example, if you want to disable a test named foo *only* in the orange context, then you would create a file named foo.orange.disable in the same directory as foo.

.. index:: running tests; enabling tests

Enabling tests
...............

Support for enable files was added to compliment the disable functionality.  The presense of an enable file supercedes any disable files for a particular test.  The enable files work just like disable files: for some test foo, you can have foo.enable which means that it *always* runs, or you can have foo.whatever.enable, which means that foo only runs when $PDK_CONTEXT has the value of "whatever".  If foo.enable or foo.*.enable exists, all foo.disable and foo.*.disable files are ignored by Pandokia.

.. index:: single: email

Email notifications
...................

You can use Pandokia to send customized email notifications of failed,
error, or disabled tests. A special file named pdk_contacts can be
placed in each test directory. This file should contain the usernames
or email addresses, one per line, of people who should be notified
when tests in this directory fail.

The contact files are applied hierarchically but cumulatively. For
example, consider the following directory layout with pdk_contacts
files populated as follows::

   film/pdk_contacts: stanley
      odyssey/pdk_contacts: arthur
         earth
         moon
         jupiter/pdk_contacts: hal
      clockwork/pdk_contacts: anthony


Then Stanley will receive an email containing information about all
failed tests; Arthur will receive email containing information about
the odyssey project, including all of its subprojects, and Anthony
will receive email about only the clockwork project. Hal will receive
mail only about the jupiter subproject of odyssey.


Unlike the previous two features, you will have to issue a couple of
commands in order to update the contact fields in the database.  On
the test machine, run::

  pdk_gen_contact projectname /directory/name > contact_list.txt

will construct a table of contact information from the contact files
in your test tree.  "projectname" is the name of the project that
you are processing and /directory/name is the path to the root of
a test tree.  (That is the directory that has the file pandokia_top
in it.)

The assumption is that the project contains the same set of tests
on all machines, so it is only necessary (or even useful) to run
pdk_gen_contact on a single machine.

(b.t.w. pdk_gen_contact is a hack; it will be replaced by "pdk
gen_contact" in a future release.)

On the server machine,

::

  pdk import_contact < contact_list.txt

will update the database with that information, so it will be
available when you run::

  pdk notify

after importing the results of a test run.

The contact names are also shown in the summary report available in the
browsable report, which can be useful information for a release
manager or someone assigning help desk calls.

.. index: running tests; attributes

Step 3: Add attributes to your tests
------------------------------------

Pandokia can collect and report additional information about your
tests through the population of test attributes.

Test definition attributes (TDAs) are typically populated by values
that are known when the test is being written. It can be used to
record input parameters, reference values, thresholds, or descriptive
information about the test that would be useful to have when analyzing
failures.

Test result attributes (TRAs) can be used to record more detailed
results than a simple pass/fail status, such as computed values and
discrepancies. They are typically populated by values that are
computed during the execution of the test.

Making use of test attributes requires modifying your tests. For
tests that inherit from unittest.TestCase, you can add::

   self.tda=dict()
   self.tra=dict()

to the setUp() method of your test class; then populate the
dictionaries as desired.

For test functions, declare the dictionaries as global variables
in your function, then populate them (but do not redefine them) in
your tests::

   tda=dict()
   tra=dict()

   def test1():
       tda['year']=2001

The Pandokia plugin will take care of clearing the dictionary contents
between tests to avoid cross-test contamination.

Additional examples of how to add attributes to your test cases and
functions can be seen in example_test_case.py and example_test_function.py


Step 4: Use helper functions to write new tests
-----------------------------------------------

Pandokia provides some helper classes and functions to facilitate
writing some kinds of tests.

File comparisons
................

The file doc/example_filetest.py contains examples of how to subclass
from and use the FileTestCase class in your own tests.  This class
pre-defines several methods:

        - command() executes a shell command
        - check_file() compares a file to a reference file
        - tearDown() cleans up any compared files for tests that passed.

Both the .command() and .check_file() methods automatically populate the
tda and tra dictionaries with useful values.

These methods use the helper functions in helpers/filecompare.py,
which can also be called independently.

Functions with attributes
.........................

Adding TDAs and TRAs to test functions can be done by implementing the
dictionaries as global variables. (See example_testfunction.py for an example)

Alternatively, a developer can inherit from the FunctionHolder, and write methods
for it as if they were functions. This class pre-defines the tda and tra
dictionaries in its setUp.



ok-ify tests
-------------

section here about the TDA _okfile and what to put in an okfile

