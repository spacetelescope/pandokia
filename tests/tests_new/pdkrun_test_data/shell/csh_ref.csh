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

# log the existence of the output files

	sh -c ". pdk_shell_runner_helper ; okfile_entry $outfile1 $outfile2"

# diff each output file

	cmp $outfile1 ref/$outfile1
	set st1=$status

	diff $outfile2 ref/$outfile2
	set st2=$status

# collect the diff/cmp statuses into an exit code for pandokia

	sh -c ". pdk_shell_runner_helper ; cmp_status $st1 $st2 -e "
	exit $status

