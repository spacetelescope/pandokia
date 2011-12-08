import os
import platform

test_mode = None
#   not in test mode
#
# test_mode = 'L'
#   cause it to be very likely that the watcher will see a locked record
#
# test_mode = 'C'
#   cause it to be very likely that the watcher will see a record change
#   while it is reading it

if test_mode :
    saw_locked = 0
    saw_changed = 0

if platform.system() == 'Windows' :

    def init_status( *l, **kw ) :
        pass
    def pdkrun_status( *l, **kw ) :
        pass
    def display( *l, **kw ) :
        pass
    def display_interactive( *l, **kw ) :
        pass

else :

    # A note on locking:
    #
    # The shared memory block is divided into records.  Each process knows
    # its own record number and only updates its own record.  So, we have
    # no need to deal with competing writers.
    #
    # The reader would like to recover consistent data.  The valid flag has
    # a serial number that is incremented each time it is updated, though
    # it wraps fairly quickly.  get_value_at_offset() looks for the valid
    # flag being different before/after it recovers the data.  If it is
    # different, we know we lost the race and should look again.
    #
    # Since it takes so little time to copy out a value, we presume that the
    # writer cannot make so many updates that N+1+1+1... wraps back around
    # to exactly N again while we are reading the data.
    # 
    # 

    def init_status(file=None, n_records=10, status_text_size = 2000 ) :
        '''Create a status file with n_records blank records in it
        '''


        valid_flag_size = 1

        try :
            import mmap
        except ImportError :
            return None

        if file is None :
            file = os.getcwd() + '/pdk_statusfile'
            try :
                os.unlink(file)
            except :
                pass
        
        #
        f = open(file,'w')

        # write the header
        #   we generate it twice so we know how big it is - the first time,
        #   we say the size is 0, but we use a fixed format; the second
        #   time, we use the actual length that resulted.  So, you can
        #   grow the header without worrying about alignment/size issues.
        def gen_header() :
            s= '********PDKRUN status monitor 000\n%08d %d %d %d\n'%( 
                header_size,  status_text_size, n_records, valid_flag_size )
            return s

        header_size = 0
        header = gen_header()

        header_size = len(header)
        header = gen_header()

        assert header_size == len(header)

        f.write(('%08x'%time.time())[0:8])
        f.write(header[8:])

        # write a blank record for everybody - use a \n between and
        # the file will be plain text
        for x in range( n_records ) :
            f.write(' ' * ( valid_flag_size + status_text_size ) )
            f.write('\n')

        # done - force it out to disk
        f.close()

        return file

    class status_block(object):

        def __init__( self, file, mode ) :
            import mmap

            if mode == 'w' :
                f=open(file,'r+b')
            else :
                f=open(file,'rb')

            # first line is header to recognize the data file
            n = f.readline()   
            if n[8:] != 'PDKRUN status monitor 000\n' :
                raise Exception('Not a PDKRUN status monitor file: %s'%file)

            # second line is about record sizes
            n = f.readline().strip()
            n = n.split(' ')

            self.header_size      = int(n[0])
            self.status_text_size = int(n[1])
            self.n_records        = int(n[2])
            self.valid_flag_size  = int(n[3])


            # each record contains a valid_flag, status_text, and a newline
            self.record_size = self.valid_flag_size + self.status_text_size + 1

            # what is the offset of the text
            self.status_text_offset = self.valid_flag_size

            # what a "locked" flag looks like
            self.locked_valid_flag = 'X' * self.valid_flag_size

            # how big is the whole file
            file_size = self.record_size * self.n_records + self.header_size 

            if mode == 'w' :
                prot = mmap.PROT_READ | mmap.PROT_WRITE
            else :
                prot = mmap.PROT_READ
            
            # map it into a shared memory block
            self.mem = mmap.mmap(
                fileno = f.fileno(),
                length = file_size,
                flags = mmap.MAP_SHARED,
                prot = prot,
                )

            self.header_timestamp = self.mem[0:8]

        def header_changed( self ) :
            return self.mem[0:8] != self.header_timestamp

        def get_status_text( self, n ) :
            return self.get_value_at_offset( n, self.status_text_offset, self.status_text_size )

        def get_value_at_offset( self, n, offset, len ) :
            # find start of record
            start = self.header_size + n * self.record_size

            # get current value of the valid flag
            flag = self.mem[ start : start + self.valid_flag_size ]

            # if the valid flag shows currently locked, we can't read the value
            if flag == self.locked_valid_flag :
                if test_mode and test_mode == 'L' :
                    global saw_locked
                    saw_locked += 1
                    return 'locked'
                return None

            # pick out the value
            s= self.mem[ start + offset : start + offset + len ]

            # if the valid flag changed while we were reading data, we can't read the value
            if flag != self.mem[ start : start + self.valid_flag_size ] :
                if test_mode and test_mode == 'C' :
                    global saw_changed
                    saw_changed += 1
                    return 'changed'
                return None

            return s

        def set_my_record( self, n ) :
            if n >= self.n_records :
                raise Exception('only %d records in file - using #%d\n'%(self.n_records,n))
            self.my_record = n
            self.my_record_offset = self.header_size + n * self.record_size

        def set_status_text( self, value ):
            return self.set_value_at_offset( self.status_text_offset, self.status_text_size, value )

        def set_value_at_offset(self, offset, blocklen, value ) :
            start = self.my_record_offset

            # find the old valid flag so we can make the new one be different
            old_valid_flag = self.mem[ start : start + self.valid_flag_size ]

            # lock the record - as a multi-byte operation, this is not atomic, but
            # if valid_flag_size == 1, it is.
            self.mem[ start : start + self.valid_flag_size ] = self.locked_valid_flag

            # pad the value
            if len(value) < blocklen :
                value = value + (' ' * (blocklen - len(value) + 1))

            # limit the value
            value = value[0:blocklen]

            # stuff it into the shared memory
            s= self.mem[ start + offset : start + offset + blocklen ] = value

            # clear the lock
            try :
                n = (int(old_valid_flag) + 1) & 7
            except :
                n = 0

            # set the new valid flag
            self.mem[ start : start + self.valid_flag_size ] = "%*d"%(self.valid_flag_size,n)


    if __name__ == '__main__' :
        import sys
        import time
        s = sys.stdin.readline().strip() 

        if s == 'i' :
            init_status('pdk_statusfile', 10)
            s = 'w'

        if s == 's' :
            m = status_block('pdk_statusfile')
            m.set_my_record(1)
            for x in range(0,10000000) :
                m.set_status_text("%d"%x)
        else :
            m = status_block('pdk_statusfile')
            m.set_my_record(int(s))
            while 1 :
                print ">"
                l = sys.stdin.readline().strip()
                if l[0] in '0123456789' :
                    n = int(l.split()[0])
                    m.set_my_record(n)
                elif l[0] == 's' :
                    m.set_status_text(l[1:])
                else :
                    print "?"


    import time

    mem = None

    def pdkrun_status( text, slot=None ) :
        '''A status setting function for use within pdkrun

        You call pdkrun_status( text ) to set your status

        slot is the slot number to note the status in (default is PDK_PROCESS_SLOT environment)
        '''

        # If we don't have a statusfile, it doesn't matter
        if not 'PDK_STATUSFILE' in os.environ :
            return

        # If we don't want one for some reason
        if os.environ['PDK_STATUSFILE'] == 'none' :
            return

        # find what slot we are in
        if slot is None :
            if 'PDK_PROCESS_SLOT' in os.environ :
                slot = int( os.environ['PDK_PROCESS_SLOT'] )
            else :
                slot = 0

        # lazy attach to the status file
        global mem
        if mem is None :
            mem = status_block( os.environ['PDK_STATUSFILE'], 'w' )
            mem.set_my_record(slot)

        # stuff the value into the data block
        mem.set_status_text( repr(text) + ',%d'%time.time())


    def display( visual, waiting_for_start ) :
        import sys
        import time
        import ast
        import os.path
        import datetime

        filename = 'pdk_statusfile'

        done_waiting = not waiting_for_start

        if waiting_for_start :
            while not os.path.exists(filename) :
                time.sleep(1)

        m = status_block(filename, 'r')

        times = { }

        while 1 :
            if visual:
                # every terminal we see is likely to be ANSI (xterm, gnome-terminal, kterm, putty )
                # home, clear to end of page
                sys.stdout.write('\033[H\033[J')

            if m.header_changed() :
                m = status_block(filename, 'r')
                done_waiting = not waiting_for_start

            any = 0
            for x in range(0,m.n_records) :
                s = m.get_status_text(x)
                if s is None :
                    sys.stdout.write('-')
                else :
                    try :
                        text, tyme = ast.literal_eval(s)
                    except SyntaxError :
                        text = str(s).strip()
                        tyme = 'None'
                    else :
                        if not tyme in times :
                            times = { }
                            times[tyme] = str(datetime.datetime.fromtimestamp(tyme))
                        tyme = times[tyme]
                        text = str(text).strip()
                        if text != '' :
                            any = 1
                            done_waiting = 1
                    sys.stdout.write('%2d %s %s'%(x,tyme,text))

                if visual :
                    # clear to end of line
                    sys.stdout.write('\033[K')
                sys.stdout.write('\n')

            if test_mode :
                sys.stdout.write('%d %d %d\n'%(time.time(),saw_locked, saw_changed))

            if not visual :
                break
            if not any and done_waiting :
                break
            time.sleep(1)

    def display_interactive(args) :
        # should do some arg parsing here
        display(1,1)
