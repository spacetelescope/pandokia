#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA)
#

import re
import sys
import pandokia.common as common
import pandokia

try:
    import io as StringIO
except ImportError:
    import StringIO

exit_status = 0
line_count = 0
insert_count = 0
quiet = False
debug = False
default_record = dict()

# This dictionary contains an entry for every test run we have seen.
# For now, we are only using it to detect whether we know this name or not.
all_test_run = dict()
all_test_runs = dict()


def read_records(fileobj):
    global exit_status, default_record, debug

    found_any = 0
    result = default_record.copy()
    parsing_name = ''
    parsing_log = False

    # There is no elegant way to check for unicode failures without "trying".
    # There's also no elegant way to continue in the event we encounter a failure.
    # Simply check whether Python dies during its interal checks before we bother parsing
    # the entire file.
    with fileobj as data:
        d = data
        try:
            d.readline()
        except UnicodeDecodeError as e:
            print('UNICODE ERROR - Fix log file and import again')
            print('HINT: "{}" @ offset {} <-> {}'.format(e.reason, e.start, e.end))
            yield result

        for offset, line in enumerate(data):
            if parsing_log:
                if debug:
                    print('debug: {:d}: ingesting log data'.format(offset, line))
                name = parsing_name
                if line.startswith("\n") or line.startswith("\r\n"):
                    if debug:
                        print('debug: {:d}: End of log data'.format(offset))
                    parsing_log = False
                    continue

                if not line.startswith('.'):
                    print('Invalid input @ {:d}: '
                          'Missing prefix character in multi-line'.format(offset, name))
                    exit_status = 1
                    parsing_log = False
                    break

                result[parsing_name] += line
                continue

            line = line.strip()
            if debug:
                print('debug: {}: {}'.format(offset, line))


            if not line or line.startswith('#'):
                if debug:
                    print('debug: {:d}: skipping'.format(offset))
                continue

            # When we see data but don't find an END marker
            # (should not happen)
            if not line and found_any:
                print('Invalid input @ {:d}: '
                      'Missing "END"'.format(offset))
                exit_status = 1
                yield result
                continue

            # END of record marker?
            if line == 'END':
                if debug:
                    print('debug: {:d}: END found'.format(offset))
                if found_any:
                    yield result
                continue

            # Save new default record
            # "result" retains the same value, since it is now initialized to
            # default
            if line == 'SETDEFAULT':
                if debug:
                    print('debug: {:d}: SETDEFAULT found'.format(offset))
                if 'test_name' in result:
                    s = 'Invalid input @ {:d}: ' \
                        'test_name in SETDEFAULT {:s}'.format(offset, name)
                    raise Exception(s)

                default_record = result.copy()
                continue

            # Only happens at the start of a run - anything that came
            # earlier should be forgotten
            if line == 'START':
                if debug:
                    print('debug: {:d}: START found'.format(offset))
                result = dict()
                default_record = dict()
                found_any = 0
                continue

            # Look for lines of the form "name=value"
            if line.find('=') > -1:
                rec = line.split('=', 1)
                elements = len(rec)
                name = rec[0].lower()

                # Value needs to be converted to a string
                if elements > 1:
                    value = ''.join(rec[1:])

                if debug:
                    print('debug: {:d}: Generated key-pair from "{:s}"'.format(offset, line))
                result[name] = value
                found_any = 1
                continue

            # Look for lines of the form;
            #   name:
            #   .value
            #   .value
            if line.find(':') != -1:
                if debug:
                    print('debug: {:d}: Checking for log data'.format(offset))
                # Split on delimiter, removing empty records
                rec = [x for x in line.split(':', 1) if x]
                elements = len(rec)
                name = rec[0]

                if elements > 1:
                    print('Invalid input @ {:d}: '
                          'Data after colon in "{:s}"'.format(offset, line))
                    exit_status = 1

                if debug:
                    print('debug: {:d}: Parsing log'.format(offset))
                found_any = 1
                result[name] = ''
                parsing_name = name
                parsing_log = True
                continue

            # Handle the unlikely event of not finding any valid input.
            print('Invalid input @ {:d}: Unrecognized line {:s}'.format(offset, name))
            exit_status = 1


# this is a hideous hack from the earliest days of pandokia.  this class shouldn't
# even be here -- just a function that inserts a dict into the database

