"""
a plugin for capturing test output from pytest
"""

# debugging


class tty:

    def write(self, s):
        pass
tty = tty()
# tty=open("/dev/tty","w")

###

import os
import time
import datetime
import sys
import re
import types
import os.path
import traceback
import platform
import signal

import pytest
# from _pytest import runner
# from _pytest import unittest
import _pytest

# I know this plugin doesn't work in pytest 2.1
if tuple(int(i) for i in pytest.__version__.split('.')) < (2, 2, 0):
    raise Exception(
        "The pytest plugin for Pandokia requires at least pytest 2.2.0")

# pycode contains an object that writes properly formatted pdk log records
import etc_utils.helpers.pycode

# basically a C struct


class data_item:
    pass

# contains various state information set by command line or whatever
state = {}

# flag for whether we should do anything at all.  we check this a lot.
enabled = False

##########


def pdktimestamp(tt):
    """Formats the time in the human readable format that pandokia accepts.
    Input is a timestamp from time.time()"""
    x = datetime.datetime.fromtimestamp(tt)
    ans = "%s.%03d" % (x.strftime("%Y-%m-%d %H:%M:%S"),
                       (x.microsecond / 1000))
    return ans

##########


def cleanname(name):
    """Removes any object id strings from the test name. These
    can occur in the case of a generated test."""
    pat = re.compile(r".at.0x\w*>")
    newname = re.sub(pat, '>', name)
    return newname

##########
# This callback happens before the command line options are parsed.


def pytest_addoption(parser):
    env = os.environ
    group = parser.getgroup("pandokia", "Pandokia options")
    group.addoption(
        "--pdk", action="store_true", dest="pdk_enabled",
        default=env.get('PDK', False),
        help="Enable the Pandokia plugin (this will generate a PDK-compatible log file)")
    group.addoption(
        "--pdklog", action="store", dest="pdklog",
        default=env.get('PDK_LOG', None),
        help="Path for PDK-compatible log file [PDK_LOG]")
    group.addoption(
        "--pdkproject", action="store", dest="pdkproject",
        default=env.get("PDK_PROJECT", "default"),
        help="Project name to write to PDK-compatible log file [PDK_PROJECT]")
    group.addoption(
        "--pdktestrun", action="store", dest="pdktestrun",
        default=env.get("PDK_TESTRUN", time.asctime()),
        help="Test run name to write to PDK-compatible log file [PDK_TESTRUN]")
    group.addoption(
        "--pdktestprefix", action="store", dest="pdktestprefix",
        default=env.get("PDK_TESTPREFIX", ''),
        help="Prefix to attach to test names in PDK-compatible log file [PDK_TESTPREFIX]")
    group.addoption(
        "--pdkcontext", action="store", dest="pdkcontext",
        default=env.get("PDK_CONTEXT", "default"),
        help="Context name to write to PDK-compatible log file [PDK_CONTEXT]")

##########
#
# This callback initializes the plugin.  It happens before any tests are
# executed.


def pytest_configure(config):
    global enabled
    if config.getvalue('pdk_enabled') or ('PDK_LOG' in os.environ):
        enabled = True

        # We use our own output capture in place of the default capture
        # manager.  See the comment near the CaptureManager class below.

        # If capturemanager is not registered, we may be pretty messed up - is this a problem?
        # assert config.pluginmanager.isregistered( None, 'capturemanager' )

        # Kick out pytest's capture manager.
        config.pluginmanager.unregister(None, 'capturemanager')

        # Collect the regular set of pandokia parameters, complete with
        # defaults.
        if config.getvalue('pdklog') is not None:
            state['pdklogfile'] = config.getvalue('pdklog')
        else:
            state['pdklogfile'] = os.path.join(
                os.path.abspath(os.path.curdir), 'PDK_DEFAULT.LOG')

        state['pdkproject'] = config.getvalue('pdkproject').replace(' ', '-')
        state['pdktestrun'] = config.getvalue('pdktestrun').replace(' ', '-')
        state['pdktestprefix'] = config.getvalue('pdktestprefix')
        state['pdkcontext'] = config.getvalue('pdkcontext').replace(' ', '-')

        hostname = platform.node()
        if '.' in hostname:
            hostname = hostname.split('.', 1)[0]

        # Open the log file.
        try:
            sd = 'PDK_FILE' not in os.environ
            state['report'] = etc_utils.helpers.pycode.reporter(
                source_file=None,
                setdefault=sd,
                filename=state['pdklogfile'],
                test_run=state['pdktestrun'],
                project=state['pdkproject'],
                host=hostname,
                context=state['pdkcontext'],

                # this is wrong for location, but it is less wrong than nothing
                # at all
                location=None,
                test_runner='pytest',
                test_prefix='')

        except IOError as e:
            sys.stderr.write(
                "Error opening log file %s: %s\n" %
                (state['pdklogfile'], e.strerror))
            sys.stderr.write("***No Logging Performed***\n")
            return
    else:
        # If the user did not ask for our plugin, remember to not do anything
        # much.
        enabled = False

