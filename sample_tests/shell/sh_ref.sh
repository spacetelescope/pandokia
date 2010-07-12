:
#

# load the helper functions
. pdk_shell_runner_helper

# output files named ".out" so we can "rm *.out" later
outfile1=$0.1.out
outfile2=$0.2.out

# do something
ls -l $0 > $outfile1
sum $0 > $outfile2


# compare the output files to what we expected

testfile diff $outfile1

testfile cmp $outfile2

# report the test result by our exit status

echo teststatus $teststatus

exit $teststatus
