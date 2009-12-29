import os
import pandokia.lib
import datetime

class reporter(object) :

    def __init__( self, source_file, setdefault=False, filename=None, test_run=None, project=None, host=None, context=None, location=None, test_runner=None, test_prefix=None ) :

        # in all cases, we need to open the output file and add a START line
        if filename is None :
            filename = os.environ['PDK_LOG']
        self.filename = filename
        self.report_file=open(filename,"a")
        self.report_file.write("\n\nSTART\n")

        # select the prefix to insert in front of test names.
        if test_prefix is None :
            if 'PDK_TESTPREFIX' in os.environ :
                self.test_prefix = os.environ['PDK_TESTPREFIX']
            else :
                self.test_prefix = ''
        else :
            self.test_prefix = test_prefix

        # if we have the name of the source file where the tests are,
        # append it to the prefix.  Otherwise, assume the user has given
        # us a complete prefix to use.
        if source_file is not None :
            if source_file.endswith(".py") :
                source_file = source_file[:-3]
            elif source_file.endswith(".pyc") or source_file.endswith(".pyo") :
                source_file = source_file[:-4]
            self.test_prefix = self.test_prefix + source_file + '.'

        if setdefault :
            # If you are running in the context of pdkrun, all of these
            # values will already be set as defaults in the pdk log file.
            #
            # This option exists so that you can use this module outside
            # the context of pdkrun.

            # test_run - required
            #   what the user provided, else PDK_TESTRUN, else 'default'
            if test_run is None :
                if 'PDK_TESTRUN' in os.environ:
                    test_run = os.environ['PDK_TESTRUN']
                else :
                    test_run = 'default'
            self.write_field('test_run',        test_run )

            # project - required
            #   what the user provided, else PDK_PROJECT, else 'default'
            if project is None :
                if 'PDK_PROJECT' in os.environ :
                    project = os.environ['PDK_PROJECT']
                else :
                    project = 'default'
            self.write_field('project',         project )

            # host - required
            #   what the user provided, else the real host name without the domain
            if host is None :
                host = pandokia.lib.gethostname()
            self.write_field('host',            host )

            # location - optional
            #   what the user provided, else current directory + PDK_FILE
            if location is None :
                if 'PDK_FILE' in os.environ :
                    location = os.getcwd()+"/"+os.environ['PDK_FILE']
                    self.write_field('location',        location )
                else :
                    pass    # no location reported in this case
            else :
                    self.write_field('location',        location )

            # test_runner - optional
            #   what the user provided, else nothing
            if test_runner is not None :
                self.write_field('test_runner',     test_runner )

            # context - currently optional
            #   what the user provided, else PDK_CONTEXT, else nothing
            if context is None :
                if 'PDK_CONTEXT' in os.environ :
                    context = os.environ['PDK_CONTEXT']
            if context is not None :
                self.write_field('context',         context )

            # this saves the default values
            self.report_file.write("SETDEFAULT\n")

        # end if setdefault

    # end def __init__

    def report( self, test_name, status, start_time=None, end_time=None, tra={ }, tda={ }, log=None ) :

        self.write_field('test_name',   self.test_prefix+test_name)

        self.write_field('status',      status)

        if start_time is not None :
            self.write_field('start_time',  str(start_time))

        if end_time is not None :
            self.write_field('end_time',    str(end_time))

        for name in tda :
            self.write_field('tda_'+name, tda[name])

        for name in tra :
            self.write_field('tra_'+name, tra[name])

        if log is not None :
            self.write_field('log',         log)

        self.report_file.write('END\n')

    def start( self, test_name, tda=None ) :
        self.test_name = test_name
        self.tda = tda
        self.start_time = datetime.datetime.now()

    def finish( self, status, tra=None, log=None ) :
        self.report( test_name=self.test_name, status=status, start_time=self.start_time, end_time=datetime.datetime.now(), tda=self.tda, tra=tra, log=log)

    def write_field(self, name, value) :
        value=str(value)
        if '\n' in value :
            if value.endswith('\n') :
                value=value[:-1]
            self.report_file.write('%s:\n'%name)
            for x in value.split('\n') :
                self.report_file.write('.%s\n'%x)
            self.report_file.write('\n')
        else :
            self.report_file.write('%s=%s\n'%(name,value))

    def close(self):
        self.report_file.close()
        self.report_file = None

