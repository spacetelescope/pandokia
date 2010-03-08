#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

dbdir="/ssbwebv1/data2/pandokia/database"

user_list = None

os_info = {

    "arzach":   "RHE 5 / 64",
    "banana":   "Mac x86",
    "basil":    "Solaris 10",
    "bond":     "Mac Leopard",
    "cadeau":   "Mac Leopard",
    "dukat":    "Windows/XP",
    "ekky":     "Mac x86",
    "etc-dev1": "RHE4 / 64, ETC",
    "gaudete":  "RHE 4 / 64",
    "herbert":  "RHE 4 / 32",
    "macbert":  "Mac PPC",
    "motoko":   "RHE 4",
    "quagga":   "RHE 3",
    "ssbwebv1": "RHE 5 / 64",
    "thor":     "RHE 4 / 64",
    "timthe":   "Mac PPC",
    "tufnel":   "Solaris pipeline",

    }

pdk_url = "https://ssb.stsci.edu/pandokia/pdk.cgi"


exclude_dirs = [
    '.svn',
    '.subversion',
    'CVS',
]

runner_glob = [
#   ( 'not_a_test*.py',     None        ),      # file name that is recognizably not a test
    ( 'pycode*.py',         'pycode'    ),      # special runner that just executes python code
    ( '*.py',               'nose'      ),      # nose on a file here
    ( '*.snout',            'snout'   ),        # nose on an installed file
    ( 'test*.sh',           'shell_runner' ),   # example of writing a test runner
    ( '*.xml',              'regtest'   ),      # legacy system used at STScI
]

server_maintenance = False

debug = True

cginame = 'https://ssb.stsci.edu/pandokia/pdk.cgi'

flagok_file = "/eng/ssb/tests/pdk_updates/%s.ok"
