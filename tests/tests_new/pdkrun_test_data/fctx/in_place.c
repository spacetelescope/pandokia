/*
* fctx can use the maker runner.  Here are the rules for linux/unix:
*
* $ cc -o in_place -I$PDK_MAKER in_place.c 
* $ ./in_place
*
*/

#include "pandokia_fct.h"

CL_FCT_BGN()
{
	FCT_QTEST_BGN(test_name_1)
	{
		printf("This test will pass\n");
		fct_chk(1);     // pass
	}
	FCT_QTEST_END();

	FCT_QTEST_BGN(test_name_2)
	{
		printf("This test will fail\n");
		fct_chk(0);     // fail
	}
        FCT_QTEST_END();

}
CL_FCT_END()

