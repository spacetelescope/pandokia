:

# The name of this test, used in various file names
tname=`basename $0 .sh`

# directories we will use
mkdir -p output ref okfile

# we have one output file, which is okifyable
echo tda__okfile=`pwd`/okfile/$tname >> $PDK_LOG
echo "../output/$tname ../ref/$tname" > okfile/$tname
echo "../output/$tname.dump ../ref/$tname.dump" >> okfile/$tname

# THE TEST
echo PERFORM IMPORT
pdk import data/PDK* > output/$tname

pdk dump_table result_scalar > output/$tname.dump

# compare to what we expect
echo OUTPUT
diff -C 3 ref/$tname output/$tname
r=$?

echo TABLE
diff -C 3 ref/$tname.dump output/$tname.dump
r=$r$?

exit $r
