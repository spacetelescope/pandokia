:

# The name of this test, used in various file names
tname=`basename $0 .sh`

# directories we will use
mkdir -p output ref okfile

# we have one output file, which is okifyable
echo tda__okfile=`pwd`/okfile/$tname >> $PDK_LOG
echo "../output/$tname.gen    ../ref/$tname.gen   " >  okfile/$tname
echo "../output/$tname.check  ../ref/$tname.check " >> okfile/$tname

# THE TEST
echo 'GEN EXPECTED'
pdk gen_expected daily test_report_1_a

echo 'DUMP EXPECTED TABLE'
pdk dump_table expected > output/$tname.gen

echo 'MOD TABLE'
pdk sql data/$tname.sql

echo 'CHECK EXPECTED'
pdk check_expected daily test_report_1_a > output/$tname.check

echo 'DUMP TABLE'
pdk dump_table result_scalar > output/$tname.check

# compare to what we expect
echo CMP GEN
diff -C 3 ref/$tname.gen output/$tname.gen
r=$?

echo ''
echo CMP CHECK

diff -C 3 ref/$tname.check output/$tname.check
r=$r$?

exit $r
