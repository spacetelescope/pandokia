import distutils.core

# import platform
# print platform.python_version()

import os

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
    'pdk_gen_contact',
    'pdk_python_runner',
]


#
# These scripts should start "#!/usr/bin/env python", not with whatever
# python we happen to be using.
use_usr_bin_env = [
    'pdknose',
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
    'package_data':     { 'pandokia' : [ '*.sql', '*.html', '*.png', '*.gif', '*.jpg' ] },
}

#
# Actually do the install
#
d = distutils.core.setup(
    **args
)

dir_set = "pdk_dir = '%s' # this was set during install by setup.py\n"

#
#
def fix_script(name) :
    fname = script_dir + "/" + name

    f=open(fname,"r")
    l = f.readlines()
    if name in use_usr_bin_env :
        l[0] = '#!/usr/bin/env python\n'
    for count, line in enumerate(l) :
        if line.startswith("PDK_DIR_HERE") :
            l[count] = dir_set % lib_dir
    f.close()

    f=open(fname,"w")
    f.writelines(l)
    f.close()

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
