
# do something
a=`expr 1 + 1`

# detect errors - e.g. expr not found
if [ $? != 0 ]
then
	echo expr exit status $?
	exit 128
fi

# check for right answer
if [ "$a" = "2" ]
then
	# pass
	exit 0
else
	# fail
	exit 1
fi
