#
# pandokia - a test reporting and execution system
# Copyright 2011, 2014, Association of Universities for Research in Astronomy (AURA)
#
# mysql database driver
#

__all__ = [
    'db_module',
    'db_driver',
    'PandokiaDB',
    'thread_safe',
]

import MySQLdb as db_module
import time

# from dbapi
thread_safe = db_module.threadsafety

import pandokia.db

# debugging
debug = False

try:
    import StringIO
except ImportError:
    import io as StringIO

import os

# use this when something is so specific to the database that you
# can't avoid writing per-database code
db_driver = 'mysqldb'

import re


class PandokiaDB(pandokia.db.where_dict_base):

    IntegrityError = db_module.IntegrityError
    ProgrammingError = db_module.ProgrammingError
    OperationalError = db_module.OperationalError
    DatabaseError = db_module.DatabaseError

    # name of this driver.  could be a constant.
    pandokia_driver_name = __module__.split('db_')[1]

    db = None

    def __init__(self, access_arg):
        self.db_access_arg = access_arg
        # the mysqldb package I have installed chokes if you give
        # it unicode strings.  So convert any unicode back to str.
        for x in access_arg:
            if isinstance(access_arg[x], str):
                self.db_access_arg[str(x)] = str(access_arg[x])
            else:
                self.db_access_arg[str(x)] = access_arg[x]

    def open(self):
        # If the user explicitly calls open(), then we know they want
        # a connection.
        #
        # If we never had a connection, open one.  We're done.
        #
        if self.db is None:
            self.connect_with_retry()
            return

        # if we already have a connection, presumably the user has called
        # this open() again to ensure an open connection.  We can re-use
        # the connection if it is still open.  If it has timed out,
        # we open it again.  Notice that this call to open is protecting
        # against idle timeouts, not server crashes.
        try:
            self.db.ping()
            return
        except db_module.DatabaseError:
            self.db.close()
            self.db = None
            self.connect_with_retry()
            return
        # NOTREACHED

    def connect_with_retry(self, max_retries = 3):
        # connect to DB with retry on failure 
        # MySQLdb.OperationalError: (2005, "Unknown MySQL server host ...")
        retries = 0
        while retries < max_retries:
            retries+=1
            try:
                if retries <= 2: # for testing raise MySQLdb.OperationalError
                    raise db_module.OperationalError
                self.db = db_module.connect(** (self.db_access_arg))
                self.execute("SET autocommit=0")
                break
            except Exception as ex:
                print(str(ex))
                if retries == max_retries:
                    raise ex
            time.sleep(0.5)
        return

    def start_transaction(self):
        if self.db is None:
            self.open()
        self.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT")

    def commit(self):
        if self.db is None:
            return
        self.db.commit()

    def rollback(self):
        if self.db is None:
            return
        self.db.rollback()

    def rollback_or_reconnect(self):
        if self.db:
            try:
                self.db.rollback()
                return
            except self.OperationalError:
                print("rollback or reconnect - reconnect")
                # We know of
                # (2006, 'MySQL server has gone away')
                # (2013, 'Lost connection to MySQL server during query')
                # but any error will do, really.
                self.db.close()
                self.db = None
        self.open()

    #
    # explain the query plan using the database-dependent syntax
    #
    def explain_query(self, text, query_dict):
        if self.db is None:
            self.open()
        f = StringIO.StringIO()
        c = self.execute('EXPLAIN EXTENDED ' + text, query_dict)
        for x in c:
            f.write(str(x))
        return f.getvalue()

    #
    # execute a query in a portable way
    # (this capability not offered by dbapi)
    #

    _pat_from = re.compile(':([a-zA-Z0-9_]*)')

    _pat_to = '%(\\1)s '

    def execute(self, statement, parameters=[], db=None):
        if self.db is None:
            self.open()

        # convert the parameters, as necessary
        if isinstance(parameters, dict):
            # dict does not need to be converted
            pass
        elif isinstance(parameters, list) or isinstance(parameters, tuple):
            # list/tuple turned into a dict with string indexes
            tmp = {}
            for x in range(0, len(parameters)):
                tmp[str(x + 1)] = parameters[x]
            parameters = tmp
        elif parameters is None:
            parameters = []
        else:
            # no other parameter type is valid
            raise self.ProgrammingError

        # for mysql, convert :xxx to %(xxx)s
        statement = self._pat_from.sub(self._pat_to, statement)

        # create a cursor, execute the statement
        c = self.db.cursor()

        if debug:
            stmt_keys_start = statement.find('(')
            stmt_keys_stop = statement.find(')')
            stmt_keys = [ x for x in statement[stmt_keys_start + 1: stmt_keys_stop - 1].replace(',', '').strip().split()]
            pmtr_keys = [ int(x) for x in sorted(parameters.keys(), key=lambda i: int(i))]
            keymap = zip(pmtr_keys, stmt_keys)

            print('QUERY: {0}'.format(statement))
            print('PARAM:')
            for k, v in sorted(parameters.items(), key=lambda i: int(i[0])):
                for keys in keymap:
                    if int(k) == keys[0]:
                        k = keys[1]
                        break

                k = str(k)
                v = str(v)
                print('{0:<16s} ({1:>6d}) = {2}'.format(k, len(v), v))

            c.execute("SHOW WARNINGS")
            print("\n\n\n")

        # print parameters,"<br>"
        c.execute(statement, parameters)

        # return the cursor
        return c

    # how much table space is this database using
    # not portable to other DB
    def table_usage(self):
        '''sum of sizes from SHOW TABLE STATUS'''
        if self.db is None:
            self.open()
        c = self.db.cursor()
        c.execute("show table status")
        tables = 0
        indexes = 0
        for x in c:
            tables = tables + x[6]
            indexes = indexes + x[8]

        return tables + indexes

    # mysql does not use database sequences because it can do auto-increments
    # fields
    next = None

"""
When first installed, there is a user named "root" with no password.

update mysql.user set password = password('xxx') where ...whatever...

select user, host, password from mysql.user;

"""
