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
        elif isinstance(d[x], list) :
            s = s + "\n" + lprint(d[x], indent+1, follow=',')
        else :
            s = s + " " + repr(d[x])+",\n"
    s = s + indent_str + '}' + follow + '\n'
    return s

def lprint( l, indent=0, follow='' ) :
    indent_str='    ' * indent
    s = indent_str + '[\n'
    for x in l :
        s = s + indent_str
        if isinstance(x, dict) :
            s = s + "\n" + dprint(x, indent+1, follow=',')
        elif isinstance(x, list) :
            s = s + "\n" + lprint(x, indent+1, follow=',')
        else :
            s = s + repr(x)+",\n"
    s = s + indent_str + ']' + follow + '\n'
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


#####
#
# show keys of a nested dict/list structure
#

def print_dict_keys(d, depth = 0) :
    for x in sorted(d.keys()) :
        showitem(x, d[x], depth)

def showitem( name, item, depth ) :
        ty = str(type(item))
        ty = ty.replace('<type ','').replace('>','').replace("'",'')
        if 'numpy.ndarray' in ty :
            ty = ty + ' ' + str( item.shape )+' = ' + str(item.size)
        s = '\t'*depth
        if name != '' :
            s = s + name + ' '
        s = s + ty
        if isinstance(item, dict) :
            print s+'(%d)'%len(item)
            print_dict_keys(item, depth+1)
        elif isinstance(item, tuple) :
            print s+'(%d)' % len(item)
            print_list(item, depth+1)
        elif isinstance(item, list) :
            print s+'(%d)' % len(item)
            print_list(item, depth+1)
        else :
            print s

def print_list(l, depth=0) :
    for x in l :
        showitem( '', x, depth )


