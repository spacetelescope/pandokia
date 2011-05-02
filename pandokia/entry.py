#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

#
# Main entry point into pandokia

helpstr = '''

pdk check_expected test_run_type test_run
    check that test_run contains a test result for each one listed as
    expected for type test_run_type; create a Missing record for any
    test that is missing.

pdk clean
    removes associated records from database if related primary records
    have been deleted.  You need to do this after 'pdk delete_run' to
    keep cruft from accumulating, but you don't need to do it right away.
    It may take some time depending on the size of your database.

pdk delete_background_step
    run one step of the background cleaner used by the new delete algorithm

pdk delete_background

pdk delete_run test_run
    removes named test run from the database

pdk export test_run_pattern [ -h host ] [ -p project ] [ -c context ] 
    export records from the database in pandokia import format

pdk gen_expected test_run_type test_run
    declares that all the tests seen in the named test_run are expected
    in runs of type test_run_type

pdk getenv
    get environment that would be used

pdk import files
    import pdk result files into the database

pdk import_contact < contact_file
    purges the projects listed in contact_file from the contact table,
    then builds new contact table entries.  This uses the 'expected'
    table to generate the matching patterns, so you may need to 
    'pdk gen_expected' first.

pdk initdb
    obsolete - see sql scripts in pandokia/sql

pdk notify
    send notification emails about failed tests

pdk ok [ okfiles ]
    Tests that use reference files can leave behind 'okfiles' when
    they run.  The okfile contains the information necessary to copy the
    output files to the reference files.  This command performs that copy.

pdk run
    run tests; use 'pdk run --help' for more detail

pdk webserver
    start up a development web server.  The root of the server is the
    current directory.  It serves pages on port localhost:7070.

'''
import os
import sys

def run() :

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
    if len(sys.argv) < 2 :
        print helpstr
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

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

    if cmd == 'clean' :
        print "not implemented any more"
        return 1


    if cmd == 'clean_queries' :
        import pandokia.cleaner
        return pandokia.cleaner.clean_queries()

    if cmd == 'delete_background_step' :
        import pandokia.cleaner
        return pandokia.cleaner.delete_background_step()

    if cmd == 'delete_background' :
        import pandokia.cleaner
        return pandokia.cleaner.delete_background(args)

    if cmd == 'config' :
        import pandokia.config
        f= pandokia.config.__file__
        if f.endswith(".pyc") or f.endswith(".pyo") :
            f = f[:-1]
        print f
        return 0

    if cmd == 'delete_run' :
        import pandokia.cleaner
        return pandokia.cleaner.delete_run(args)

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
        print helpstr
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

    if cmd == 'notify':
        print "COMMAND OBSOLETE"
        return 1
        import pandokia.contact_notify
        return pandokia.contact_notify.run(args)

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

    sys.stderr.write("command %s not known\n'"%cmd)
    return 1
