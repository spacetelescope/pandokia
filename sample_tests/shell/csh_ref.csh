#!/bin/csh

# This part is the actual test:

# output files named ".out" so it is easy to "rm *.out" if we want to
set outfile1=$0.1.out
set outfile2=$0.2.out

# do something to test
ls -l $0 > $outfile1
sum $0 > $outfile2

#end of test

# The rest of this is comparing the output/reference files, creating the
# okfile (for the flagok button on the gui), and computing the exit status

# alias for diff and cmp:

alias do_diff 'echo \!* ref/\!* >> $okfile ; diff \!* ref/\!* ; set st=( $status $st )'
alias do_cmp  'echo \!* ref/\!* >> $okfile ; cmp  \!* ref/\!* ; set st=( $status $st )'

set okfile=`basename $0`.okfile

rm -f $okfile

set st=( )

#
# put your file comparisons here
do_diff  $outfile1 
do_cmp   $outfile2

# now figure out what the final exit status should be - it is the
# worst of pass, fail, error
set teststatus=0

foreach x ( $st )
	switch ($x)
	case 0:
		breaksw
	case 1:
		if ( $teststatus == 0 ) set teststatus=1
		breaksw
	default:
		set teststatus=128
		breaksw
	endsw
end

echo teststatus $teststatus

exit $teststatus
