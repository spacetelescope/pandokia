import os
import pandokia.common as c

import sys
sys.stdout=open("/dev/tty","w")

parse_time = c.parse_time
sql_time = c.sql_time

os.environ['TZ'] = 'EST5EDT'

def t_parse_time() :
    """
    >>> parse_time('Thu Jan 14 11:55:41 2010')
    datetime.datetime(2010, 1, 14, 11, 55, 41)

    >>> parse_time('1263488141')
    datetime.datetime(2010, 1, 14, 11, 55, 41)

    >>> parse_time('2010-01-14 11:55:41')
    datetime.datetime(2010, 1, 14, 11, 55, 41)

    >>> parse_time('1263488141.25')
    datetime.datetime(2010, 1, 14, 11, 55, 41, 250000)

    >>> parse_time('2010-01-14 11:55:41.25')
    datetime.datetime(2010, 1, 14, 11, 55, 41, 250000)

    >>> parse_time('2010-1-4 1:5:1.25')
    datetime.datetime(2010, 1, 4, 1, 5, 1, 250000)

    >>> parse_time('Thu Jan  4  1:05:01 2010')
    datetime.datetime(2010, 1, 4, 1, 5, 1)

    >>> parse_time('Thu Jan 4 1:5:1 2010')
    datetime.datetime(2010, 1, 4, 1, 5, 1)

    >>> parse_time('2010-01-14 11:55:41.25')
    datetime.datetime(2010, 1, 14, 11, 55, 41, 250000)

    >>> parse_time('1263488141.2512341234')
    datetime.datetime(2010, 1, 14, 11, 55, 41, 251234)

    >>> parse_time('2010-01-14 11:55:41.2512341234')
    datetime.datetime(2010, 1, 14, 11, 55, 41, 251234)
    """

def t_sql_time() :
    '''
    >>> d=parse_time('2010-01-14 11:55:41.251234')
    >>> sql_time(d)
    '2010-01-14 11:55:41.251234'
    '''
