:
#

# load the helper functions

	. pdk_shell_runner_helper

# note the existence of an okfile and clear old contents away

	init_okfile

# This part is the actual test:

        # output files named ".out" so it is easy to "rm *.out" if we want to
        outfile1=$0.1.out
        outfile2=$0.2.out

        # make some output to test
        cat $0 > $outfile1
        sum $0 > $outfile2

# compare the output files to what we expected

	# comparing an output file with cmp
	testfile cmp  $outfile1

	# comparing an output file with diff
	testfile diff $outfile2

# return the test exit status

	exit $teststatus

