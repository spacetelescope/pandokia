import pandokia.helpers.minipyt as mpt

def test_p() :
	print "We are here!"
	assert True

def test_f() :
	print "We are here!"
	assert False

def test_e() :
	print "We are here!"
	raise Exception('Bomb')

@mpt.test
def decorated() :
	print "We are here!"
	assert True

@mpt.notest
def test_not_a_test() :
	print "We are here!"
	# there should be no test report for this one
	raise Exception('Bomb')

@mpt.test
def fn_with_tda() :
	print "We are here!"
	tda['tda_1'] = 1
	tda['tda_2'] = 2


@mpt.test
def fn_with_tra() :
	print "(Do you hear a Who?)"
	tra['tra_1'] = 1
	tra['tra_2'] = 2

@mpt.test
def fn_with_attributes() :
	print "We are here!"
	tda['tda_1'] = 1
	tda['tda_2'] = 2
	tra['tra_1'] = 1
	tra['tra_2'] = 2
	assert False

print "We are here!"
