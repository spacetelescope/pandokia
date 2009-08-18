:
#
set -e

a=`booga booga`
b=yes

if [ "$a" != "$b" ]
then
	echo pdk and pdkrun are not in the same directory
	exit 1
fi

exit 0
