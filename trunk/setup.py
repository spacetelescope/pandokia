## basic imports

import sys
import os
import os.path

##
#

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: POSIX',
   # 'Operating System :: Microsoft :: Windows',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Unix',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Quality Assurance',
    'Topic :: Software Development :: Testing',
]

## detect our environment
#
# This setup.py was written to work with distutils.  I still use
# it with distutils, so I'm preserving that capability.  If you
# try to install with easy_install or pip, it will load setuptools
# before setup.py; we detect that here and modify our behaviour
# to work in the setuptools environment.
#
# if you use setuptools (including easy_install or pip) then
# the CGI magic that was in earlier versions of pandokia will
# not work.  Your web server must provide a proper PYTHONPATH.

if 'setuptools' in sys.modules :
    from setuptools import setup
    have_setuptools = True

else :
    from distutils.core import setup
    have_setuptools = False

## detect our environment
#
# A flag for whether this is a MS Windows machine
#
# n.b. Windows support is strictly experimental and incomplete.

import platform
# print platform.python_version()
windows = platform.system() == 'Windows'

## basic config
#
# This is a list of all the packages that we install.

package_list = [
    'pandokia',             # core of pandokia system
    'pandokia.runners',     # "plugin-like" things that run various kinds of tests
    'pandokia.helpers',     # modules to use in running your tests
    'stsci_regtest',        # legacy STScI test system for IRAF packages
]

#
# These are all commands that the user can type.
#
python_commands = [
    'pdk',                      # pandokia main entry point
    'pdkrun',                   # like "pdk run"
    'pdk_filecomp',             # helper file comparisons for use in shell scripts
    'pdk_python_runner',        # exec for custom test runner written in python
    'pdk_stsci_regress_helper', # part of regtest runner
    'pdk_stsci_regress_refs',   # ?
    'pdknose',                  # run nose with pdk plugin
    'pdkpytest',                # run py.test with pdk plugin
    'junittopdk',               # convert junit/xml to pandokia format
    'tbconv',                   # table conversion among various formats
    'pywhere',                  # show where a python module is
    'json_pp',                  # json pretty printer
     ]

shell_commands = [
    'pdk_gen_contact',          # create contact list for pdk import_contact
    'pdk_monthly',              # cleaner tool for stsci
    'pdk_run_helper.sh',        # helper for shell scripts using "run" runner
    'pdk_shell_runner',         # run a shell script as a test, use exit code as status
    'pdk_shell_runner_helper',  # tools to use in shell_runner scripts
    'pdk_stsci_regress',        # regtest runner
    'sendto',                   # here for convenience; not really pandokia
    'shunit2_plugin_pdk',       # pandokia plugin for shunit2
    'xtname',                   # here for convenience; not really pandokia
    'pdk_sphinxweb',            # builds a bunch of sphinx documents into a web page
    'checktabs',                # check .py/.rst files for tabs in indents
    ]

command_list = python_commands + shell_commands

## version
#
# get our version out of __init__ so we only have to edit one place
#

f=open("pandokia/__init__.py","r")
for x in f :
    if x.startswith('__version__') :
        exec(x)
        break
f.close()


##
# if the stsci distutils hack is present, use it to try to capture
# subversion information.
#
# If you are not at STScI, you do not need this.  Delete this call if
# it causes you any trouble.
#
def du_hack() :
    try :
        import stsci.tools.stsci_distutils_hack as H
    except ImportError :
        pass
    else :
        # we have to deal with two possible versions of the distutils
        # hack - the latest, and the one in the pyetc environment.  So,
        # __set_svn_version__ is duplicated and modified here.
        version_file = "pandokia/svn_version.py"
        rev = H.__get_svn_rev__('.')
        if rev is None :
            if os.path.exists(version_file) :
                    return
            revision = 'Unable to determine SVN revision'
        else:
            if ( rev == 'exported' or rev == 'unknown' ) and os.path.exists(version_file) :
                return
            revision = str(rev)
        info = H.__get_full_info__('.')
        f = open(version_file,'w')
        f.write("__svn_version__ = %s\n" % repr(revision))
        f.write("\n__full_svn_info__ = '''\n%s'''\n\n" % info)
        f.close()
du_hack()

##
# we provide setuptools-style entry points that cause plugins to
# be available to some other programs.  This is the setuptools
# format for defining them.

entry_points_dict = {
    'pytest11' : ['pandokia = pandokia.helpers.pytest_plugin'],
    'nose.plugins.0.10' : ['pandokia = pandokia.helpers.nose_plugin:Pdk']
    }

##
# setup args - common to distutils and setuptools

