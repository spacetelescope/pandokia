import distutils.core
import os
import os.path

import platform
# print platform.python_version()

windows = platform.system() == 'Windows'


# bug: take this out (?)
# os.system("rm -rf build")

package_list = [
    'pandokia',             # core of pandokia system
    'pandokia.runners',     # "plugin-like" things that run various kinds of tests
    'pandokia.helpers',     # modules to use in writing your tests, usually with nose/unittest
    'stsci_regtest',        # legacy STScI IRAF/PyRAF test system
]

#
# These are all commands that the user can type.  We will susbstitute strings
# in them so that they will find the pandokia we are installing even if it is
# not on PYTHONPATH, _even_ if there is _another_ pandokia on pythonpath.
command_list = [
    'pdk', 
    'pdknose',
    'pdkpytest',
    'pdkrun',
    'tbconv',   # this doesn't really belong in pandokia, but
                # I plan to use it for the documentation and it
                # needs a place to live.  and it need pandokia.text_table
    'pdk_shell_runner',
    'pdk_shell_runner_helper',

    'pdk_filecomp',

    'pdk_stsci_regress',
    'pdk_stsci_regress_helper',
    'pdk_stsci_regress_refs',

    # 
    'pdk_gen_contact',

    # run various python modules for test runners
    'pdk_python_runner',

    # plugin for shunit2
    'shunit2_plugin_pdk',

]


#
# These scripts should start "#!/usr/bin/env python", not with whatever
# python we happen to be using.
use_usr_bin_env = [
    'pdknose',
    'pdkpytest',
    'pdk_stsci_regress_helper',
    'pdk_python_runner',
]

args = {
    'name' :            'pandokia',
    'version' :         '1.0',
    'description' :     'Pandokia - a test management and reporting system',
    'author' :          'Mark Sienkiewicz, Vicki Laidler',
    'author_email':     'help@stsci.edu',
    'url' :             'https://svn.stsci.edu/trac/ssb/etal/wiki/Pandokia',
    'license':          'BSD',
    'platforms':        ['Posix', 'MacOS X'],
    'scripts' :         [ "commands/"+x for x in command_list ],
    'packages':         package_list,
    'package_data':     { 'pandokia' : [ '*.sql', '*.html', '*.png', '*.gif', '*.jpg', 'sql/*.sql' ]  },
}

#
# Actually do the install
#
d = distutils.core.setup(
    **args
)

dir_set = "pdk_dir = r'%s' # this was set during install by setup.py\n"

#
#
def fix_script(name) :
    fname = os.path.join(script_dir,name)

    f=open(fname,"r")
    l = f.readlines()
    if name in use_usr_bin_env :
        l[0] = '#!/usr/bin/env python\n'
    for count, line in enumerate(l) :
        if line.startswith("PDK_DIR_HERE") :
            l[count] = dir_set % lib_dir.replace('\\','/')
    f.close()

    f=open(fname,"w")
    f.writelines(l)
    f.close()

    # windows versions - turns out we use these everywhere
    # to avoid writing a lot of "if windows: x=x+'.py'"
    f=open(fname+".py","w")
    f.writelines(l)
    f.close()

    # make .bat files too, so the commands can have normal names
    f=open(fname+".bat","w")
    f.write("@echo off\n%s.py %%*\n" % fname)
    f.close()

    if not windows :
        os.chmod(fname + '.py', 0700)

if 'install' in d.command_obj :
    # they did an install
    script_dir = d.command_obj['install'].install_scripts
    lib_dir    = d.command_obj['install'].install_lib
    print 'scripts went to', script_dir
    print 'python  went to', lib_dir
    for x in command_list :
        fix_script(x)
    print 'set path = ( %s $path )' % script_dir
    print 'setenv PYTHONPATH  %s:$PYTHONPATH' % lib_dir
else :
    print "no install"
