#!/bin/sh
#
# usage:
#	. pdk_run_helper.sh
#	main_start
#		test_start NAME
#			init_okfile
#			testfile diff my_output file
#			test_status F
#			test_status $exit_code
#		test_end   NAME STATUS
#	main_end STATUS
#

. pdk_shell_runner_helper

pdk_tmpfile=pdk.runner.tmp
pdk_test_name=none

datefmt='+%Y-%m-%d %H:%M:%S'
base_test_name=${PDK_TESTPREFIX}`echo $PDK_FILE | sed 's/\.[^.]*$//'`

test_start() {
	pdk_test_name=$1
	(
	echo "test_name=$base_test_name"/$1
	echo "start_time="`date "$datefmt"`
	) >> $PDK_LOG
	# pdk_okfile and pdk_okfile_dir will be created by init_okfile
	# if it is used within the test
	pdk_pokfile=okfile/$base_test_name.$pdk_test_name.okfile
	pdk_okfile_dir=okfile
	pdk_teststatus=0
	exec > $pdk_tmpfile 2>&1
}

test_status() {
	case "$1"
	in
	P)	
		:
		;;
	F)	
		if [ $pdk_teststatus -eq 0 ]
		then
			pdk_teststatus=1
		fi
		;;
	E)
		pdk_teststatus=128
		;;
	[0-9]*)
		if [ $pdk_teststatus -lt $1 ]
		then
			pdk_teststatus=$1
		fi
		;;
	*)
		pdk_teststatus=128
		echo invalid test status parameter:
		echo $1
		;;
	esac
}

test_end() {

	if [ $pdk_teststatus -ge 128 ]
	then
		stat=E
	else
		if [ $pdk_teststatus -gt 0 ]
		then
			stat=F
		else
			stat=P
		fi
	fi

	exec >> $pdk_tmpfile 2>&1
	(
	echo 'end_time='`date "$datefmt"`
	echo 'status='$stat
	echo 'log:'
	sed 's/^/./' < $pdk_tmpfile
	# one blank line in case $pdk_tmpfile does not end with newline
	echo ''         
	# one blank line terminates the log: entry.
	echo '' 
	# end the record for this test.
	echo END
	)  >> $PDK_LOG
}


cleanup() {
	rm -f $pdk_tmpfile
}
