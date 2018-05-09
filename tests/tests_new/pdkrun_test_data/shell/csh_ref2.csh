#!/bin/tcsh -f

# note the existence of an okfile and clear old contents away

        sh -c '. pdk_shell_runner_helper ; init_okfile '

# This part is the actual test:

	# output files named ".out" so it is easy to "rm *.out" if we want to
	set outfile1=$0.1.out
	set outfile2=$0.2.out

	# make some output to test
	cat $0 > $outfile1
	sum $0 > $outfile2

# diff each output file against the reference and find a pdk-compliant exit code

	sh -c ". pdk_shell_runner_helper ; csh_diff $outfile1 $outfile2 "
	exit $status
