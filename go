:
# This is a script I use to install pandokia at various places that I use here at stsci.  This is unlikely to be useful to you.

rm -rf build

case "$1"
in
pyssg)
	python setup.py -q install 
	cp stsci/config.py /usr/stsci/pyssgdev/Python-2.5.4/lib/python2.5/site-packages/pandokia/config.py
	# no top_level.html needed
	exit 0
	;;
ssbdev)
	there=/usr/stsci/ssbdev
	python setup.py -q install --home $there
	;;
'')
	n=33
	there=/ssbwebv1/data2/pandokia/c$n
	python setup.py -q install --home $there
	rm -f /eng/ssb/websites/ssb/pandokia/$n.cgi
	if [ ! -L /eng/ssb/websites/ssb/pandokia/c$n.cgi ]
	then
		echo make link
		ln -s $there/bin/pdk /eng/ssb/websites/ssb/pandokia/c$n.cgi
	fi
	if grep -q c$n.cgi  /eng/ssb/websites/ssb/index.html 
	then
		:
	else
		(
		cd /eng/ssb/websites/ssb
		sed 's?<!--PDK-->?<!--PDK--><a href="pandokia/c'$n'.cgi">c'$n'</a> <br> ?' < index.html > tmp
		mv -f tmp index.html
		)
	fi

	;;
esac

cp stsci/config.py $there/lib/python/pandokia/config.py

cp  stsci/top_level.html   $there/lib/python/pandokia/

