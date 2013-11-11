import pandokia.helpers.pycode as pycode
import pandokia.helpers.runner_minipyt as runner_minipyt

def test_1() :
    print "test_1", runner_minipyt.currently_running_test_name
    with pycode.test("foo") :
        print "foo", runner_minipyt.currently_running_test_name
        with pycode.test("bar") :
            print "bar", runner_minipyt.currently_running_test_name

        print "foo", runner_minipyt.currently_running_test_name
    print "test_1", runner_minipyt.currently_running_test_name

