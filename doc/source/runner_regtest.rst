.. index:: single: runners; STScI Regtests

===============================================================================
SPP - regtest - an STScI legacy system for IRAF packages
===============================================================================

Overview
-------------------------------------------------------------------------------

``regtest`` tests IRAF tasks.  It is derived from a legacy system,
and is still in use at STScI.  It is so specialized that it is
unlikely to be useful to you.

Test definitions
-------------------------------------------------------------------------------

Each test exists in a separate XML file.  The file format is defined in the
Pandokia source code in stsci_regtest/TEST_FORMAT.xml 

regtest automatically generates the data needed to make okifiable tests.

Test Execution
-------------------------------------------------------------------------------

This runner uses PyRAF to execute IRAF tasks.  Before executing the tasks
under test, it loads these IRAF packages::

    fitsio
    images
    stsdas
    tables

In the test definition, it lists one or more output files.  Each output file
is compared to a reference file.  If all match (within the parameters of the
comparison), the test passes.