args = {
    'name' :            'pandokia',
    'version' :         __version__,
    'description' :     'Pandokia - a test management and reporting system',
    'author' :          'Mark Sienkiewicz, Vicki Laidler',
    'author_email':     'help@stsci.edu',
    'url' :             'http://ssb.stsci.edu/testing/',
    'license':          'BSD',
    'platforms':        ['Posix', 'MacOS X'],
    'scripts' :         [ "commands/"+x for x in command_list ],
    'packages':         package_list,
    'package_data':     { 'pandokia' : [ '*.sql', '*.html', '*.png', '*.gif', '*.jpg', 'sql/*.sql', 'runners/maker/*'  ]  },
    'classifiers' :     classifiers,
}

# setup args - known by setuptools only

if have_setuptools :
    args.update(
        {
        'entry_points' : entry_points_dict,
        'zip_safe' : False,
        }
    )

##
# Actually do the install
#
d = setup(
    **args
)

##
# cgi magic - "python setup.py install --home /a/b/c" and then you can
# "ln -s /a/b/c/bin/pdk ..../pdk.cgi" on your web server.  This setup
# will write this assignment so the cgi can add  /a/b/c/lib/python to
# sys.path at run time.
#
# works with distutils only, not easy_install, pip, or setuptools.
dir_set = "    pdk_dir = r'%s' # this was set during install by setup.py\n"

#
#
def fix_script(name) :
    fname = os.path.join(script_dir,name)

    f=open(fname,"r")
    l = f.readlines()
    for count, line in enumerate(l) :
        if 'pdk_dir =' in line :
            l[count] = dir_set % lib_dir.replace('\\','/')
    f.close()

    f=open(fname,"w")
    f.writelines(l)
    f.close()

    # windows versions - we hope to use these everywhere
    # to avoid writing a lot of "if windows: x=x+'.py'"
    f=open(fname+".py","w")
    f.writelines(l)
    f.close()

    if windows :
        # make .bat files too, so the commands can have normal names
        f=open(fname+".bat","w")
        f.write("@echo off\n%s.py %%*\n" % fname)
        f.close()

    os.chmod(fname + '.py', 0755)

# py.test and nose use setuptools to find their plugins, but whenever
# I go near setuptools, it always causes problems for me.  You
# can't avoid it with easy_install or pip, but you can otherwise.
#
# If we are just using distutils, procedure here is simple:  Install
# with distutils, then convert the .egg-info file that is installed
# into a setuptools-compatible .egg-info directory that contains the
# entrypoints definition.

def dorque_egg_info( target ) :
    import os
    # convert entry point dict to a .ini file
    entry_points_file = [ ]
    for x in entry_points_dict :
        entry_points_file.append('[' + x + ']')
        for y in entry_points_dict[x] :
            entry_points_file.append(y)

    entry_points_file = '\n'.join(entry_points_file)

    # read the .egg-info file
    pkginfo = open(target).read()

    # delete it
    os.unlink(target)

    # make the .egg-info a directory
    os.mkdir(target)

    # put files in it
    open(target+"/PKG-INFO","w").write(pkginfo)
    open(target+"/not-zip-safe","w").close()
    open(target+"/entry_points.txt","w").write(entry_points_file)


##
# if the user did an install, do some post-install follow-up

if 'install' in d.command_obj :

    if not have_setuptools :
        # Convert the egg-info to a dir that looks like what setuptools
        # uses.  Set the entry points for use by nose and py.test
        dorque_egg_info( d.command_obj['install_egg_info'].target )

    # find where the scripts went
    script_dir = d.command_obj['install'].install_scripts
    lib_dir    = d.command_obj['install'].install_lib
    # print 'scripts went to', script_dir
    # print 'python  went to', lib_dir

    # tell the user about the install
   
    print ''
    print 'If you need to change your path for this install:'
    print ''
    print '    set path = ( %s $path )' % script_dir
    print '    setenv PYTHONPATH  %s:$PYTHONPATH' % lib_dir
    print ''
    print '    export PATH=%s:$PATH'%script_dir
    print '    export PYTHONPATH=%s:$PYTHONPATH'%lib_dir

    print ''
    print 'The CGI is:'
    print ''
    print '    ', os.path.join(script_dir, 'pdk')
    if not have_setuptools :
        # hack the scripts for PDK_DIR_HERE
        for x in python_commands :
            fix_script(x)
            pass
    else :
        print '    If you did not install pandokia in the default location, you must'
        print '    ensure that PYTHONPATH is provided by your web server'
    print ''

    import pandokia
    f= pandokia.cfg.__file__
    if f.endswith(".pyc") or f.endswith(".pyo") :
        f = f[:-1]
    print 'The config file is:'
    print ''
    print '    ',f
    print ''
    print '    you can find the config file at any time with the command "pdk config"'
    print ''


else :
    pass
    # print "no install"

