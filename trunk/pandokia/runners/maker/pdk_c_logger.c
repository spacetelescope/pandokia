/*
* This is a start of an experimental pycode reporter for C.
* Do not expect this to work at all.
*/

#include <stdio.h>
#include <stdlib.h>

#include "pdk_c_logger.h"

FILE *pdk_log_fp = NULL;

char *pdk_testprefix;
int pdk_need_dot_in_name;

/*
* count of how many times each happened
*/
int pdk_pass, pdk_fail, pdk_error, pdk_disable;

/*
* most severe reported status of the current test
*/
char pdk_reported_status;

/*
*/

int pdk_init( char *source_file, char *location, char *test_runner, char *testprefix )
{
	char *s, *t, *u;

	if (pdk_log_fp)
		{
		fprintf(stderr, "duplicate call to pdk_init");
		abort();
		}

	s = getenv("PDK_LOG");
	if (! s)
		{
		fprintf(stderr, "PDK_LOG not set");
		abort();
		}

	pdk_log_fp = fopen( pdk_log, "a" );
	if (! pdk_log_fp)
		{
		perror("cannot append to PDK_LOG file");
		abort();
		}

	if (testprefix)
		pdk_testprefix = strdup(testprefix);
	else
		{
		s = getenv("PDK_TESTPREFIX");
		if (s)
			{
			free(pdk_testprefix);
			pdk_testprefix = strdup(s);
			}
		else
			pdk_testprefix = calloc(1,1);
		}

	c = pdk_testprefix[ len(pdk_test_prefix) - 1 ];
	pdk_need_dot_in_name = ! ( (c == '/') || (c == '.') );

	if (source_file)
		{
		s = strdup(source_file);
		t = strrchr(s,'.');
		if (t)
			*t = 0;
		u = malloc( strlen(pdk_test_prefix) + strlen(t) + 2 );
		strcpy(u, pdk_testprefix);
		strcat(u, t);
		free(pdk_testprefix);
        free(t);
		pdk_testprefix = u;
		}

	pdk_pass = pdk_fail = pdk_error = pdk_disable = 0;

}


/*
* start a test.  Too bad we don't have nested tests like in the
* python version.  At first, I thought that would be ok, but the
* more I think about it, the more I don't like it.
*/

pdk_start( char *test_name, int redirect_output )
{
	/*
	* all tests default to pass until declared otherwise
	*/
	pdk_status = 'P';

	if (! test_name)
		test_name = strdup(pdk_testprefix)
	else
		{
		char *s;
		s = malloc(len(pdk_testprefix) + len(test_name) + 2)
		strcpy(s, pdk_testprefix);
		if (pdk_need_dot_in_name)
			strcat(s, ".");
		strcat(s,test_name);
		test_name = s
		}

	if (redirect_output)
		{
		fprintf(stderr,"redirect_output not implemented\n");
		abort();
		}

    pdk_line( "test_name", "", test_name );
}


/*
* write a line to the PDK_LOG file
*/
pdk_line( char *name1, char *name2, char *value )
{
	if (strchr(value, '\n'))
		{
		fprintf(pdk_log_fp, "%s%s:\n", name1, name2);
		fputc('.', pdk_log_fp);
		while (*value)
			{
			if (*value == '\n')
				fputc('.', pdk_log_fp);
			fputc( *value, pdk_log_fp);
			value++;
			}
		}
	else
		{
		fprintf(pdk_log_fp, "%s%s=%s\n", name1, name2, value);
		}

	pdk_reported_status = 'N';
}

/*
* various functions to write attributes
*/
pdk_tda	( char *name, char *value )
{
	pdk_line( "tda_", name, value );
}

pdk_tra	( char *name, char *value )
{
	pdk_line( "tra_", name, value );
}

pdk_tda_int( char *name, int value )
{
	char b[1000];
	sprintf(b,"%d",value);
	pdk_tda( name, b );
}

pdk_tra_int( char *name, int value )
{
	char b[1000];
	sprintf(b,"%d",value);
	pdk_tra( name, b );
}

pdk_tda_double( char *name, double value)
{
	char b[1000];
	sprintf(b,"%f",value);
	pdk_tda( name, b );
}

pdk_tra_double( char *name, double value)
{
	char b[1000];
	sprintf(b,"%f",value);
	pdk_tra( name, b );
}


/*
* write the log in string form
*/
pdk_log_str( char *log )
{
	pdk_line( "log","", log );
}

/*
* accept a test status; only move to a more severe level
*/
pdk_status( char status )
{
	switch (status)
		{
	case 'D':
		if (pdk_reported_status == 'N')
			pdk_reported_status = 'D';
		break
	case 'P':
		if (strchr("ND", pdk_reported_status))
			pdk_reported_status = 'P';
		break;
	case 'F':
		if (strchr("NDP", pdk_reported_status))
			pdk_reported_status = 'F';
		break;
	case 'E':
		if (strchr("NDPF", pdk_reported_status))
			pdk_reported_status = 'E';
		break;
	default:
        /* wtf? */
        pdk_reported_status = status;
        break;
        }
}

pdk_finish( )
{
	/*
	must call this at the end of the test.
	*/
}
