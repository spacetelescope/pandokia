:
#
set -e

a=`which pdk`
a=`dirname $a`

echo found pdk in $a

echo looking for other pandokia commands

for x in pdk_shell_runner  pdknose  pdkrun  tbconv 
do
	b=`which $x`
	b=`dirname $b`

	if [ "$a" != "$b" ]
	then
		echo pdk and $x are not in the same directory
		exit 1
	else
		echo found $x
	fi
done

echo everything ok

exit 0
