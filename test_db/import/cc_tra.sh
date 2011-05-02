:

# The name of this test, used in various file names
tname=`basename $0 .sh`

# directories we will use
mkdir -p output ref okfile

# we have one output file, which is okifyable
echo tda__okfile=`pwd`/okfile/$tname >> $PDK_LOG
echo "../output/$tname ../ref/$tname" > okfile/$tname

# THE TEST
python -c "import pandokia.db as d; d.table_to_csv('result_tra','output/$tname')"

# compare to what we expect
diff -C 3 ref/$tname output/$tname
r=$?

exit $r
