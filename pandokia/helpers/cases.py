"""Define TestCase classes from which test developers can inherit
to easily write tests."""

import unittest
import os
from pandokia.helpers import filecomp

class FileTestCase(unittest.TestCase):
    """This class pre-defines several methods:
        - setUp() defines self.tda and self.tra dictionaries
        - command() executes a shell command
        - check_file() compares a file to a reference file
        - tearDown() cleans up any compared files for tests that passed.

    Both the .command() and .check_file() methods automatically populate the
    tda and tra dictionaries with useful values."""

    def setUp(self):
        #Define the tda and tra dictionaries for use by the tests
        self.tda=dict()
        self.tra=dict()
        #Define some internal bookkeeping things with which to
        #manage housekeeping
        self._flist=[]
        self._ok_to_clean=False
        
    def tearDown(self):
        #Clean up any files we compared, but only if all comparisons
        #in the test have passed.
        if self._ok_to_clean:
            for fname in self._flist:
                os.unlink(fname)
            
    def command(self,cmdstring,suffix=''):
        """execute the specified command string, saving it as a
        tda and the return status as a tra.
        The 'suffix' argument allows users to distinguish between multiple
        commands issued as part of the same test.
        """
        
        self.tda['cmd%s'%str(suffix)]=cmdstring
        self.tra['cmd%s_retstat'%str(suffix)]=filecomp.command(cmdstring)

    def check_file(self, name, cmp, msg=None, suffix='', **kwargs):
        """Save the filename as a tda, and do the requested file
        comparison. Optional suffixes are provided in case the same
        test wants to compare multiple files.

        Only the name of the test file needs to be provided. The name
        of the reference file is always constructed as "ref/%s"%name.

        Some state management is performed in order to allow the tearDown
        method to clean up the compared files only if all files in the
        test have passed."""

        #Save the name
        self.tda['fname%s'%str(suffix)]=name
        #Mark state
        self._ok_to_clean=False
        #Do the comparison
        filecomp.check_file(name, cmp, msg, exc=True, **kwargs)

        #check_file will raise an exception if the test fails, so
        #it is safe to change state and add the file to the cleanup list
        #at this point
        self._flist.append(name)
        self._ok_to_clean=True


class FunctionHolder(unittest.TestCase):
    """Subclass from this case instead of writing test functions.

    Adding TDAs and TRAs to test functions can be done, but it is a little
    dangerous because the dictionaries are global variables.

    Instead, a developer can inherit from this test class, and write methods
    for it as if they were functions. This class pre-defines the tda and tra
    dictionaries in its setUp.

    """

    def setUp(self):
        self.tda=dict()
        self.tra=dict()
