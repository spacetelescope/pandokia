import sys

#####
#
# dprint is way easier to read than pprint, but it was originally
# only intended to work well on dicts/lists/scalars.  If it works
# on anything else, then bonus.
#

def dprint( d, indent=0, follow='' ) :
    """ because pprint.PrettyPrinter is too hard to read 

    print nested dictionaries in a nicely indented format
    """
    indent_str='    ' * indent
    l = d.keys()
    l.sort()
    s = indent_str + '{\n'
    maxlen=0
    for x in l :
        if len(x) > maxlen :
            maxlen = len(x)
    maxlen = maxlen + 3
    for x in l :
        s = s + indent_str + ( '%-*s :' % (maxlen,"'%s'"%x) )
        if isinstance(d[x], dict) :
            s = s + "\n" + dprint(d[x], indent+1, follow=',')
        else :
            s = s + " " + repr(d[x])+",\n"
    s = s + indent_str + '}' + follow + '\n'
    return s

#####
#
# read a python expression from a file; useful for creating simple
# data structures for test input.
#

def eval_file( filename ) :
    'open a file, return eval of the contents'
    f=open(filename,"r")
    r = eval(f.read())
    f.close()
    return r

#####
#
# dprint into a file
#

def dlwrite( filename, data, comment = None ):
    ''''write a dict/list item to a file

    The assumption is that the data item is a dict or list, which
    in turn contains only other dicts, lists, or scalars.

    "dl" => "dict / list"
    '''
    f=open(filename,"w")
    if comment is not None :
        f.write('#')
        f.write(comment.replace('\n','\n#'))
        f.write('\n')
    f.write(dprint(data))
    f.close()

#####
#
# return a string showing the current location in the stack.
#

import traceback

def get_stack() :
    return ''.join(traceback.format_stack())

