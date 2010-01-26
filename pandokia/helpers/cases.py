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

    Both the .command() and .check_file() methods automatically populate the
    tda and tra dictionaries with useful values.

    Test cases may support "okifying" if the subclass:
      - saves self.tda['_okfile']=some absolute file name
      - opens that file name, and passes the handle to the check_file method

    This will write the names of files that did not pass the comparison to
    the okfile, which Pandokia then knows how to use to "okify".
    """

    def setUp(self):
        #Define the tda and tra dictionaries for use by the tests
        self.tda=dict()
        self.tra=dict()

            
    def command(self,cmdstring,suffix=''):
        """execute the specified command string, saving it as a
        tda and the return status as a tra.
        The 'suffix' argument allows users to distinguish between multiple
        commands issued as part of the same test.
        """
        
        self.tda['cmd%s'%str(suffix)]=cmdstring
        self.tra['cmd%s_retstat'%str(suffix)]=filecomp.command(cmdstring)


    def check_file(self, name, cmp, okfh=None, msg=None, suffix='', **kwargs):
        """Save the filename as a tda, and do the requested file
        comparison. Optional suffixes are provided in case the same
        test wants to compare multiple files.

        Only the name of the test file needs to be provided. The name
        of the reference file is always constructed as "ref/%s"%name.

        Some state management is performed in order to allow the tearDown
        method to clean up the compared files only if all files in the
        test have passed."""

        #Save what we're comparing
        self.tda['fname%s'%str(suffix)]=name
        #Do the comparison
        filecomp.check_file(name, cmp=cmp, msg=msg, exc=True,
                            cleanup=True, okfh=okfh,
                            **kwargs)



class FunctionHolder(unittest.TestCase):
    """Subclass from this case instead of writing test functions.

    Adding TDAs and TRAs to test functions can be done, but it is a little
    dangerous because the dictionaries are global variables.

    Instead, a developer can inherit from this test class, and write methods
    for it as if they were functions. This class pre-defines the tda and tra
    dictionaries in its setUp, which will be run before each test function.

    """

    def setUp(self):
        self.tda=dict()
        self.tra=dict()
