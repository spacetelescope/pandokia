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
	set n=38
	set there=/ssbwebv1/data2/pandokia/c$n
	python setup.py -q install --home $there
	rm -f /eng/ssb/websites/ssb/pandokia/$n.cgi
	if ( ! -f /eng/ssb/websites/ssb/pandokia/c$n.cgi ) then
		echo make link
		ln -s $there/bin/pdk /eng/ssb/websites/ssb/pandokia/c$n.cgi
	endif

	if ( { grep -q c$n.cgi  /eng/ssb/websites/ssb/index.html }  ) then
		echo ''
	else
		cd /eng/ssb/websites/ssb
		sed 's?<!--PDK-->?<!--PDK--><a href="pandokia/c'$n'.cgi">c'$n'</a> <br> ?' < index.html > tmp
		mv -f tmp index.html
	endif

	cp stsci/config.py $there/lib/python/pandokia/config.py

	cp  stsci/top_level.html   $there/lib/python/pandokia/

	breaksw

endsw