##########
#

# current_timeout is a global used by the signal handler;  we store
# the timeout duration here so that the exception can say how long the
# timeout was
current_timeout = None

# an exception to raise when a test takes too long


class TimeoutError:
    '''An exception for this plugin to use internally for timeouts.

    This is an old-style class so that user code can't catch it with
        except Exception, e:
            ...
    '''

    def __init__(self, timeout):
        self.timeout = timeout

    def __str__(self):
        return "time out after %s seconds" % self.timeout

# A signal handler for the alarm.  Remove the signal handler and raise
# the exception to indicate a timeout.


def timeout_expired_callback(signum, stk):
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    raise TimeoutError(current_timeout)

##########
# before each test setup (?)
# before makereport setup
#

try:
    import stsci.tools.tester

    def in_tester():
        tty.write(
            "USING TESTER %s\n" %
            stsci.tools.tester.pytools_tester_active)
        return stsci.tools.tester.pytools_tester_active
except ImportError:
    def in_tester():
        tty.write("NOT USING TESTER\n")
        return False

cached_trimmed_dirs = {}


def trim_filename(name):
    org_name = name
    l = []
    tty.write("trim_filename %s\n" % name)
    while len(name) > 0:
        d, f = os.path.split(name)
        l.append(f)
        tty.write("trim_filename step %s %s\n" % (d, f))
        name = d

    try:
        n = l.index('tests')
    except ValueError:
        return org_name

    if n >= 0:
        l = l[0:n]

    l.reverse()
    tty.write("ARF: %s\n" % l)
    return os.path.join(*l)


def pytest_runtest_setup(item):
    if not enabled:
        return

    # a pandokia-specific place to store our data
    item.pandokia = data_item()

    tty.write("runtest_setup\n")

    # compute the name of this test, save it for when we need it:

    # the name of the test is the name of the file the test is in ...
    filename = item.location[0]
    if filename.endswith('.py'):
        filename = filename[:-3]

    if in_tester():
        tty.write("IN TESTER\n")
        # we are NOT running in the context of pdkrun, so the file
        # name may contain various kinds of junk that we want to
        # exclude.
        try:
            filename = trim_filename(filename)
        except Exception as e:
            tty.write("EXCEPTION " + str(e) + "\n")
    else:
        tty.write("NOT IN TESTER\n")

    tty.write("HERE\n\n\n")

    # + the name of the class/method/function/whatever
    name = filename + '/' + cleanname(item.location[2])
    tty.write("NAME: %s\n      %s\n" % (filename, name))

    # + whatever prefix was handed in to us by pdkrun
    if state['pdktestprefix'] != '':
        if not state['pdktestprefix'].endswith('/'):
            name = '%s/%s' % (state['pdktestprefix'], name)
        else:
            name = '%s%s' % (state['pdktestprefix'], name)

    # remember the name for later
    item.pandokia.name = name

    # grab the stdout/stderr
    etc_utils.helpers.pycode.snarf_stdout()
    item.pandokia.start_time = time.time()

    # set up a timeout, if necessary )
    if 'timeout' in item.keywords:
        item.pandokia.timeout = int(item.keywords['timeout'].args[0])
    else:
        # may someday implement a default
        item.pandokia.timeout = None

    if item.pandokia.timeout:
        if sys.platform != 'win32':
            # I need to have timeout_expired_callback be the same function
            # all the time (so we can recognize it), but I need it to know
            # information to show in the exception.  Since it is called
            # by the signal callback, the only way to get the information
            # to it is a global variable.
            global current_timeout
            current_timeout = item.pandokia.timeout

            # set the signal handler
            prev = signal.signal(signal.SIGALRM, timeout_expired_callback)
            if prev != signal.SIG_DFL:
                # if somebody else installed a handler for SIGALRM,
                # then we broke it.  This test cannot work reliably with
                # a timeout.
                signal.signal(signal.SIGALRM, signal.SIG_DFL)
                raise Exception(
                    'Timeout declared but somebody already '
                    'installed a signal handler for SIGLARM (%s)' %
                    prev)

            # set the alarm
            signal.alarm(item.pandokia.timeout)
        else:
            print("Warning: Test timeouts not implemented on Windows")

    # done pytest_runtest_setup


