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
	there=/ssbwebv1/data1/pandokia/c13
	python setup.py -q install --home $there
	;;
esac

cp stsci/config.py $there/lib/python/pandokia/config.py

cp  stsci/top_level.html   $there/lib/python/pandokia/