class test_result(object):

    def _lookup(self, name, default=None):
        if name in self.dict:
            return self.dict[name]
        if default is not None:
            return default
        self.missing.append(name)

    def __init__(self, dict):
        global all_test_run
        self.dict = dict
        self.missing = []

        self.test_run = self._lookup("test_run")
        all_test_run[self.test_run] = 1

        self.project = self._lookup("project")
        self.test_name = self._lookup("test_name")
        self.context = self._lookup("context", 'default')
        self.host = self._lookup("host", "unknown")
        self.location = self._lookup("location", "")
        self.test_runner = self._lookup("test_runner")
        self.status = self._lookup("status")
        self.log = self._lookup("log", "")
        self.start_time = self._lookup("start_time", '')
        self.end_time = self._lookup("end_time", '')
        self.has_okfile = 'tda__okfile' in dict

        # no space in test name
        if '\n' in self.test_name:
            self.test_name = self.test_name.replace('\n', '_')
        if ' ' in self.test_name:
            self.test_name = self.test_name.replace(' ', '_')
        if '\t' in self.test_name:
            self.test_name = self.test_name.replace('\t', '_')
        # avoid excess / or . at beginning (easy to do by mistake in some
        # runners)
        while self.test_name.startswith('/') or self.test_name.startswith('.'):
            self.test_name = self.test_name[1:]

        try:
            if self.start_time != '':
                self.start_time = common.parse_time(self.start_time)
                self.start_time = common.sql_time(self.start_time)
        except ValueError:
            print("")
            print("INVALID START TIME, line %d" % line_count)

        try:
            if self.end_time != '':
                self.end_time = common.parse_time(self.end_time)
                self.end_time = common.sql_time(self.end_time)
        except ValueError:
            print("")
            print("INVALID END TIME, line %d" % line_count)

        self.tda = {}
        self.tra = {}

        for x in dict:
            if x.startswith("tda_"):
                self.tda[x[4:]] = self._lookup(x)
            if x.startswith("tra_"):
                self.tra[x[4:]] = self._lookup(x)

        if len(self.missing) > 0:
            print("FIELDS MISSING %s %d" % (self.missing, line_count))
            exit_status = 1

    def try_insert(self, db, key_id):
        if self.has_okfile:
            okf = 'T'
        else:
            okf = 'F'
        if key_id:
            ss = 'key_id, '
            ss1 = ', :13'
            parm = [key_id]
        else:
            parm = []
            ss = ''
            ss1 = ''
        parm += [self.test_run,
                 self.host,
                 self.project,
                 self.test_name,
                 self.context,
                 self.status,
                 self.start_time,
                 self.end_time,
                 self.location,
                 self.attn,
                 self.test_runner,
                 okf]
        return db.execute(
            "INSERT INTO result_scalar ( %s test_run, host, project, test_name, context, status, start_time, end_time, location, attn, test_runner, has_okfile ) values "
            " ( :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12 %s )" %
            (ss, ss1), parm)

    def insert(self, db):

        global insert_count

        if len(self.missing) > 0:
            print("NOT INSERTED DUE TO MISSING FIELDS %s %s %d" %
                  (self.missing, self.test_name, line_count))
            exit_status = 1
            return

        if self.test_name.endswith("nose.failure.Failure.runTest"):
            print("NOT INSERTING %s, (not an error)" % self.test_name)
            print("Can we have the nose plugin stop reporting these?")
            return

        self.test_name = self.test_name.replace("//", "/")

        # compute attention automatically
        if self.status == 'P':
            self.attn = 'N'
        else:
            self.attn = 'Y'

        # but use the value in the input record if there is one
        self.attn = self._lookup("attn", self.attn)

        # if this database engine does not have a usable auto-increment
        # field, get a key_id from the sequence in the database
        if db.next:
            key_id = db.next('sequence_key_id')
        else:
            key_id = None

        try:
            res = self.try_insert(db, key_id)
            if not db.next:
                key_id = res.lastrowid
            insert_count += 1

        except db.IntegrityError as e:
            db.rollback()
            # if it is already there, look it up - if it is status 'M' then we are just now receiving
            # a record for a test marked missing.  delete the one that is 'M'
            # and insert it.
            c = db.execute(
                "select status from result_scalar where "
                "test_run = :1 and host = :2 and context = :3 and project = :4 and test_name = :5 and status = 'M'",
                (self.test_run,
                 self.host,
                 self.context,
                 self.project,
                 self.test_name))
            x = c.fetchone()
            if x is not None:
                db.execute(
                    "delete from result_scalar where "
                    "test_run = :1 and host = :2 and context = :3 and project = :4 and test_name = :5 and status = 'M'",
                    (self.test_run,
                     self.host,
                     self.context,
                     self.project,
                     self.test_name))
                res = self.try_insert(db, key_id)
                insert_count += 1
            else:
                raise e

        for x in self.tda:
            db.execute(
                "INSERT INTO result_tda ( key_id, name, value ) values ( :1, :2, :3 )",
                (key_id,
                 x,
                 self.tda[x]))

        for x in self.tra:
            db.execute(
                "INSERT INTO result_tra ( key_id, name, value ) values ( :1, :2, :3 )",
                (key_id,
                 x,
                 self.tra[x]))

        # BUG: this is stupid.  Do something about it.

        if len(self.log) > 990000:
            # hack around mysql's "max_allowed_packet" limit.  Somehow this still results in
            # /ssbwebv1/data2/pandokia/c38/lib/python/pandokia/db_mysqldb.py:115: Warning: Data truncated for column 'log' at row 1
            # but at least it doesn't crash the import...
            self.log = self.log[
                0:990000] + '\n\n\nLOG TRUNCATED BECAUSE MYSQL CANNOT HANDLE RECORDS > 1 MB\n'
            print("LOG TRUNCATED: key_id=%d" % key_id)

        db.execute("INSERT INTO result_log ( key_id, log ) values ( :1, :2 )",
                   (key_id, self.log))

        db.commit()

        if self.test_run not in all_test_runs:
            # if we don't know about this test run,
            try:
                # add it to the list of known test runs
                db.execute(
                    "INSERT INTO distinct_test_run ( test_run, valuable ) VALUES ( :1, 0 )",
                    (self.test_run,
                     ))
                db.commit()
            except db.IntegrityError:
                db.rollback()
            # remember that we saw it so we don't have to touch the database
            # again
            all_test_runs[self.test_run] = 1


