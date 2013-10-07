int pdk_init( char *source_file, char *location, char *test_runner, char *test_prefix );
	/*

	source_file
		The base name of the source file is added to the test
		prefix.  May be NULL if you don't want that.

	does not write a setdefault block; assumes pandokia already
	did that.

	does not let you choose an output file name; putenv PDK_LOG if
	you want

	location
		Characteristics of this test run; if NULL, figure out
		the location of the tests from the current directory
		and PDK_FILE.  If it can't, don't report a location.

        test_runner
		If not NULL, report this string as the test runner used.

        test_prefix
            put this prefix on each test name; if NULL, use PDK_TESTPREFIX
            environment.  If not in environment, there is no prefix.

	*/


/*

These are all functions about a particular test.  Call pdk_start(),
then any of the other functions to report whatever you need, then
pdk_finish().

*/

pdk_start( char *test_name, int redirect_output );
	/*
	Call this at the start of each test.  The test name is the unique
	name of this test within this program.

	redirect_output is true if you want to create a temp file and
	collect stdout/stderr into the PDK_LOG file.
	*/

/*
	Various functions to set attributes.
*/
pdk_tda		( char *name, char   *value );
pdk_tda_int	( char *name, int    value );
pdk_tda_double	( char *name, double value);
pdk_tra		( char *name, char   *value );
pdk_tra_int	( char *name, int    value );
pdk_tra_double	( char *name, double value);


pdk_log_str( char *log );
	/*
	If you passed False for redirect_output in pdk_start(), you
	can use this to write the test output to the report.
	*/

pdk_status( char status );
	/*
	You can call this as many times as you want.  The most severe
	status will be reported when you call pdk_finish()
	*/

pdk_finish( );
	/*
	must call this at the end of the test.
	*/
