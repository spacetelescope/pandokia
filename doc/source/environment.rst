.. index:: single: environment

Environment variables
---------------------

These environment variables are used by pandokia:

PDK_CONTEXT

   As input to pdkrun:  equivalent to --context

   As input to a runner: The name of the context to be reported for the
   tests to be run.

PDK_DIRECTORY

   As input to a runner:  The full path name of the current directory
   where the test is executing.

PDK_FILE

   As input to a runner: 
   The name of the file that contains tests to run in this process.  pandokia
   runners may use this to know which file to run tests from, though a runner
   may also be written to take the file name as a parameter.

PDK_LOG

   As input to pdkrun:  equivalent to --log

   As input to a runner: The name of the file to append PDK_LOG entries
   to.  This is how the test runner reports results to the rest of
   the system.

PDK_PARALLEL (input, output)

   As input to pdkrun:  equivalent to --parallel ; the number of
   concurrent test runners that may execute.

   As input to a runner:  The max number of concurrent test runners that
   may be executing.  Not particularly useful.

PDK_PROCESS_SLOT

   As input to a runner:  A small integer that uniquely identifies one
   of the concurrent test processes.  You can use this for unique temp
   file names.

PDK_PROJECT

   As input to pdkrun:  equivalent to --project

   As input to a runner: The name of the project to be reported for the
   tests to be run.

PDK_STATUSFILE

   As input to pdkrun or "pdk status":  Name of file to record currently
   executing processes.

PDK_TESTPREFIX

   As input to a runner:  This MUST be prepended to the local test names
   that the runner reports.  It contains the location in the hierarchy
   where the current test file is located.

PDK_TESTRUN

   As input to pdkrun:  equivalent to --test_run ; the name of the test
   run to report.

   As input to a runner: The name of the test_run to be reported for the
   tests to be run.

.. index:: single: timeout

PDK_TIMEOUT

   As input to pdkrun:  The number of wall clock seconds that a test
   runner may be allowed to run.  This time is per-file.  Processes
   that exceed this limit will be killed, first with SIGTERM and 10
   seconds later with SIGKILL if necessary.  Processes that survive
   SIGKILL for more than 10 seconds will be assumed to be wedged and
   ignored.

PDK_TMP

   Used internally to locate certain temp files.

   
