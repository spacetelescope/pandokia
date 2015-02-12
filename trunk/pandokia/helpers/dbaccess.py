import pandokia
pdk_db = pandokia.cfg.pdk_db

import pandokia.common

import time


##########
#
# look up a key_id in the database; return a dict of all the fields
#

def load_key_id( key_id ) :

    # select every column of result_scalar 
    c = pdk_db.execute("SELECT key_id, test_run, project, host, context, test_name, status, test_runner, start_time, end_time, location, attn FROM result_scalar WHERE key_id = :1", (key_id,) )

    return load_part_2( c.fetchone() )

##########
#
# common to multiple functions here:  Now that we have selected every column
# of the result_scalar table, convert the result tuple into a named dict,
# then look up values in the other tables by the extracted key_id
#

def load_part_2( result_scalar_tuple, ignore_log=False ) :
    out = { }

    # crack the result into named fields in the dict
    ( out['key_id'],
        out['test_run'],
        out['project'],
        out['host'],
        out['context'],
        out['test_name'],
        out['status'],
        out['test_runner'],
        out['start_time'],
        out['end_time'],
        out['location'],
        out['attn'] ) = result_scalar_tuple

    key_id = result_scalar_tuple[0]

    # collect values from the other tables: tda
    c1 = pdk_db.execute("SELECT name, value FROM result_tda WHERE key_id = :1",(key_id,))
    for x in c1 :
        try :
            v = float(x[1])
        except :
            v = x[1]
        out['tda_'+x[0]] = v

    # collect values from the other tables: tra
    c1 = pdk_db.execute("SELECT name, value FROM result_tra WHERE key_id = :1",(key_id,))
    for x in c1 :
        try :
            v = float(x[1])
        except :
            v = x[1]
        out['tra_'+x[0]] = v

    if not ignore_log :
        # collect values from the other tables: log
        c1 = pdk_db.execute("SELECT log FROM result_log WHERE key_id = :1",(key_id,))
        x = c1.fetchone()
        if x is not None :
            out['log'] = x[0]

    return out

##########
#
#

# default values: we hope the user stuffs values into these variables that
# are more suitable to their application
default_test_run = 'daily_latest'
default_project = '*'
default_context = '*'
default_host = '*'
default_test_name = '*'

def load_identity( test_run = None, project = None, context = None, host = None, test_name = None, ignore_log=False ) :

    # turn unspecified values into the defaults
    if test_run is None :
        test_run = default_test_run
    if project is None :
        project = default_project
    if context is None :
        context = default_context
    if host is None :
        host = default_host
    if test_name is None :
        test_name = default_test_name

    # convert test run name
    test_run = pandokia.common.find_test_run(test_run)

    # build the list of things we want to select on
    select = [
        ( 'test_run', test_run ),
        ( 'project', project ),
        ( 'context', context ),
        ( 'host', host ),
        ( 'test_name', test_name ),
        ] 

    # convert the list to sql and make the query
    hc_where, hc_where_dict = pdk_db.where_dict ( select )

    c = pdk_db.execute("SELECT key_id, test_run, project, host, context, test_name, status, test_runner, start_time, end_time, location, attn FROM result_scalar " + hc_where, hc_where_dict )

    l = [ ]
    for x in c :
        l.append( load_part_2( x, ignore_log ) )

    return l

##########

def load_qid( qid ) :
    l = [ ]
    c = pdk_db.execute('SELECT key_id FROM query WHERE qid = :1', (qid,))
    for key_id,  in c :
        x = load_key_id( key_id )
        l.append(x)
    return l

##########
#
# find the list of unique field names in a list of dictionaries; return
# them in our preferred order

def unique_fields( list_of_dict ) :
    d = { }
    for x in list_of_dict :
        d.update(x)
    l1=['key_id','test_run','project','host','context','test_name','status','test_runner','start_time','end_time','location','attn']
    for x in l1 :
        if x in d :
            del d[x]
    l2 = d.keys()
    l2.sort()
    return l1 + l2


##########
#
# make a table out of a list of dictionaries
#
#   ld = load_identity( ... )
#   # ld is a list of dictionaries
#   t = make_table( ld, unique_fields(ld) )
#   print t.get_csv( headings=False )
#   print t.get_html( headings=True, color_rows=5 )
#

def make_table( list_of_dict, order_of_columns = [ ] ) :
    import pandokia.text_table
    t = pandokia.text_table.text_table()

    if len(order_of_columns) == 0 :
        order_of_columns = sorted( [ x for x in unique_fields( list_of_dict ) ] )

    for x in order_of_columns :
        t.define_column(x)

    for x in list_of_dict :
        row = t.get_row_count()
        for y in order_of_columns :
            if y in x :
                t.set_value(row, y, x[y])

    return t

##########
#
# make a qid out of the list of dictionaries or a list of keys

def make_qid( tests=None, key_ids=None ) :
    key_id_list = [ ]
    if tests :
        key_id_list = [ x['key_id'] for x in tests if ( 'key_id' in x ) ]
    if key_ids :
        key_id_list = key_id_list + key_ids

    # create a new qid - this is the identity of a list of test results

    now = time.time()
    expire = now + ( 30 * 86400 )
    if pdk_db.next :
        newqid = pdk_db.next('sequence_qid')
        c = pdk_db.execute("INSERT INTO query_id ( qid, time, expires ) VALUES ( :1, :2, :3 ) ",
            ( newqid, now, expire ) )
    else :
        c = pdk_db.execute("INSERT INTO query_id ( time, expires ) VALUES ( :1, :2 ) ",
            ( now, expire ) )
        newqid = c.lastrowid

    # Enter the test results into the qdb.
    
    for key_id in key_id_list :
        pdk_db.execute("INSERT INTO query ( qid, key_id ) VALUES ( :1, :2 ) ", (newqid, key_id ) )
    pdk_db.commit()

    return newqid


