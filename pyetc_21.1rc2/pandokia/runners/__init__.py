"""
This is a package to hold test runners.  See doc/Adding_Runners.rst for details.
"""

# edit this if you create a new runner
runner_glob = [
#   ( 'not_a_test*.py',     None        ),      # file name that is recognizably not a test
    ( '*.py',               'nose'      ),      # nose on a file here
    ( 'test*.sh',           'shell_runner' ),   # single test in a shell script
    ( 'test*.csh',          'shell_runner' ),   # single test in a csh script
    ( '*.xml',              'regtest'   ),      # legacy system used at STScI
    ( '*.shunit2',          'shunit2'   ),      # shunit2 with stsci hacks
    ( '*.c',                'maker'     ),      # compiled C unit tests (fctx)
    ( '*.run',              'run'       ),      # run a pdk-aware executable
]




