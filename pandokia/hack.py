
# a place for testing little hacks - this is whatever I wanted to try out today

import pandokia
import pandokia.text_table

pdk_db = pandokia.cfg.pdk_db

def cursor_to_table( c, t=None ) :
    if t is None :
        t = pandokia.text_table.text_table()
    row = len(t.rows)

    for x in c :
        col = 0
        for y in x :
            t.set_value( row, col, y )
            col = col + 1
        row = row + 1
    return t


def run(args ) :
    c = pdk_db.execute("  select distinct test_run_type, context, project, host, count(*) from expected group by test_run_type, project, host, context order by test_run_type, context, project, host " )

    t = cursor_to_table( c )

    print t.get_rst()
