#!/bin/csh
# This is a script I use to install pandokia at various places that I use here at stsci.  This is unlikely to be useful to you.

rm -rf build

unsetenv PYTHONPATH

switch ( "$1" )

case iraf:
	iraf
	set libdir=$PYTHONPATH
	python setup.py -q install --install-lib $libdir
	cp stsci/config.py $libdir/pandokia/config.py
	# no top_level.html needed
	cp  stsci/top_level.html   $libdir/pandokia/top_level.html
	exit 0

case irafx:
	irafx
	set libdir=$PYTHONPATH
	python setup.py -q install --install-lib $libdir
	cp stsci/config.py $libdir/pandokia/config.py
	# no top_level.html needed
	cp  stsci/top_level.html   $libdir/pandokia/top_level.html
	exit 0

case irafdev:
	irafdev
	set libdir=$PYTHONPATH
	python setup.py -q install --install-lib $libdir
	cp stsci/config.py $libdir/pandokia/config.py
	# no top_level.html needed
	cp  stsci/top_level.html   $libdir/pandokia/top_level.html
	exit 0

case "":
	set n=40
	set there=/ssbwebv1/data2/pandokia/c$n
	find $there -name '*.pyc' -exec rm -f {} ';'
	python setup.py -q install --home $there
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

	cat stsci/config.py >> $there/lib/python/pandokia/config.py

	set pass=$there/lib/python/pandokia/password
	if ( ! -f $pass ) then
		echo 'Must set password in '$pass
	endif

	cp  stsci/top_level.html   $there/lib/python/pandokia/

	chgrp -R ssb $there

	breaksw

endsw

