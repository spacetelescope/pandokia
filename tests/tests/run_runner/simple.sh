#!/bin/sh

# read in the helper library
. pdk_run_helper.sh

# this is outside any test
echo before P

# begin a test named "P".
test_start P
	# do some stuff here
	echo this is test P
	# report a test status - you can do this as many times as
	# you like; the resulting status will be the worst case that
	# was reported
	test_status P
# 
test_end

echo P - F

test_start F
	echo this is test F
	test_status F
test_end

echo F - E

test_start E
	echo this is test E
	test_status E
test_end

echo after E

test_start escalated_PF
	echo this test reported several status, worst is F
	test_status P
	test_status F
test_end

test_start escalated_FP
	echo this test reported several status, worst is F
	test_status F
	test_status P
test_end

test_start escalated_PF
	echo this test reported several status, worst is F
	test_status P
	test_status F
test_end

test_start escalated_PFE
	echo this test reported several status, worst is E
	test_status P
	test_status F
	test_status E
test_end

test_start escalated_EFP
	echo this test reported several status, worst is E
	test_status E
	test_status F
	test_status P
test_end

cleanup
