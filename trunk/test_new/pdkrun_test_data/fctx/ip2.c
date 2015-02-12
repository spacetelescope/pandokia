/*
* fctx can use the maker runner.  Here are the rules for linux/unix:
*
* $ cc -o ip2 -I$PDK_MAKER ip2.c 
* $ ./ip2
*
* These are in place tests that include attributes
*
*/

#include "pandokia_fct.h"

int a;

CL_FCT_BGN()
{
	FCT_QTEST_BGN(test_name_1)
	{
		fct_nlist_t *t;
		int x;
		printf("This test will pass\n");
		fct_chk(1);     // pass
		printf("prefix %s\n",pandokia_logger_object->pdk_prefix);
		printf("file %s\n",pandokia_logger_object->pdk_file);
		printf("basename %s\n",pandokia_logger_object->pdk_basename);
		printf("test name %s\n",fctkern_ptr__->ns.curr_test_name );
	}
	FCT_QTEST_END();

	FCT_QTEST_BGN(test_name_2)
	{
		pandokia_attr("tda","foo","one");
		pandokia_attr("tra","bar","two");
		pandokia_attr_double("tra","double",1.0/3.0);
		pandokia_attr_int("tra","double",55);
		pandokia_okfile("xfile");
		printf("This test will fail\n");
		fct_chk(0);     // fail
	}
        FCT_QTEST_END();

}
CL_FCT_END()

