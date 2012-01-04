import pandokia.helpers.minipyt as minipyt
minipyt.noseguard()

dbx = None  # will be assigned after we are imported

import StringIO

csv_of_table = '''a,b,c
a,b,1
a,c,2
aaa,bbb,111
'''

@minipyt.test
def t020_csv() :
    out = StringIO.StringIO()
    dbx.table_to_csv( 'test_table', out )
    s = out.getvalue().replace('\r','')
    if s != csv_of_table :
        import difflib
        for x in difflib.context_diff(s.split('\n'), csv_of_table.split('\n') ) :
            print x
        assert 0, 'Not match'

