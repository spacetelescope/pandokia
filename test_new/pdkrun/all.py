import os
import sys
import json

import pandokia.helpers.test_in_db as test_in_db
import pandokia.helpers.pycode as pycode
import pandokia.helpers.filecomp as filecomp



f = open('test_list','r')

query = {
    'test_run' : 'pdkrun_test',
    'project'  : 'default',
    'context'  : 'default',
    'host'     : '*',
    'test_name': '*',
    }

d = test_in_db.load_tests( query )
for x in d :
    print "SEE",x

for test in f :
    test = test.strip()
    if test.startswith('#') :
        continue

    print '-%s-'%test
    tname = test.replace('pdkrun_test_data/','')

    with pycode.test(test) as f :
        tda = f.tda
        tra = f.tra
        
        if not test in d :
            print "NO TEST RESULT FOUND"
            continue

        tinfo = d[test]
        del d[test]

        for x in tinfo :
            print "KEY",x

        del tinfo['start_time']
        del tinfo['end_time'] 
        del tinfo['key_id']
        tinfo['location'] = tinfo['location'].split('pdkrun_test_data')[1]
        if 'tda__okfile' in tinfo :
            tinfo['tda__okfile'] = tinfo['tda__okfile'].split('pdkrun_test_data')[1]

        # bug: should drop the traceback part, but keep the exception at the end
        tinfo['log'] = tinfo['log'].split('Traceback')[0]

        # to a file
        fname = test.replace('/','#')
        fname = fname.replace('\\','#')
        f=open("out/%s"%fname,"w")
        json.dump( d, f, indent=4, sort_keys=True, default=str )
        f.close()

        output = [ ( fname, 'diff' ) ]

        filecomp.compare_files( output, ( __file__, test ), tda, tra )

with pycode.test('no_dups') :
    if len(d) > 0 :
        print "Extra results:"
        for x in d :
            print json.dumps( x, indent=4, sort_keys=True, default=str )

