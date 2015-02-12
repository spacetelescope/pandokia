.. index:: single: runners; shell (sh, bash, csh, etc)

===============================================================================
any - shell_runner - shell scripts or simple programs
===============================================================================

:abstract:

    ``shell_runner`` executes a shell script or simple program
    that contains a single test.  The exit status of the script
    is the test result.  For ``sh``, there are helper functions
    to compare files and report test attributes.

.. contents::

general
-------------------------------------------------------------------------------

With ``shell_runner``, each test file contains a single test.  The name
of the test is the name the test file with the extension removed.

The exit status of the script is the status of the test:

    - exit code 0 is Pass

    - exit code 1-127 is Fail

    - exit code 128-255 is Error (this range of exit codes is normally
      associated with a process that exits due to an un-trapped signal.)

The entire stdout and stderr of the script are captured and reported in
the test result.

There are examples in the source code in pandokia/sample_tests/shell

sh
-------------------------------------------------------------------------------

Special helper functions are available in sh, bash, and compatible shells:

        . pdk_shell_runner_helper

Your script can create an output file and compare it to a reference file.::

    init_okfile

    testfile cmp  $file
    testfile diff $file

    exit $teststatus

Your script can report attributes::

    bug: not implemented

csh
-------------------------------------------------------------------------------

In general, sh is a better scripting language than csh, but you can
write your test in csh if necessary.

There are examples in the source code in pandokia/sample_tests/shell


other shells
-------------------------------------------------------------------------------

Files that are executable are executed directly with ``./filename`` .
If you want something other than sh or csh, you can use #! to call out
a specific shell.


reporting attributes
-------------------------------------------------------------------------------

In ``sh``, there are helper functions described above that log test
attributes.

The environment variable PDK_LOG contains the name of the pandokia
log file.  Any test can append tda/tra values directly to the log file.