##########

def find_txa(test):
    """Find the TDA and TRA dictionaries, which will be in different
    places depending on what kind of a test this is.
    """
    if isinstance(test, pytest.Function):
        if isinstance(test.obj, types.MethodType):
            # I wonder what this is about?
            try:
                tda = test.obj.__self__.tda
            except AttributeError:
                tda = dict()

            try:
                tra = test.obj.__self__.tra
            except AttributeError:
                tra = dict()

        elif isinstance(test.obj, types.FunctionType):
            # if the test is just a function, it is in the global
            # namespace of the module that the function is defined in.
            try:
                tda = test.obj.__globals__['tda']
            except KeyError:
                tda = dict()

            try:
                tra = test.obj.__globals__['tra']
            except KeyError:
                tra = dict()

    elif isinstance(test, _pytest.unittest.UnitTestCase):
        # if the test is in a class, the tda/tra dicts are attributes of that
        # class
        try:
            tda = test.tda
        except AttributeError:
            tda = dict()
        try:
            tra = test.tra
        except AttributeError:
            tra = dict()

    elif isinstance(test, _pytest.doctest.DoctestModule):
        # A doctest cannot have attributes.
        tda = {}
        tra = {}

    else:
        # If there is any unrecognized type of test, then the plugin
        # does not know how to deal with it.
        tda = dict()
        tra = {'warning': 'Unknown test type: tda/tra not found'}

        # I'm making it an error to not recognize the test type; comment
        # out this line if that is a problem.
        raise TypeError("Unknown test type, %s" % type(test.test))

    return tda, tra

##########
# make available a funcarg:  A function parameter named pdk_test_name
# will contain the name that Pandokia knows this test by.


@pytest.fixture
def pdk_test_name(request):
    if not enabled:
        return None
    tty.write("FUNCARG TEST NAME ")
    return request._pyfuncitem.pandokia.name

##########
#
# called at various times in the execution of a single test
#

