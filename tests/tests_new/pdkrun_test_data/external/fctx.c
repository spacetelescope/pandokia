/*
* cc -I`pdk maker` -o fctx fctx.c
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

