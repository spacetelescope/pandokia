import json
import pprint
import difflib

import pandokia.helpers.pycode as pycode
import pandokia.helpers.filecomp as filecomp
import pandokia.helpers.minipyt as minipyt


# See that filecomp._normalize_list() works when given a tuple
with pycode.test('normalize_tuples') :

    # 
    l = [ ( 'f1', 'text' ), ('f2', 'arf', { 'foo' : 1 } ) ]

    filecomp._normalize_list(l)

    result = json.dumps( l, indent=4, sort_keys=True, default=str )

    print result

    ref = """
[
    {
        "comparator": "text",
        "kwargs": {},
        "output": "out/f1",
        "reference": "ref/f1"
    },
    {
        "comparator": "arf",
        "kwargs": {
            "foo": 1
        },
        "output": "out/f2",
        "reference": "ref/f2"
    }
]
"""
    assert filecomp.diffjson( result, ref )


# see that filecomp._normalize_list() works when given a dict
with pycode.test('normalize_dict') :
    l = [ { 'output' : 'OUT', 'reference' : 'REF',  } ]

    assert False, "Test incomplete"

# see that filecomp._normalize_list() works when given a dict
# that needs no normalizing
with pycode.test('not_normalize_dict') :
    assert False, "Test incomplete"
