# This is a merging of the idea at
# http://code.activestate.com/recipes/52215-get-more-information-from-tracebacks/
# with traceback (from the standard library) and a few other things 
# - Mark S. 2014-12-04

import sys, linecache

# variable names found in this set will not be displayed
default_ignore_vars = set( [ '__builtins__', '__doc__' ] )

def exc( show_globals=True, ignore_vars=None, write=None) :
    """
    Print the usual traceback information, followed by a listing of the
    current values of variables visible to each frame.

    l = pandokia.helpers.backtrace.exc( write=sys.stdout )
        get stack trace as list

    pandokia.helpers.backtrace.exc( write=sys.stdout )
        show stack trace on stdout

    l = pandokia.helpers.backtrace.exc( show_globals = False )
        ignore global variables in the report

    l = pandokia.helpers.backtrace.exc( ignore_vars = set( 'a', 'b' ) )
        do not display variables named "a" and "b" in trace
    
    """

    if ignore_vars is None :
        ignore_vars = default_ignore_vars
    else :
        ignore_vars = set( [ x for x in ignore_vars ])
    
    # get the location of the most recent exception
    excinfo = sys.exc_info()

    # get the traceback
    tb = excinfo[2]

    # The traceback does not have everything we want.  Run to the
    # end of the stack to find the frame of the last item on the
    # traceback.
    while 1:
        if not tb.tb_next:
            break
        tb = tb.tb_next

    # Follow the frames backwards to find the top of the real stack.
    # At the same time, gather a list of the frames (in reverse order).
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back

    # Reverse it (to get it in forward order).
    stack.reverse()

    # Get text of the exception.
    exception_str = repr(excinfo[1])

    # Do not hang on to the excinfo; let the garbage collector have it.
    del excinfo

    # rval is the list of lines to print for the report.
    rval = [ '', exception_str, '' ]

    # now walking the stack, using the previously collected list.
    for frame in stack :

        filename = frame.f_code.co_filename
        name = frame.f_code.co_name

        # note that frame.f_code.f_lineno has continued changing
	    # during the code that eventually calls this function.  We
	    # have to get the line number from the traceback.
        lineno = frame.f_lineno

        rval.append( "%s : %s - %s " % ( filename, lineno, name) )

        # just like in traceback.py
        linecache.checkcache(frame.f_code.co_filename)

        # but print a few lines before and after
        for x in range( max(lineno - 3, 0), lineno + 4 ) :
            line = linecache.getline(filename, x, frame.f_globals)
            if line:
                if x == lineno :
                    rval.append('->' + line[:-1])
                else :
                    rval.append(' .' + line[:-1])
        rval.append('')

	    # want to explain which are global and which are local; get
	    # all keys of all variables, sorted.
        if show_globals :
            g = frame.f_globals
        else :
            g = { }
        l = frame.f_locals

        keys = sorted( set( l.keys() + g.keys() ) - ignore_vars )

        # show them
        for key in keys :
            if key in l :
                eq = "L"
                value = l[key]
                # if a local variable is masked by a global, show both values
                if key in g :
                    try:                   
                        sss = '  %20s G <masked by local> %s' % ( key, eq, repr(value).replace('\n',r'\n' ) )
                    except:
                        sss = '  %20s G <masked by local> <error printing value>' % key
                    rval.append(sss)
            else :
                eq = "G"
                value = g[key]
            try:                   
                sss = '  %20s %s %s' % ( key, eq, repr(value).replace('\n',r'\n' ) )
            except:
                sss = '  %20s <error printing value>' % key
            rval.append(sss)
        
        rval.append('')

    # duplicate the exception string at the end
    rval.append( exception_str )
    rval.append( '' )

    if hasattr(write,'write') :
        for x in rval :
            write.write(x)
            write.write("\n")
    return rval


def foo():
        raise AssertionError()
def here(*l, **kw) :
    try :
        foo()
    except AssertionError :
        exc(*l, **kw)


if __name__ == '__main__':
    #A simplistic demonstration of the kind of problem this approach can help
    #with. Basically, we have a simple function which manipulates all the
    #strings in a list. The function doesn't do any error checking, so when
    #we pass a list which contains something other than strings, we get an
    #error. Figuring out what bad data caused the error is easier with our
    #new function.
    def nest1(thing) :
        return nest2(thing)

    def nest2(thing):
        backtrace = 0
        return "0" * (4 - len(thing)) + thing

    
    data = ["1", "2", 3, "4"] #Typo: We 'forget' the quotes on data[2]
    def pad4(seq):
        """
        Pad each string in seq with zeros, to four places. Note there
        is no reason to actually write this function, Python already
        does this sort of thing much better.
        Just an example.
        """
        return_value = []
        for thing in seq:
            return_value.append(nest1(thing))
        return return_value

    def cause_exc() :
        try:
            print "HERE"
            pad4(data)
            print "STILL HERE"
        except:
            for x in exc() :
                print x

    # cause_exc()

    def a() :
        b()
    def b() :
        c()
    def c() :
        d()
    def d() :
        cause_exc()

    a()
