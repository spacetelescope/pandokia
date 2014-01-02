#
# pandokia - a test reporting and execution system
# Copyright 2009, 2011 Association of Universities for Research in Astronomy (AURA) 
#

#
# Main entry point into pandokia

'''

pdk check_expected test_run_type test_run
    check that test_run contains a test result for each one listed as
    expected for type test_run_type; create a Missing record for any
    test that is missing.

pdk clean [ max_records records_per_step sleep_between_steps ]
    Run the background step that cleans deleted material from the database.

pdk clean_queries
    delete old qids

pdk delete -test_run xx -project xx -context xx -host xx -status xx
        -n -wild -count
    delete records from the database

pdk export test_run_pattern [ -h host ] [ -p project ] [ -c context ] 
    export records from the database in pandokia import format

pdk gen_expected test_run_type test_run
    declares that all the tests seen in the named test_run are expected
    in runs of type test_run_type

pdk email

pdk getenv
    get environment that would be used

pdk import files
    import pdk result files into the database

pdk import_contact < contact_file
    purges the projects listed in contact_file from the contact table,
    then builds new contact table entries.  This uses the 'expected'
    table to generate the matching patterns, so you may need to 
    'pdk gen_expected' first.

pdk ok [ okfiles ]
    Tests that use reference files can leave behind 'okfiles' when
    they run.  The okfile contains the information necessary to copy the
    output files to the reference files.  This command performs that copy.

pdk run
    run tests; use 'pdk run --help' for more detail

pdk runstatus
    show status of actively running tests

pdk webserver
    start up a development web server.  The root of the server is the
    current directory.  It serves pages on port localhost:7070.

fuller documentation is available at http://ssb.stsci.edu/testing/pandokia/

'''
import os
import sys

def run( argv = sys.argv ) :

    # first, we have a special heuristic to discover if we are running
    # as a CGI.  If we are, jump in to the cgi entry point.

    # With most web servers, QUERY_STRING is sufficient to recognize
    # you are in a CGI.  With the python CGIHTTPServer object,
    # you may not get a QUERY_STRING if you are running on MS WINDOWS.
    if 'QUERY_STRING' in os.environ or 'GATEWAY_INTERFACE' in os.environ :
        import pandokia.pcgi
        pandokia.pcgi.run()
        return

    # Ok, not a CGI, so it must be a command line of the form
    # pdk command [ args ]
    if len(argv) < 1 :
        print __doc__
        return

    cmd = argv[1]
    args = argv[2:]

    # each entry here follows the general form of:
    #   if cmd == 'whatever' :
    #       execute_command
    #       return
    #
    # To execute a command, we usually use:
    #       import pandokia.whataver
    #       pandokia.whatever.run(args)
    #
    # All commands are all lower case.
    # All commands are listed here in alphabetic order.

    if cmd == 'check_expected' :
        import pandokia.check_expected as x
        return x.run(args)

    if cmd == 'chronic' :
        import pandokia.chronic as x
        return x.run(args)

    if cmd == 'clean' :
        import pandokia.cleaner
        return pandokia.cleaner.delete_background(args)

    if cmd == 'clean_queries' :
        import pandokia.cleaner
        return pandokia.cleaner.clean_queries()

    if cmd == 'clean_db' :
        import pandokia.cleaner
        return pandokia.cleaner.clean_db(args)

    if cmd == 'config' :
        import pandokia
        f= pandokia.cfg.__file__
        if f.endswith(".pyc") or f.endswith(".pyo") :
            f = f[:-1]
        print f
        return 0

    if cmd == 'delete' :
        import pandokia.cleaner
        return pandokia.cleaner.delete(args)

    if cmd == 'dump_table' :
        import pandokia.db
        return pandokia.db.cmd_dump_table(args)

    if cmd == 'email' :
        import pandokia.contact_notify_select
        return pandokia.contact_notify_select.run(args)

    if cmd == 'export' :
        import pandokia.export
        return pandokia.export.run(args)

    if cmd == 'gen_contact' :
        import pandokia.gen_contact as x
        return x.run(args)

    if cmd == 'gen_expected' :
        import pandokia.gen_expected as x
        return x.run(args)

    if cmd == 'getenv' :
        import pandokia.run as x
        return x.export_environment(args)

    if cmd == 'help' or cmd == '-h' or cmd == '--help' :
        print __doc__
        return

    if cmd == 'import' :
        import pandokia.import_data as x
        return x.run(args)

    if cmd == 'hackimport' :
        import pandokia.import_data as x
        return x.hack_import(args)

    if cmd == 'import_contact' :
        import pandokia.import_contact as x
        return x.run()

    if cmd == 'ok' or cmd == 'okify' :
        import pandokia.ok
        return pandokia.ok.run(args)

    if cmd == 'run' :
        import pandokia.run as x
        (err, lstat) =  x.run(args)
        #import pandokia.common as common
        # print ""
        # print "Summary of entire run:"
        # common.print_stat_dict(lstat)
        return err

    if cmd == 'sql' :
        import pandokia.db
        return pandokia.db.sql_files( args )

    if cmd == 'runstatus' :
        import pandokia.run_status as x
        err = x.display_interactive(args)
        return err

    if cmd == 'version' or cmd == '--version' or cmd == '-v' or cmd == '-V' :
        import pandokia
        print "pandokia",pandokia.__version__
        print os.path.dirname(pandokia.__file__)
        return 0

    if cmd == 'webserver' :
        import pandokia.webserver
        return pandokia.webserver.run(args)

    if cmd == 'maker' :
        import pandokia.runners as x
        print os.path.join( os.path.dirname(x.__file__), 'maker' )
        return 0

    if cmd == 'query' :
        import pandokia
        return pandokia.cfg.pdk_db.query_to_csv( args[0], sys.stdout )

    if cmd == 'recount' :
        import pandokia.cleaner
        return pandokia.cleaner.recount( args )

    if cmd == 'hack' :
        import pandokia.hack
        return pandokia.hack.run(args)

    sys.stderr.write("command %s not known\n"%cmd)
    return 1