# Bugfix: __multicall__ is deprecated, and removed in pytest 7.x
# Solution courtesy of
# https://mail.python.org/pipermail/pytest-dev/2015-September/003158.html
# and https://docs.pytest.org/en/7.1.x/how-to/writing_hook_functions.html
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport( item, call):
    tty.write("runtest_makereport when=%s\n" % call.when)

    # get the report output from the thing we're wrapping
    outcome = yield
    report = outcome.get_result()

    # if not --pdk, skip all the rest
    if not enabled:
        tty.write("NOT ENABLED\n")
        return report

    # we are called 3 times for each test, with different data available
    # at each invocation.  This if statement lists those times in order.

    if call.when == 'setup':
        # default to no exception (we may detect one shortly)
        item.pandokia.exception = None

        # if we don't make it to the 'call' when, there was an
        # error in the setup.  Make an empty record that gets us
        # through the report.
        item.pandokia.status = None
        item.pandokia.tda = {}
        item.pandokia.tra = {}

    elif call.when == 'call':
        # this is called after the test function was called:

        # pick up attributes
        item.pandokia.tda, item.pandokia.tra = find_txa(item)

        # convert the pyetc status to a pandokia status
        if report.outcome == 'passed':
            item.pandokia.status = 'P'
        elif report.outcome == 'skipped':
            item.pandokia.status = 'D'
        else:
            if not isinstance(call.excinfo, pytest.ExceptionInfo):
                item.pandokia.status = 'E'
            else:
                if call.excinfo.errisinstance(AssertionError):
                    item.pandokia.status = 'F'
                else:
                    item.pandokia.status = 'E'
                    item.pandokia.tra['exception'] = call.excinfo.exconly()
            item.pandokia.exception = 'EXCEPTION:\n%s\n' % str(report.longrepr)

        # all that material is saved in item.pandokia, which will be
        # available when we get called with call.when == 'teardown'

    elif call.when == 'teardown':

        # after the test and the teardown function are finished running:

        # If there is an exception in the test setup, when='call'
        # never happens.  This part dances around that issue.

        # no status implies not pass/skipped/fail, leaving E
        if item.pandokia.status is None:
            item.pandokia.status = 'E'

        # if pytest tells us an exception code for the teardown
        # and we do not already have one from earlier, save it up
        if isinstance(call.excinfo, pytest.ExceptionInfo):
            item.pandokia.status = 'E'
            if item.pandokia.exception is None:
                item.pandokia.tra['exception'] = call.excinfo.exconly()
                item.pandokia.exception = 'EXCEPTION:\n%s\n' % str(
                    report.longrepr)

        # shut off the timeout
        more_log = ''

        tty.write("TEARDOWN BEFORE TIMEOUT\n")

        if hasattr(item.pandokia, 'timeout') and item.pandokia.timeout:
            tty.write("CLEAR ALARM FOR TIMEOUT\n")
            signal.alarm(0)
            signal_handler = signal.signal(signal.SIGALRM, signal.SIG_DFL)
            if signal_handler != timeout_expired_callback:
                item.pandokia.status = 'E'
                more_log = ('\nERROR: This function had a timeout, but '
                            'something changed the SIGALRM handler (to %s)' %
                            (str(signal_handler))
                            )
        else:
            tty.write("NO TIMEOUT TO CLEAR\n")

        # Now we are finally finished; note the time.
        item.pandokia.end_time = time.time()

        # pick up the logged stdout
        log = etc_utils.helpers.pycode.end_snarf_stdout()

        # add any exception report to the stdout log
        if item.pandokia.exception:
            log += item.pandokia.exception

        # add any errors detected in this function
        if more_log:
            log += more_log

        # write the PDK_LOG record
        if '[doctest]' in item.pandokia.name:
            item.pandokia.name = 'BUG-TEST NAME WITH BRACKETS'

        state['report'].report(
            test_name=item.pandokia.name,
            status=item.pandokia.status,
            start_time=pdktimestamp(item.pandokia.start_time),
            end_time=pdktimestamp(item.pandokia.end_time),
            tda=item.pandokia.tda,
            tra=item.pandokia.tra,
            log=log,
        )

    else:
        # if there is some other time we are called, have an error --
        # pytest is no longer implementing the interface that we expect,
        # so we have to fix this code.
        raise Exception(
            'pandokia plugin does not expect call.when = %s' % str(
                call.when))

    # always return the report object
    return report


# pytest comes with a capture manager, but it does not reliably contain
# the captured stdout.  (I think this is because it offers destructive
# reads.)  Since I can't get the stdout/stderr that I want, I evict
# the default capture manager completely and inject this one as my own.
#
# I expect this breaks anybody who expects capsys/capfd to work as
# documented, at least until I figure out what is supposed to be going on
# with all that.

# This object implements the same hooks as the default capture manager.
class CaptureManager(object):

    def __init__(self, method='default'):
        # not implementing parameter "method" right now
        pass

# bug: somewhere in here, you have to call the function that shows all the
# funcargs values to stdout

    @pytest.mark.tryfirst
    def pytest_runtest_setup(self, item):
        pass

    @pytest.mark.tryfirst
    def pytest_runtest_call(self, item):
        pass

    @pytest.mark.tryfirst
    def pytest_runtest_teardown(self, item):
        pass

    def pytest_keyboard_interrupt(self, excinfo):
        # bug: ???
        return
        if hasattr(self, '_capturing'):
            self.suspendcapture()

    @pytest.mark.tryfirst
    def pytest_runtest_makereport(self, __multicall__, item, call):
        rep = __multicall__.execute()
        return rep
