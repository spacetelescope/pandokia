#
# pandokia - a test reporting and execution system
# Copyright 2009, 2010, 2011 Association of Universities for Research in Astronomy (AURA) 
#

#
# database functions common to multiple database engines
#

import sys
import re
import types
import pandokia.text_table as text_table

re_funky_chars = re.compile('[^ -~]')   
# used to remove control characters. Not space (32) through tilde (127).
# Yes, it works on strings with \0 in them.
# Should we do iso-8859 or just wait to support unicode?

re_star_x_star = re.compile('^\*[^*]*\*$')


class name_sequence(object) :

    def __init__(self) :
        self.counter = 0
        self.dict = { }

    def next(self, v) :
        n = str(self.counter)
        self.counter += 1
        self.dict[n] = v
        return n

# bug: change this name
class where_dict_base(object) :

    '''
    where_dict is a mechanism for constructing SQL WHERE clauses in a
    portable way, but without going so far from SQL as an ORM

    This class exists so you can subclass from it in the database driver.
    It is (so far) the same for every database driver.
    '''
    #
    # convert a list of (name,value) to an sql WHERE clause.  value may be
    # a list to mean any one of the list elements.
    #
    # more_where is added to the end with " AND %s ", so you can add additional
    # clauses that don't fit through the interface.
    #
    # the word "WHERE" is automatically added, but if there is nothing to match
    # then the return is a zero length string.
    #
    def where_dict(self, list, more_where = None ) :
        '''
            where_text, where_dict = pdk_db.where_dict( [
                ('field', value),
                ('anotherfield', anothervalue),
                ], more_where )

            c = pdk_db.execute( "SELECT col FROM tbl %s " % where_text, where_dict)
        '''

        # if the list is a dict, convert it
        if type(list) == dict :
            nl = [ ]
            for x in list:
                nl.append( (x, list[x]) )
            list = nl

        ns = name_sequence()

        and_list = [ ]
        for name, value in list :
            if ( value == '*' ) or ( value == '%' ) or ( value is None ) :
                # if value is "*", we don't need to do a
                # comparison at all.  In sqlite, " xxx glob '*' "
                # takes much longer than leaving out the glob operator.
                or_list = [ ] 
            else :
                # If value is a list, the query is to match any of the values.
                # If it is not a list, we have a list of 1 value.
                if not isinstance( value, types.ListType ) :
                    value = [ value ]

                # print "VALUE", name, value
                or_list = [ ]
                for v in value :
                    if v is None or v == '*' or v == '%' :
                        # Our convention is that None matches anything,
                        # so if one of the possible values is None, then this
                        # field will always match
                        or_list = [ ]
                        break

                    v = str(v)

                    # I assume any control character is hostile action.  It
                    # is convenient to just quietly drop it.
                    v = re_funky_chars.sub('',v)

                    # if value contains a wild card, add a GLOB/LIKE
                    # action, otherwise add '='.
                    if '%' in v :
                        n = ns.next( v )
                        or_list.append( " %s LIKE :%s "%(name,n) )

                    elif '*' in v :
                        # this is a hack to make some things a little easier to get going
                        # *X or X* can be used with LIKE

                        if v.startswith('*') :
                            v = '%'+v[1:]
                        if v.endswith('*') :
                            v = v[:-1]+'%'

                        if '*' in v :
                            assert 0, 'GLOB not supported except *xx or xx* '

                        n = ns.next( v )
                        or_list.append( " %s LIKE :%s "%(name,n) )

                    elif '*' in v or '?' in v or '[' in v :
                        print 'content-type: text/plain\n'
                        print list
                        print v
                        assert 0, 'GLOB not supported'
                    else :
                        n = ns.next( v )
                        or_list.append( " %s = :%s "%(name,n) )
                    
            # print "or_list",or_list
            if len(or_list) > 0 :
                and_list.append(
                        ' ( %s ) ' 
                        % 
                        ( ' OR ' .join( or_list ) )
                    )

        res = ' AND '.join(and_list)

        if more_where :
            if res != '' :
                res = ' %s AND %s '%(res,more_where)
            else :
                res = more_where

        # if we some how managed to avoid adding any conditions to the
        # string, we also do not want the word "WHERE " in it.  The
        # user then has "select ... from table" + ""
        if res != "" :
            res =  "WHERE " + res
        return res, ns.dict


    #
    # extract a table as a csv file
    # used for testing
    #

    def table_to_csv( self, tablename, fname, where='', cols=None ) :

        if cols is None :
            c = self.execute('SELECT * FROM %s LIMIT 1'%tablename )
            cols = [ x[0] for x in c.description ]
            c.close()

        colstr = ','.join(cols)
        
        import csv

        if isinstance(fname,str) :
            f = open(fname,"wb")
        else :
            f = fname

        cc = csv.writer(f,lineterminator='\n')
        cc.writerow( cols )

        print colstr

        print "ORDER",colstr
        c = self.execute('select %s from %s %s order by %s'%(colstr, tablename, where, colstr) )
        for x in c :
            cc.writerow( [ y for y in x ] )
        c.close()

        if not isinstance(fname,str) :
            f.close()

    def query_to_csv( self, query, fname ) :
        import csv
        if isinstance(fname,str) :
            f = open(fname,"wb")
        else :
            f = fname

        cc = csv.writer(f,lineterminator='\n')

        c = self.execute(query)
        for x in c :
            cc.writerow( [ y for y in x ] )
        c.close()

        if not isinstance(fname,str) :
            f.close()

    #
    # run a big sequence of SQL commands
    #
    def sql_commands(self, s, format='rst') :
        # s is a single string, maybe with newlines.  Split it into a
        # list of lines.
        s = s.split('\n')

        # tear comments out of all lines.  hmmm... don't use -- in a
        # string constant...
        import re
        comment = re.compile('--.*$')
        s = [ comment.sub('',x).strip() for x in s ]

        # turns on and off for conditional processing
        active = True

        c = ''
        line = 0
        for x in s :
            line = line + 1
            if x == '' :
                continue

            # This implements the ++driver convention.  A line that
            # begins with ++name begins a section that is only performed
            # when using that database driver.  A line that contains just ++
            # beings a section that is performed for all drivers.
            if x.startswith("++") :
                x=x[2:].split()
                if len(x) == 0 :
                    active = True
                    continue
                if self.pandokia_driver_name in x :
                    active = True
                    continue
                active = False
                continue

            if not active :
                continue

            # gather the line 
            c = c + x + '\n'

            # end of a command.
            if c.endswith(';\n') :
                # perform the command
                cursor = self.execute(c)

                # display the result
                tbl = text_table.text_table()

                # define columns, if we know them
                if cursor.description :
                    for name in cursor.description :
                        name = name[0]
                        tbl.define_column( name )

                # Display the results, if any
                try :
                    # fill the table cells
                    for rownum, rowval in enumerate(cursor) :
                        for colnum, colval in enumerate(rowval) :
                            tbl.set_value( rownum, colnum, colval )

                    if len(tbl.rows) > 0 :
                        # show the table in the format the user asked
                        print tbl.get(format=format, headings=1)
                except self.ProgrammingError as e :
                    if 'no results to fetch' in str(e) :
                        pass
                    else :
                        print "Programming Error for ",c
                        print e

                except self.IntegrityError as e :
                    print "Integrity Error for ",c
                    print e

                cursor.close()

                c = ''

        self.commit()


