TODO: 

What are the contents of a test result?
---------------------------------------

There is one test_result each time we run a specific test.
The fields can be categorized as follows

    Type: This set of fields identifies a type of test::
        project
        test_runner
        test_name

    Identity: this set of fields identifies a single test_result record::
        test_run
        host
        context
        project
        test_name

    Required: This set of fields is required::
        test_run
        project
        test_name
        status

    Optional: All other recognized fields::
       location     (of the test file)
       test_runner  (used to run the test)
       log          (stdout/stderr logs)
       start_time
       end_time
       tda_*
       tra_* 

An unrecognized field will not cause an error, but will not be
imported into the database.


What are the meanings of the fields in a report record?
-------------------------------------------------------

( test_run, project, host, context, test_name ) identify the specific
instance of a test result.

- test_run identifies a specific instance of running the test.  If
  you run a test suite more than once, you need some way to distinguish
  which run a result came from.  Each time you run it, you report
  it as a different test_run.  Normally, you would find the same
  test name with many different host/context values, indicating that
  you ran the same test in many environments.

  The reporting system displays the name of the test_run that a result
  came from.  It can also compare the results of multiple test runs.
  e.g. This test failed today, but it passed yesterday.

- project is an arbitrary way of grouping tests.  The authors have
  many separate projects that are tested each night as part of
  our continuous integration.  In the morning, we look at a single
  report that provides a summary of the results from all the
  projects.

- host identifies the machine where this test ran.

- context identifies some specific configuration.  For example, if
  we run the same test in two different versions of python, we use
  a different context to report each.  The context can identify
  versions of interpreters or shared libraries, cpu type, available
  memory -- it means whatever you want it to mean.  You say the
  name of the context when you run the test, and you read the name
  of the context in the reports.

- test_name identifies the test.  A test name is unique within a
  project.  The test name is the same every day and in every execution
  environment, so that you can compare results from day to day or
  across environments.

These fields uniquely identify a test result.  It is an error to
report the same result again, but if you run the test again, the
test is part of a different test_run so you have a different test
result.

Other than the identity, there is only one required field:

- status tells us what happened with the test
    P = passed
        the test observed whatever it expected
    F = fail
        we ran the test, but it failed
    E = error
        For some reason, we could not complete the test.
        We distinguish this from Fail because an error
        may indicate a problem with the test, not a problem
        with the software being tested.
    D = disabled
        We asked not to run the test.  We report this
        so that the test is not Missing.
    M = missing
        We did not receive a report, but expected one.
        You don't normally report Missing in a test result
        file, but this condition can be detected later in
        the database.

There are various optional fields:

- test_runner tells us which software ran the test.  Since we can 
  accept reports from many test systems, this tells us which one
  produced this result.

- start_time
- end_time
  The cumulative run time of some of our test suites is many hours.
  It helps to know when a particular test ran.

  Two formats are supported for these timestamps::

    - time_t (seconds since 1970)
      may be floating point for fractions of a second

    - YYYY-MM-DD HH:MM:SS.sss
      The output from 
         date '+%Y-%m-%d %H:%M:%S'
      matches this format.  All times in this format are assumed
      to be local time.

- location is information for a developer who has to diagnose
  a problem with a test.  Since we have 5 projects spread over 8 
  test environments, and a total of nearly 5000 tests, it is helpful
  for the report to display the location of the one you are looking at.
  The location is normally the fully qualified file name of the test.

- log is the stdout/stderr from a test.  If the test fails, it helps
  to see what it said.

- tda_*
  tra_*

  TDA/TRA (test definition/result attributes) are further information
  that the test explicitly reports.  The test author can make up names
  for as many TDA or TRA fields as they want. The names will be
  converted to lower case on import to the database.

  The meaning of a TDA or TRA field is only defined for a specific
  test, though as test author you are free to use the same meanings
  for a group of tests.  It is information for the developer to
  analyze what was happening.  An attribute may be useful even for a
  test that passed, if it tells you something about how/why/how-well
  it passed.

