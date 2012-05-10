Appendix: Importing Demo Data
==============================


TODO: THIS CHAPTER IS PROBABLY OUT OF DATE


After you have installed Pandokia on your system, you can follow this
procedure to import the provided demo data into your database.

About the demo data
-------------------

In the sample_data directory, you will find a series of pdk log files
with various names. These files were created by:

- running a set of tests, which we designated as test run demo_1, on a
  computer named banana


      pdkrun --parallel 4 --project sample --test_run=demo_1 --log sample_data/demo_1.banana -r tests

- running the same test run on a computer named justine

      pdkrun --parallel 4 --project sample --test_run=demo_1 --log sample_data/demo_1.justine -r tests


- running the same set of tests, but designated as test run demo_2, on
  banana

      pdkrun --parallel 4 --project sample --test_run=demo_2 --log sample_data/demo_2.banana -r tests

These are both four-processor machines, so we ran the tests in 4
parallel processes to make best use of the hardware, and each process
produced its own pdk log file, with a distinguishing numerical
suffix. We designated this the "sample" project for convenience. 


Importing the demo data
-----------------------

All the data can be imported with one command::

     cd sample_data
     pdk import *

or you can import them one test run at a time::

     pdk import demo_1.*
     pdk import demo_2.*

The importer prints some diagnostic information to stdout as it
processes each file.


Browsing the demo data
----------------------

Point your browser at the top level pandokia webpage (if you followed
the instructions in INSTALL/"Using the pandokia test web server", then
this will be URL localhost:7070/pdk.cgi)

At this point you can navigate from the top level to the test run and
host that you're interested in. The figure (report_flow.png,
report_flow_caption.png) illustrates the possible navigation paths.

In this case, we'll start by clicking in the "Lists of Test Runs" on
"All". Both demo test runs show up, with several active links:

  - if you click on the name of the test run, you get a tabular view

    Here the tests are grouped by host and status. Clicking on any
    of the links will take you to a page showing only those tests that
    satisfy the relevant conditions.

  - clicking on "T" gives you the treewalker view
    
    Here the tests are grouped by status and the first element of the
    hierarchical test name. One can click on any of the links in the
    table which will again take you to a page showing only those tests
    that satisfy the relevant conditions, or use one of the "narrow to"
    choices to further narrow by host or project.

  - clicking on "P" gives you a summary of only the problem cases
    (status = error or fail)
 
    This is a summary view, pre-selected to show only
    the tests with an error or failing status. From here you can
    click on an individual test name to see its test result; or
    "detail of all" down at the bottom to see them all on one page.

    From a summary view, you can compare to another test run by typing
    its name into the box and clicking "compare". This will show the
    status of each test from the "other" run (ie, the one whose name
    you typed in) next to the status from this run. You can also click
    "different", which will show only the tests whose status changed
    between the two runs (none in this case), or "same" for the
    complementary set.

    You can also "add attributes" to a summary view. This will expand
    the table to include one column for every TDA or TRA that was
    defined by any of the tests in the set. (Thus, it may be a sparse
    table, if the tests defined different attributes.) That's not very
    interesting in the demo test set, but for real tests, it might
    provide useful clues about what failing tests had in common, or
    further detail about how badly a test failed.