def run(argv, hack_callback=None):
    global insert_count, quiet, debug
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('-H', '--host')
    parser.add_argument('-c', '--context', default='unk')
    parser.add_argument('-p', '--project')
    parser.add_argument('--test-runner')
    parser.add_argument('--test-run')
    parser.add_argument('filename', nargs='*', type=argparse.FileType('r'), default=[sys.stdin])
    args = parser.parse_args(argv)

    pdk_db = pandokia.cfg.pdk_db

    default_test_runner = ''
    insert_count = 0
    line_count = 0
    duplicate_count = 0
    quiet = args.quiet
    debug = args.debug

    for handle in args.filename:
        if not quiet:
            print("FILE: %s" % handle.name)

        for x in read_records(handle):
            if "test_run" not in x:
                x["test_run"] = args.test_run
            if "context" not in x:
                x["context"] = args.context
            if "host" not in x:
                x["host"] = args.host
            if "project" not in x:
                x["project"] = args.project
            if "test_runner" not in x:
                x["test_runner"] = args.test_runner

            # bug: remove this when the old nose plugin is no longer running
            # around
            if "name" in x:
                x["test_name"] = x["name"]
                del x["name"]

            #
            if 'test_name' not in x:
                # should not happen, but don't want to let it kill the import
                print("warning: no test name on line: %4d" % line_count)
                print("   %s" % [zz for zz in x])
                continue

            if x["test_name"].endswith(".xml") or x["test_name"].endswith(".log"):
                x["test_name"] = x["test_name"][:-4]

            rx = test_result(x)

            # the hack_callback allows us to insert something to modify the
            # record before we insert it; we also have the option of ignoring
            # the record.
            if hack_callback:
                if not hack_callback(rx):
                    continue
            try:
                rx.insert(pdk_db)
            except pdk_db.IntegrityError:
                duplicate_count += 1

            pdk_db.commit()

    result_str = '{:d} records inserted'.format(insert_count)
    if duplicate_count:
        result_str += ' ({:d} skipped)'.format(duplicate_count)

    if not quiet:
        print(result_str)

    # could use all_test_run here to clear the cgi cache
    sys.exit(exit_status)


def hack_import(args):
    run(args, hack_callback=pyetchack)


def pyetchack(arg):
    # for a hack_callback, arg is a dict.  Modify the dict in any way
    # that you like to change what gets imported.  Return true if
    # the record should be imported, false if it should be ignored.

    n = arg.test_name

    if not n.endswith('.all'):
        return False

    arg.test_name = arg.test_name.replace(".peng.all", "")
    return True
