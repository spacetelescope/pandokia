"""
Adds a plugin for capturing test output from py.test
"""

import os, time, datetime, sys, re, types

import py.test
import pytest
from _pytest import runner
from _pytest import unittest

from StringIO import StringIO as p_StringO    #for stdout capturing
from cStringIO import OutputType as c_StringO
import traceback
import platform

# pycode contains an object that writes properly formatted pdk log records
import pandokia.helpers.pycode

state = {}

def pdktimestamp(tt):
    """Formats the time in the format PDK wants.
    Input is a timestamp from time.time()"""
    x=datetime.datetime.fromtimestamp(tt)
    ans="%s.%03d"%(x.strftime("%Y-%m-%d %H:%M:%S"),
                   (x.microsecond/1000))
    return ans

def cleanname(name):
    """Removes any object id strings from the test name. These
    can occur in the case of a generated test."""
    pat=re.compile(".at.0x\w*>")
    newname=re.sub(pat,'>',name)
    return newname

def pytest_addoption(parser):
    env = os.environ
    group = parser.getgroup("pandokia", "Pandokia options")
    group.addoption(
        "--pdk", action="store_true", dest="pdk_enabled",
        default=env.get('PDK', False),
        help="Generate PDK-compatible log file")
    group.addoption(
        "--pdklog",action="store",dest="pdklog",
        default=env.get('PDK_LOG',None),
        help="Path for PDK-compatible log file [PDK_LOG]")
    group.addoption(
        "--pdkproject",action="store",dest="pdkproject",
        default=env.get("PDK_PROJECT","default"),
        help="Project name to write to PDK-compatible log file [PDK_PROJECT]")
    group.addoption(
        "--pdktestrun",action="store",dest="pdktestrun",
        default=env.get("PDK_TESTRUN",time.asctime()),
        help="Test run name to write to PDK-compatible log file [PDK_TESTRUN]")
    group.addoption(
        "--pdktestprefix",action="store",dest="pdktestprefix",
        default=env.get("PDK_TESTPREFIX",''),
        help="Prefix to attach to test names in PDK-compatible log file [PDK_TESTPREFIX]")
    group.addoption(
        "--pdkcontext",action="store",dest="pdkcontext",
        default=env.get("PDK_CONTEXT","default"),
        help="Context name to write to PDK-compatible log file [PDK_CONTEXT]")

# Called before any tests are run
def pytest_configure(config):
    if config.getvalue('pdk_enabled'):
        state['enabled'] = True

        if config.getvalue('pdklog') is not None:
            state['pdklogfile'] = config.getvalue('pdklog')
        else:
            state['pdklogfile'] = os.path.join(os.path.abspath(os.path.curdir), 'PDK_DEFAULT.LOG')

        state['pdkproject'] = config.getvalue('pdkproject').replace(' ', '-')
        state['pdktestrun'] = config.getvalue('pdktestrun').replace(' ', '-')
        state['pdktestprefix'] = config.getvalue('pdktestprefix')
        state['pdkcontext'] = config.getvalue('pdkcontext').replace(' ', '-')

        hostname = platform.node()
        if '.' in hostname:
            hostname = hostname.split('.', 1)[0]

        try:
            sd = not 'PDK_FILE' in os.environ
            state['report'] = pandokia.helpers.pycode.reporter(
                source_file = None,
                setdefault = sd,
                filename = state['pdklogfile'],
                test_run = state['pdktestrun'],
                project = state['pdkproject'],
                host = hostname,
                context = state['pdkcontext'],

                # this is wrong for location, but it is less wrong than nothing at all
                location = os.path.abspath(os.path.curdir),
                test_runner = 'pytest',
                test_prefix = '')
        except IOError as e:
            sys.stderr.write("Error opening log file %s: %s\n"%(fname,e.strerror))
            sys.stderr.write("***No Logging Performed***\n")
            return
    else:
        state['enabled'] = False

def pytest_runtest_call(item):
    if state['enabled']:
        item.start_time = time.time()
    item.runtest()

def find_txa(test):
    """Find the TDA and TRA dictionaries, which will be in different
    places depending on what kind of a test this is.
    """
    if isinstance(test, py.test.Function):
        if isinstance(test.obj, types.MethodType):
            try:
                tda = test.obj.im_self.tda
            except AttributeError:
                tda = dict()

            try:
                tra = test.obj.im_self.tra
            except AttributeError:
                tra = dict()
        elif isinstance(test.obj, types.FunctionType):
            try:
                tda = test.obj.func_globals['tda']
            except KeyError:
                tda = dict()
                
            try:
                tra = test.obj.func_globals['tra']
            except KeyError:
                tra = dict()

    elif isinstance(test, unittest.UnitTestCase):
        try:
            tda = test.tda
        except AttributeError:
            tda = dict()
        try:
            tra = test.tra
        except AttributeError:
            tra = dict()

    else:
        tda = dict()
        tra = {'warning':'Unknown test type: tda/tra not found'}
        raise TypeError("Unknown test type, %s"%type(test.test))

    return tda, tra            
    
def pytest_runtest_makereport(__multicall__, item, call):
    item.end_time = time.time()
    
    report = __multicall__.execute()

    if state['enabled'] and call.when == 'call':
        exc = report.longrepr
        name = cleanname(report.location[2])
        if state['pdktestprefix'] != '':
            if not state['pdktestprefix'].endswith('/'):
                name = '%s/%s' % (state['pdktestprefix'], name)
            else:
                name = '%s%s' % (state['pdktestprefix'], name)
        status = {'passed': 'P', 'failed': 'E', 'skipped': 'S'}[report.outcome]

        log = '\n\n'.join((x for x in item.outerr if x))
        
        tda, tra = find_txa(item)

        if report.longrepr is not None:
            tra['Exception'] = report.longrepr
        
        state['report'].report(
            test_name = name,
            status = status,
            start_time = pdktimestamp(item.start_time),
            end_time = pdktimestamp(item.end_time),
            tda = tda,
            tra = tra,
            log = log)
            
    return report
    
