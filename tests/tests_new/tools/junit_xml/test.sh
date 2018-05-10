. pdk_shell_runner_helper

# these tests convert sample junit/xml files that I think were
# produce by actual JUnit java code.  They were created by
# running the junittopdk converter on them and then manually
# inspecting the output to see that it looks like what I
# expect.  The output was stored as reference files in ref/

simple() {
	init_okfile $_shunit_test_
	junittopdk testresults/$1 > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

testAssuranceTest() {
	simple TEST-net.cars.documents.AssuranceTest.xml
}

testBougieTest() {
	simple TEST-net.cars.engine.BougieTest.xml
}

testCarburateurTest() {
	simple TEST-net.cars.engine.CarburateurTest.xml
}

testDelcoTest() { 
	simple TEST-net.cars.engine.DelcoTest.xml
}

testDemareurTest() {
	simple TEST-net.cars.engine.DemareurTest.xml
}

testMoteurTest() {
	simple TEST-net.cars.engine.MoteurTest.xml
}

testPistonTest() {
	simple TEST-net.cars.engine.PistonTest.xml
}

testBootTest() {
	simple TEST-net.cars.engine.diagnostics.selftest.computer.backup.BootTest.xml
}

# these tests are checking that various flags work

test_help() {
	init_okfile $_shunit_test_
	junittopdk -h > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

ffile=testresults/TEST-net.cars.documents.AssuranceTest.xml

test_test_run() {
	init_okfile $_shunit_test_
	junittopdk -test_run My_TEST_RUN $ffile > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

test_host() {
	init_okfile $_shunit_test_
	junittopdk -host MY_HOST $ffile > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

test_context() {
	init_okfile $_shunit_test_
	junittopdk -context MY_CONTEXT $ffile > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

test_project() {
	init_okfile $_shunit_test_
	junittopdk -project MY_PROJECT $ffile > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

test_prefix() {
	init_okfile $_shunit_test_
	junittopdk -prefix /arf/arf $ffile > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

test_all_flags() {
	init_okfile $_shunit_test_
	junittopdk -test_run MY_TEST_RUN -host MY_HOST -context MY_CONTEXT  -project MY_PROJECT -prefix /arf/arf $ffile > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

# try converting py.test and nose output

test_nose() {
	init_okfile $_shunit_test_
	echo RUNNING nosetests TO GET AN XML FILE
	nosetests --with-xunit --xunit-file=tmp/nose.xml nose_tests.py
	echo CONVERTING XML TO PDK
	junittopdk tmp/nose.xml | grep -v ^start_time > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

test_pytest() {
	init_okfile $_shunit_test_
	echo RUNNING py.test TO GET AN XML FILE
	py.test --junitxml=tmp/pytest.xml pytest_tests.py
	echo CONVERTING XML TO PDK
	junittopdk tmp/pytest.xml | grep -v ^start_time > out/$_shunit_test_
	testfile diff out/$_shunit_test_
}

# simple errors

test_nofile() {
	echo RUN
	if junittopdk no_such_file 
	then
		fail "should have indicated error"
	fi
}

