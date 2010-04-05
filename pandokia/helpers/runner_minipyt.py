#! python
#

import inspect
import traceback
import imp
import os.path
import time
import gc

# the pycode helper contains an object that writes pandokia report files
import pandokia.helpers.pycode as pycode

# there has to be a better way than this to get the type
# of a function.
def function ( ) :
	pass
function = type(function)

####
#### utility functions
####

#
# sort the list of tests into the order that they are defined in the file,
# at least for things that are statically defined.
# 
# the list is [ (name, ob), ... ]
#
# I got the method for doing this from
# http://lists.idyll.org/pipermail/testing-in-python/2010-January/002596.html

def _sort_fn(a) :
	(name,ob) = a
	code = getattr( ob, 'func_code', None )
	line = getattr( code, 'co_firstlineno', 0 )
	return line

def sort_test_list(l) :
	l.sort(key=_sort_fn)

####
#### actually run a test function
####

def run_test_function(rpt, mod, name, ob) :

	# blank out the tda/tra dictionaries for each test.
	# poke directly into the module to do it.
	mod.tda = { }
	mod.tra = { }

	# start gathering up the stdout/stderr for this test
	pycode.snarf_stdout()

	# run the test
	start_time = time.time()
	try :
		ob()
		status = 'P'
	except AssertionError :
		status = 'F'
		traceback.print_exc()
	except :
		status = 'E'
		traceback.print_exc()
	end_time = time.time()

	# collect the gathered stdout/stderr
	log = pycode.end_snarf_stdout()

	# write a report the the pandokia log file
	rpt.report( name, status, start_time, end_time, mod.tra, mod.tda, log )

####
#### actually run a test class
####

# There is a test name that corresponds to the whole class.  This gathers any
# result and/or error that comes from the class, but not from an individual
# test method.

def run_test_class( rpt, mod, name, ob ) :

	pycode.snarf_stdout()
	class_start_time = time.time()
	class_status = 'P'

	try :
		l = [ ]

		have_setup = 0
		have_teardown = 0

		for f_name, f_ob in inspect.getmembers(ob, inspect.ismethod) :

			# magic names to remember.  (The names are ugly
			# because they are copied from nose, which copied
			# them from unittest.)

			if f_name == 'setUp' :
				have_setup = 1
				continue

			if f_name == 'tearDown' :
				have_teardown = 1
				continue

			# if it has minipyt_test, that value is a flag
			# about whether it is a test or not.
			try :
				n = getattr(f_ob,'minipyt_test')
				if n :
					l.append( ( f_name, f_ob ) )
				continue
			except AttributeError :
				pass

			# if it does not have minipyt_test, we consider
			# other criteria that may make it count as a test.

			# '_*' is not a hest
			if f_name.startswith('_') :
				continue

			# if the method name looks like a test, it is a test
			if f_name.startswith('test') or f_name.endswith('test') :
				l.append( (f_name, f_ob) )

		# have a deterministic order
		sort_test_list(l)

		# do we need to make a new instance of the object for every test?
		new_object_every_time = not getattr(ob,'minipyt_shared',0)

		# if not, we need to make just one right now
		if not new_object_every_time :
			class_ob = ob()

		# for each test method on the object
		for f_name, f_ob in l :

			save_tda = { }
			save_tra = { }

			try :
				# gather up stdout/stderr for the test
				pycode.snarf_stdout()

				fn_start_time = time.time()

				# make the new object, if necessary
				if new_object_every_time :
					class_ob = ob()

				# blank out the tda/tra dictionaries for each test.
				class_ob.tda = save_tda
				class_ob.tra = save_tra

				# get a bound function that we can call
				fn = eval('class_ob.'+f_name)

				# call the test method
				try :
					if have_setup :
						class_ob.setUp()
					fn()
					fn_status = 'P'
				except AssertionError :
					fn_status = 'F'
					traceback.print_exc()
				except :
					fn_status = 'E'
					traceback.print_exc()

				# Always run teardown, no matter how the test worked out.
				try :
					if have_teardown :
						class_ob.tearDown()
				except :
					fn_status = 'E'
					traceback.print_exc()

				# The user may have replaced these
				# dictionaries, so we need to pick them
				# out of the object.  ( Copy them out of the object because it may be
				# gone by the time we need them. )
				save_tda = class_ob.tda
				save_tra = class_ob.tra

				# if we make a new object instance for
				# every test, dispose the old one now
				if new_object_every_time :
					del class_ob


			except AssertionError :
				fn_status = 'F'
				traceback.print_exc()
			except :
				fn_status = 'E'
				traceback.print_exc()

			fn_end_time = time.time()

			fn_log = pycode.end_snarf_stdout()

			rpt.report( name + '.' + f_name, fn_status, fn_start_time, fn_end_time, save_tda, save_tra, fn_log )

	except AssertionError :
		class_status = 'F'
		traceback.print_exc()
	except :
		class_status = 'E'
		traceback.print_exc()

	# this is the end of everything relating to the class.
	class_end_time = time.time()
	class_log = pycode.end_snarf_stdout() 

	rpt.report( name, class_status, class_start_time, class_end_time, { }, { }, class_log )
	

