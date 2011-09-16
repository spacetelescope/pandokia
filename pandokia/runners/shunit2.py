import platform
windows = platform.system() == 'Windows'

if windows :
    # You can't run shunit2 on Windows, so report those tests as Disable.
    # (maybe do something for cygwin/mingw some day.)

    def run_internally(env) :
        f = open(env['PDK_LOG'],"a")

        # construct the name the same way that shunit2 does
        name = env['PDK_TESTPREFIX'] +  env['PDK_FILE']
        if name.endswith('.sh') :
            name = name[:-3]
        elif name.endswith('.shunit') :
            name = name [:-7]
        f.write("name=%s\n"%name)

        f.write("status=D\nlog=shunit2 not available on Windows\nEND\n\n")
        f.close()

    def command(env) :
        return None

else :
    def command( env ) :
        return 'shunit2 --plugin pdk $PDK_FILE'

# returns a list of tests in the file
def list( env ) :
    return [ ]

