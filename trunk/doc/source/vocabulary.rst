Appendix: Glossary
------------------

Meta-Runner: the program invoked when the "pdk run" command is
given. The meta-runner discovers tests, sets up the test environment,
and invokes the appropriate test runner(s) to run tests.

PDK Log: an ascii file containing a series of test results. See
file_format.rst.  

TDA: Test Definition Attribute. Test authors may define TDAs to
associate information about the test input or properties with the test
result.

TRA: Test Result Attribute. Test authors may define TRAs to associate
more detailed information about the test output than the simple
status.

Test result: a complete record describing the result of a test
containing all required fields. A test result is represented in
various ways: it is written in a log file (by a combination of default
and test-specific fields), and it is stored in the database. See
report_fields.rst. 

Test runner: a specific test runner, such as nose.

