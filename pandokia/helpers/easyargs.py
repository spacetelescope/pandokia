'''
This is a primitive but effective library for parsing argv.  It is not
getopt or POSIX, but you can write some arg processing with much less
work than getopt, optparse, or argparse.

    import easyargs
    opt, args = easyargs.get( spec, argv )

Parameters: 
    spec is a dictionary that describes all the options that your program
    will accept.

    argv is the list of args; it optional, defaulting to sys.argv[1:]

Return values:
    opt is a returned dictionary of all the options recognized from spec.
    (If the order matters to you, you can't use this library.)

    args is the list of non-option arguments that remain after collecting
    the options.  It stopped processing argv when the next arg did not
    start with '-'.

spec is a dictionary where the key is an option and the value is a
description of how to process it.

    spec = {
        '-v' : 'flag',          # arg takes no parameter, opt['-v'] is
                                # how many times it occurred
        '-f' : 'one',           # arg takes a parameter
        '-mf' : 'list',         # arg takes a parameter, may be specified 
                                # several times to get a list
        '--verbose' : '-v',     # arg is an alias for some other arg
    }


The value '' means that we should count how many times the option occurs.
So,
    # myprog.py -v
    if opt['-v'] > 0 :
        print "verbose"
    else :
        print "not verbose"
    if opt['-v'] >= 2 :
        print "even more verbose"

The value '=' means that we should collect the next word as a parameter
to the option.  Only the last instance of the option counts:
    # myprog -f filename
    if '-f' in opt :
        print "file name is",opt['-f']

The value '=+' means that the option may occur more than once and we want a list
of all the values given
    # myprog -mf f1 -mf f2 
    if '-mf' in opt :
        for x in opt['-mf'] :
            print "another",x

A value beginning with '-' is an alias for another option.  In this
example, '--verbose' is the same as '-v'.  Only '-v' will appear in
the returned opt dict.  Aliases may not point to other aliases.

Bad args passed by the user will raise the BadArgs exception.

A bad spec will raise SyntaxError

'''

# 
class BadArgs(Exception) :
    pass


def get( spec, argv = None, allow_unexpected = False ) :

    # the returned dict 
    opts = { }

    # if the user did not give argv, use sys.argv, but skip the 
    # program name
    if argv is None :
        import sys
        argv=sys.argv
        n=1
    else :
        n=0

    # for opts that are just counted, initialize them to 0
    for x in spec :
        s = spec[x]
        if s == '' or s == 'flag' :
            opts[x] = 0

    # loop over the args, picking out args that we recognize
    arglen = len(argv)
    while n < arglen :

        this_opt = argv[n]

        # if we recognize this arg
        if this_opt in spec :

            # consume it
            n=n+1

            # If there is an error, we want to be able to say the name
            # of the arg that the user gave, not the other arg it is
            # aliased to
            org_this_opt = this_opt

            # find the spec for how to handle it
            this_spec = spec[this_opt]

            # if the spec starts with - that means this opt is an
            # alias for another opt.  You only get one time through,
            # though - no chains and no loops.
            if this_spec.startswith('-') :
                this_opt=this_spec
                this_spec=spec[this_opt]

            if this_spec.startswith('-') :
                raise SyntaxError('Bad spec to easyargs - cannot chain aliases: %s : %s : %s'%(org_this_opt, this_opt, this_spec))

            # if the spec starts with '=', it means an opt that takes an arg
            if this_spec.startswith('=') or ( this_spec == 'one' ) or ( this_spec == 'list' ) :
                if n >= arglen :
                    raise BadArgs('%s requires argument'%org_this_opt)

                # consume the next element as the value
                thisarg = argv[n]
                n=n+1

                # =+ means we want a list
                # =  means we want just the last one
                if ( '+' in this_spec ) or ( this_spec == 'list' ) :
                    l = opts.get(this_opt,[])
                    l.append(thisarg)
                    opts[this_opt]=l
                else :
                    opts[this_opt]=thisarg

            # spec does not start with '=', the opt takes no args -
            # the returned value is how many times we saw it
            else :
                opts[this_opt] += 1

        # unknown arg
        elif this_opt.startswith('-') :
            if allow_unexpected:
                n += 1
            else:
                raise BadArgs("unknown arg %s"%this_opt)

        # anything else is the end of the list
        else :
            break

    # return value is the dict of opts that we collected and
    # the list of parameters that were not opts
    return opts, argv[n:]


###

if __name__ == '__main__' :
    spec = {
        '-l' :      '--list',   # '-l' is the same as '--list'

        '--list' :  '=+',       # '--list' collects a list of all the args 
                                # foo.py --list a --list b --list c
                                #   { '--list' : [ 'a', 'b', 'c' ] }

        '-v' :       '',        # -v is just counted
                                # result is how many times it appeared
                                # foo.py -v -v 
                                #   { '-v' : 2 }
                                # foo.py
                                #   { '-v' : 0 }

        '-a' :      '=',        # foo -a 1 -a 2 
                                #   { '-a' : '2' }

        # an alias that causes an error
        '-x' :      '-y',
        '-y' :      '-z',
    }

    import sys
    args, rest = get(spec)

    l = [x for x in args]
    l.sort()
    for x in l :
        print x,args[x]
    print rest

