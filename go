#!/bin/csh
# This is a script I use to install pandokia at various places that I use here at stsci.  This is unlikely to be useful to you.
echo $path

set n=84

rm -rf build

unsetenv PYTHONPATH

switch ( "$1" )

case iraf:
	iraf $2
	set which_python=`which python`
	set python_bin=`dirname $which_python`
        set libdir=`echo $PYTHONPATH  | tr ':' '\n' | grep -v stsci_python | tail -1 `
        rm -rf $libdir/pandokia*
	python setup.py -q install --install-lib $libdir
        cat stsci/config.py >> $libdir/pandokia/default_config.py
        echo CONFIG $libdir/pandokia/default_config.py
	# no top_level.html needed
	cp  stsci/top_level.html   $libdir/pandokia/top_level.html
	cp  /eng/ssb/web/shunit/shunit2 $python_bin
	ls -ld $python_bin/shunit2
	cp /eng/ssb/web/shunit/shunit2_test_helpers $python_bin
	exit 0

case irafx:
	irafx $2
	set which_python=`which python`
	set python_bin=`dirname $which_python`
        set libdir=`echo $PYTHONPATH  | tr ':' '\n' | grep -v stsci_python | tail -1 `
        rm -rf $libdir/pandokia*
	python setup.py -q install --install-lib $libdir
        cat stsci/config.py >> $libdir/pandokia/default_config.py
        echo CONFIG $libdir/pandokia/default_config.py
	# no top_level.html needed
	cp  stsci/top_level.html   $libdir/pandokia/top_level.html
	cp  /eng/ssb/web/shunit/shunit2 $python_bin
	ls -ld $python_bin/shunit2
	cp /eng/ssb/web/shunit/shunit2_test_helpers $python_bin
	exit 0

case irafdev:
	irafdev $2
	set which_python=`which python`
	set python_bin=`dirname $which_python`
        set libdir=`sh -c 'echo $PYTHONPATH'  | tr ':' '\n' | grep -v stsci_python | tail -1 `
        if ( X$libdir == X ) then
                echo libdir blank - derive from python version
                set version=`python -V |& awk '{ print $2 }' `
                echo V=$version
                set libdir='/usr/stsci/pyssgdev/'$version
        endif
        echo LIBDIR IS $libdir
        rm -rf $libdir/pandokia*
        python setup.py -q install --install-lib $libdir
        cat stsci/config.py >> $libdir/pandokia/default_config.py
        echo CONFIG $libdir/pandokia/default_config.py
	# no top_level.html needed
	cp  stsci/top_level.html   $libdir/pandokia/top_level.html
	cp  /eng/ssb/web/shunit/shunit2 $python_bin
	ls -ld $python_bin/shunit2
	cp /eng/ssb/web/shunit/shunit2_test_helpers $python_bin
	exit 0

case "":
	set which_python=`which python`
	switch ( $which_python )
	case /usr/stsci/*:
		echo ''
		breaksw
	default:
		echo 'not using the right python'
		which python
		exit 1
		breaksw
	endsw

	set there=/ssbwebv1/data2/pandokia/c$n
        rm -rf $there/lib/python/pandokia*
	python setup.py -q install --home $there

	cp  /eng/ssb/web/shunit/shunit2 $there/bin
	cp /eng/ssb/web/shunit/shunit2_test_helpers $there/bin

	rm -f /eng/ssb/websites/ssb/pandokia/$n.cgi
	if ( ! -f /eng/ssb/websites/ssb/pandokia/c$n.cgi ) then
		echo make link
		ln -s $there/bin/pdk /eng/ssb/websites/ssb/pandokia/c$n.cgi
	endif

	if ( { grep -q c$n.cgi  /eng/ssb/websites/ssb/index.html }  ) then
		echo ''
	else
		set id=/eng/ssb/websites/ssb
		sed 's?<\!--PDK-->?<\!--PDK--><a href="pandokia/c'$n'.cgi">c'$n'</a> <br> ?' < $id/index.html > tmp 
		cp tmp $id/index.html
		ls -l $id/index.html
	endif

	cat stsci/config.py >> $there/lib/python/pandokia/default_config.py

	set pass=$there/lib/python/pandokia/alt_password
	if ( ! -f $pass ) then
		echo 'Must set password in '$pass
	endif

	cp  stsci/top_level.html   $there/lib/python/pandokia/

	chgrp -R ssb $there

	breaksw

endsw

