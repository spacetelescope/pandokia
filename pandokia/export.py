#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import sys
import pandokia.common as common

#
# emit a single field of an output record.  use name=value
# or name:\n.text\n.text\n.text\n\n as appropriate
def emit_field( output, name, value ) :
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
def do_export( output, where ) :
    db = common.open_db()

    sqlite3 = common.get_db_module()
    db.row_factory = sqlite3.Row

    # list of fields to export
    fields =[ 'test_run', 'project', 'host', 'context', 'test_name', 'status', 'test_runner', 'start_time', 'end_time', 'location', 'attn' ]

    # tell the reader to forget any defaults
    output.write( "RESET\n" )

    # 
    c = db.execute("SELECT key_id, test_run, project, host, context, test_name, status, test_runner, start_time, end_time, location, attn FROM result_scalar "+where)
    for record in c :

        # we used sqlite3.Row to create rows so that we can loop over the named fields to emit them
        for x in fields :
            if record[x] is not None :
                emit_field(output,x,record[x])

        # and now the other tables
        c1 = db.execute("SELECT name, value FROM result_tda WHERE key_id = ?",(record['key_id'],))
        for x in c1 :
            emit_field(output,'tda_'+x[0],x[1])
        
        c1 = db.execute("SELECT name, value FROM result_tra WHERE key_id = ?",(record['key_id'],))
        for x in c1 :
            emit_field(output,'tra_'+x[0],x[1])

        c1 = db.execute("SELECT log FROM result_log WHERE key_id = ?",(record['key_id'],))
        x = c1.fetchone()
        if x is not None :
            emit_field(output,'log',x[0])

        output.write("END\n")


def run(args) :
    # entry point for the command line
    import getopt
    options, value  = getopt.gnu_getopt(args, 'h:p:c:o:' )

    query_dict = { }
    if len(value) > 1 :
        sys.stderr.write("too many arguments: %s\n",value[1])
        return 1

    if len(value) < 1 :
        sys.stderr.write("must specify test_run\n")
        return 1
        
    query_dict['test_run'] = common.find_test_run(value[0])

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

    where = common.where_str([ (x,query_dict[x]) for x in query_dict ] )

    do_export(output, where)
