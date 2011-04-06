#
# pandokia - a test reporting and execution system
# Copyright 2009, 2010, 2011 Association of Universities for Research in Astronomy (AURA) 
#

#
# database functions common to multiple database engines
#

import re
import types

re_funky_chars = re.compile('[^ -~]')   
# used to remove control characters.  Yes, it works on strings with \0
# in them.

re_star_x_star = re.compile('^\*[^*]*\*$')


def next_name( v ) :
    global name_dict_counter
    n = str(name_dict_counter)
    name_dict[n] = v
    name_dict_counter += 1
    return n

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
def where_dict(list, more_where = None ) :
    global name_dict_counter, name_dict
    name_dict = { }
    name_dict_counter = 0

    and_list = [ ]
    for name, value in list :
        if ( value == '*' ) or ( value is None ) :
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
                if v is None :
                    # Our convention is that None matches anything,
                    # so if one of the possible values is None, then this
                    # field will always match
                    or_list = [ ]
                    break

                v = str(v)

                # I assume any control character is hostile action.  It
                # is convenient to just quietly drop it.
                v = re_funky_chars.sub('',v)

                # if value contains a wild card, add a GLOB
                # action, otherwise add '='.
                if '%' in v :
                    n = next_name( v )
                    or_list.append( name + " LIKE :" + n + " " )

                elif '*' in v :
                    # this is a hack to make some things a little easier to get going
                    # *x or X* can be used with LIKE

                    if v.startswith('*') :
                        v = '%'+v[1:]
                    if v.endswith('*') :
                        v = v[:-1]+'%'

                    if '*' in v :
                        assert 0, 'GLOB not supported'

                    n = next_name( v )
                    or_list.append( name + " LIKE :"+n+" ")

                elif '*' in v or '?' in v or '[' in v :
                    assert 0, 'GLOB not supported'
                    or_list.append( name + " GLOB :" + n + " " )
                else :
                    n = next_name( v )
                    or_list.append( name + " = :" + n + " " )
                
        # print "or_list",or_list
        if len(or_list) > 0 :
            and_list.append( '(' + ( ' OR ' .join( or_list ) ) + ')' )

    res = ' AND '.join(and_list)

    if more_where :
        if res != '' :
            res = res + ' AND ' + more_where
        else :
            res = more_where

    # if we some how managed to avoid adding any conditions to the
    # string, we also do not want the word "WHERE " in it.  The
    # user then has "select ... from table" + ""
    if res != "" :
        res =  "WHERE " + res
    return res, name_dict

