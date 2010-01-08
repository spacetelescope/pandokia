:
# This is a script I use to install pandokia at various places that I use here at stsci.  This is unlikely to be useful to you.

rm -rf build

case "$1"
in
pyssg)
	python setup.py -q install 
	echo 'dbdir="/ssbwebv1/data1/pandokia/database"' >> /usr/stsci/pyssgdev/Python-2.5.4/lib/python2.5/site-packages/pandokia/config.py
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


echo 'dbdir="/ssbwebv1/data1/pandokia/database"' >>  $there/lib/python/pandokia/config.py
cp  /ssbwebv1/data1/pandokia/c12/lib/python/pandokia/top_level.html   $there/lib/python/pandokia/

