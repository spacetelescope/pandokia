import sys
import os
import pandokia.helpers.pycode as pycode

class CramReporter(object) :

    # convert cram status to pandokia status
    map_status = { 
        '.' : 'P',  # pass
        '!' : 'F',  # fail
        's' : 'D',  # disable
        'e' : 'D',  # cram counts an empty file as a skip
    }

    #
    def __init__( self, option_parser ):
        pass
        option_parser.add_option('--pdk', action='store', default=None, type='str', help='write pandokia format to file' )

    # we don't actually have any parser options
    def handle_parser_options( self, opts ) :
        try :
            self.pdk_log = opts.pdk
        except AttributeError :
            try :
                self.pdk_log = os.environ['PDK_LOG']
            except KeyError :
                self.pdk_log = 'PDK.LOG'
        self.r = pycode.reporter( source_file=None, filename=self.pdk_log, test_runner='cram' )

    # report 
    def report( self, file, status, start_time, end_time, refout, postout, diff ):

        # pandokia test names do not contain file extensions
        if file.endswith('.t') :
            file = file[:-2]

        # convert cram status to pandokia status
        status = self.map_status[status]

        # gather the output from the tested commands
        if postout :
            log = ''.join(postout)
        else :
            log = ''    # hmm - no output?
            
        # if there were differences, add the diff too
        if diff :
            log = log + ''.join(diff)

        # write the pandokia report for this test
        self.r.report( test_name=file, status=status, start_time=start_time, end_time=end_time,
            log= log )

    # finish means we just close the file; pandokia logs do not contain a summary
    def finish( self, total, skipped, failed ) :
        self.r.close()

    # the pandokia system does not interact with the user at this stage,
    # therefore cannot ask questions
    def ask_patch( self, diff, answer ) :
        return False
