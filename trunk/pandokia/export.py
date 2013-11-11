#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import pandokia.common as common

import pandokia

pdk_db = pandokia.confi.cfg.pdk_db()

#
# emit a single field of an output record.  use name=value
# or name:\n.text\n.text\n.text\n\n as appropriate
def emit_field( output, name, value ) :
    value=str(value)
    if "\n" in value :
        # put . in front of first line; put . after each
        # line, but take off extra . at end;  A field that
        # contains a newline always ends with a newline because of the
        # input file format.  You can break that assumption by 
        # manipulating the database directly, but you will lose a
        # character here.
        output.write( name+":\n."+value.replace("\n","\n.")[:-1] + "\n" )
    else :
        output.write( name+"="+value+"\n" )


#
# actual export function.
#   output is a file to write to
#   where is an SQL where clause, beginning with the word "WHERE "
#

exportable_fields =[ 'test_run', 'project', 'host', 'context', 'test_name', 'status', 'test_runner', 'start_time', 'end_time', 'location', 'attn' ]
exportable_fields_string =  ','.join(fields)

def do_export( output, where_text, where_dict ) :
    # list of fields to export

    # fields_zip is the index in the returned record of each name in fields
    # it is 1+ because key_id is not listed
    fields_zip = zip( range(1,1+len(fields)), fields )

    # tell the reader to forget any defaults
    output.write( "START\n" )

    sys.stderr.write('begin select\n')
    # 
    sql = ("SELECT key_id, %s FROM result_scalar " % exportable_fields_string ) +where_text
    c = pdk_db.execute( sql, where_dict)
    sys.stderr.write('begin writing\n')
    for record in c :
        export_record( output, record )
    sys.stderr.write('end writing\n')


def do_export_qid( output, qid ) :
    qid = int(qid)
    qid_query = "SELECT key_id FROM query WHERE qid = %d " % qid
    c = pdk_db.execute( qid_query )
    for key_id in c :
        c1 = pdk_db.execute("SELECT key_id, %s FROM result_scalar WHERE key_id = %d" % ( exportable_fields_string, key_id ) )
        for r in c1 :
            export_record(output, r )

# export a single record in the current cursor

def export_record( output, record ) :

        key_id = record[0]
        # we used sqlite3.Row to create rows so that we can loop over the named fields to emit them
        for x, name in fields_zip :
            if record[x] is not None :
                emit_field(output,name,record[x])

        # and now the other tables
        c1 = pdk_db.execute("SELECT name, value FROM result_tda WHERE key_id = :1",(key_id,))
        for x in c1 :
            emit_field(output,'tda_'+x[0],x[1])
        
        c1 = pdk_db.execute("SELECT name, value FROM result_tra WHERE key_id = :1",(key_id,))
        for x in c1 :
            emit_field(output,'tra_'+x[0],x[1])

        c1 = pdk_db.execute("SELECT log FROM result_log WHERE key_id = :1",(key_id,))
        x = c1.fetchone()
        if x is not None :
            emit_field(output,'log',x[0])

        output.write("END\n")


def run(args) :
    # entry point for the command line
    import getopt
    options, value  = getopt.gnu_getopt(args, 'h:p:c:o:' )

    query_dict = { }

    if len(value) < 1 :
        sys.stderr.write("must specify test_run\n")
        return 1

    output = sys.stdout

    for x,y in options :
            if   x == '-c' :
                query_dict['context'] = y
            elif x == '-h' :
                query_dict['host'] = y
            elif x == '-o' :
                output = open(y,"w")
            elif x == '-p' :
                query_dict['project'] = y

    for name in value :
        name = common.find_test_run(value[0])
        c = pdk_db.execute('SELECT name FROM distinct_test_run WHERE name LIKE :1 ORDER BY name',(name,))
        for test_run in c :
            test_run = test_run[0]
            sys.stderr.write('test_run %s\n'%test_run)
            query_dict['test_run'] = test_run
            where_text, where_dict = pdk_db.where_dict([ (x,query_dict[x]) for x in query_dict ] )

            do_export(output, where_text, where_dict)

