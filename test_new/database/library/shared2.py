from __future__ import print_function
import pandokia.helpers.minipyt as minipyt
minipyt.noseguard()

import pprint

@minipyt.test
def t100_explain_runs_no_dict():
    x = dbx.explain_query("select * from test_table", { } )
    print(x)