def cmd_dump_table( args ) :
    import sys
    import pandokia
    for x in args :
        pandokia.cfg.pdk_db.table_to_csv( x,sys.stdout, )

def sql_files( files ) :
    import os.path
    import pandokia
    pdk_db = pandokia.cfg.pdk_db

    format= 'tw'

    while len(files) > 0 and files[0].startswith('-') :
        arg = files[0]
        files = files[1:]
        if arg in ( '-html', '-csv', '-awk', '-rst', '-text', '-trac_wiki', '-tw' ) :
            format = arg[1:]
            print "FORMAT",format
        else :
            print arg, "unrecognized"
            return 1

    if len(files) > 0 :

        dir = os.path.dirname(__file__) + "/sql/"
        for x in files :
            try :
                f = open(x)
            except IOError:
                f = open(dir+x)
            pdk_db.sql_commands(f.read(), format=format)
            f.close()
    else :
        import sys
        pdk_db.sql_commands(sys.stdin.read(), format=format)

    return 0

def db_from_django( settings ) :
    '''Connect to a django database, using the pandokia database interface.

    The parameter is the django settings module.

    This function is useful mainly when you want something from an
    application that uses a django database, but you don't want to go
    through the pain of using the django ORM to form your query.

    '''

    if settings.DATABASE_ENGINE == 'mysql' :
        import pandokia.db_mysqldb as dbmod
        access = {
            'host'  : settings.DATABASE_HOST,
            'db'    : settings.DATABASE_NAME,
            'user'  : settings.DATABASE_USER,
            'passwd': settings.DATABASE_PASSWORD
            }
        if settings.DATABASE_PORT :
            access['port'] = settings.DATABASE_PORT
        db = dbmod.PandokiaDB( access )
        return db

    if settings.DATABASE_ENGINE == 'sqlite3' :
        import pandokia.db_sqlite as dbmod
        db = dbmod.PandokiaDB( 
            {   
            'db'  : settings.DATABASE_NAME,
            }
        )
        return db

    # I have no other django-based databases to test with, but you can
    # see it is relatively simple if there is already pandokia support
    # for that database.

    raise Exception('Pandokia does not know django database engine name %s'%settings.DATABASE_ENGINE)