####
#### run a whole file of tests
####

# There is a test name that corresponds to the file.  This gathers any
# result and/or error that comes from the file, but not from an individual
# test.

def process_file( filename ) :

	# pandokia log entry object - writes the pandokia reports
	rpt = pycode.reporter( filename )

	# the module name is the basename of the file, without the extension
	module_name = os.path.basename(filename)
	module_name = os.path.splitext(module_name)[0]

	# gather up the stdout from processing the whole file.	individual
	# tests will suck up their own stdout, so it will not end up in
	# the file.
	pycode.snarf_stdout()

	file_start_time = time.time()
	file_status = 'P'

	try :

		# import the module
		module = imp.load_source( module_name, filename )

		print 'import succeeds'

		# look through the module for things that might be tests
		l = [ ]
		for name, ob in inspect.getmembers(module, inspect.isfunction) + inspect.getmembers(module, inspect.isclass) :

			# "_*" is never a test, no matter what it looks like
			if name.startswith('_') :
				continue

			try :
				# if it has minipyt_test, that value is a flag
				# about whether it is a test or not.
				n = getattr(ob,'minipyt_test')
				if n :
					l.append( (name, ob) )
				continue
			except AttributeError :
				# if it does not have minipyt_test, we consider
				# other criteria that may make it count as a test.
				pass

			# if the name looks like a test, it is a test
			if name.startswith('test') or name.endswith('test') :
				l.append( (name, ob) )

		# now we have a list of all the tests in the file

		# we have an opportunity to get them in the order they were
		# defined in the file, instead of alpha.  Just need to
		# figure out how.

		sort_test_list(l)

		for x in l :
			name, ob = x
			if type(ob) == function :
				print 'function', name
				run_test_function( rpt, module, name, ob )
			else :
				print 'class', name
				run_test_class( rpt, module, name, ob )

		print 'tests completed'

	except AssertionError :
		file_status = 'F'
		traceback.print_exc()
	except :
		file_status = 'E'
		traceback.print_exc()

	log = pycode.end_snarf_stdout()
	file_end_time = time.time()

	# the name for the report on the file as a whole is derived from
	# the file name. the report object is already set up to do this,
	# so we do not need to provide any more parts of the test name.
	rpt.report( None, file_status, file_start_time, file_end_time, { }, { }, log )

	rpt.close()


####
#### an entry point for pdk_python_runner to use
####

def main(argv) :
	for x in argv :
		process_file( x )


####
#### a main program so we can run this thing for debugging purposes
####

if __name__ == '__main__' :
	import sys
	main(sys.argv[1:])

