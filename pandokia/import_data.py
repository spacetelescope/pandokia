#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA)
#
from __future__ import print_function

import re
import sys
import hashlib
import pandokia.common as common
import pandokia

from six import StringIO

#Define some constants based on database schema.
#TRAs and TDAs have the same lengths; use TXA as shorthand.
maxlen_txa_name = 100
maxlen_txa_value = 1024

exit_status = 0

line_count = 0

default_record = { }

all_test_run = {  }

quiet = 0

def read_record(f) :
    global line_count, default_record

    ans = default_record.copy()
    found_any = 0

    while 1 :

        l = f.readline()
        line_count = line_count + 1
        if l == "" :
            # EOF - invalid if we saw any data (no END)
            # unremarkable otherwise
            if found_any :
                print("INVALID INPUT FILE - NO END %d" % line_count)
                exit_status = 1
                return ans
            else :
                return None

        l = l.strip()

        if l == "" :
            # blank lines allowed
            continue

        if l[0] == '#' :
            # comment lines allowed, even though we wouldn't normally
            # need them
            continue

        # end of record marker ?
        if l == "END" :
            if found_any :
                return ans
            continue

        if l == "SETDEFAULT" :
            if "test_name" in ans :
                s = "INVALID INPUT FILE - test_name in SETDEFAULT %s %d"%(name,line_count)
                print(s)
                raise Exception(s)
            # save the new default
            # ans retains the same value, since it is now initialized to the default
            default_record = ans.copy()
            continue

        # ABORT/RESET is obsolete usage - still here from early drafts of the spec
        if l == 'START' :
            # only happens at the start of a run - anything that came
            # earlier should be forgotten
            ans = { }
            default_record = { }
            found_any = 0
            continue

        # look for lines of the form "name=value"
        n = l.find("=")

        if n >= 0 :
            found_any = 1
            name = l[0:n]
            name = name.lower()
            value = l[n+1:]
            ans[name] = value
            found_any = 1
            continue

        # look for lines of the form
        #   name:
        #   .value
        #   .value
        #
        n = l.find(":")

        if n >= 0 :
            found_any = 1
            name = l[0:n]
            name = name.lower()
            value = l[n+1:]
            if value != "" :
                print("INVALID INPUT FILE - stuff after colon %s %s " % (name,line_count))
                exit_status = 1
            stuff = StringIO()
            while 1 :
                l = f.readline()
                line_count = line_count + 1
                if l == "" :
                    print("INVALID INPUT FILE - eof in multi-line",name,line_count)
                    exit_status = 1
                    break
                if l == "\n" or l == '\r\n':
                    # blank line marks end
                    break
                if l[0] != '.' :
                    print("INVALID INPUT FILE - missing prefix in multi-line",name,line_count)
                    exit_status = 1
                    break
                stuff.write(l[1:])
            # bug: this is hokey, but if you allow \0 in the string (in sqlite), the string gets truncated.
            ans[name] = stuff.getvalue().replace("\0","\\0")
            del stuff
            continue

        print("INVALID INPUT FILE - unrecognized line",l,line_count)
        exit_status = 1


insert_count = 0
reimport_count = 0
reimport_parm = { }

# This dictionary contains an entry for every test run we have seen.
# For now, we are only using it to detect whether we know this name or not.
all_test_runs = { }


# this is a hideous hack from the earliest days of pandokia.  this class shouldn't
# even be here -- just a function that inserts a dict into the database

class test_result(object):

    def _lookup(self,name,default=None) :
        if name in self.dict:
            return self.dict[name]
        if default != None :
            return default
        self.missing.append(name)

    def __init__(self, dictt) :
        self.dict = dictt
        self.missing = [ ]
        self.hash = ''

        self.test_run   = self._lookup("test_run")
        all_test_run[self.test_run] = 1

        self.project    = self._lookup("project")
        self.test_name  = self._lookup("test_name")
        self.context    = self._lookup("context",'default')
        self.custom     = self._lookup("custom",'')
        self.host       = self._lookup("host","unknown")
        self.location   = self._lookup("location","")
        self.test_runner= self._lookup("test_runner")
        self.status     = self._lookup("status")
        self.log        = self._lookup("log","")
        self.start_time = self._lookup("start_time",'')
        self.end_time   = self._lookup("end_time",'')
        self.has_okfile = 'tda__okfile' in self.dict

        # no space in test name
        if '\n' in self.test_name :
            self.test_name = self.test_name.replace('\n','_')
        if ' ' in self.test_name :
            self.test_name = self.test_name.replace(' ','_')
        if '\t' in self.test_name :
            self.test_name = self.test_name.replace('\t','_')
        # avoid excess / or . at beginning (easy to do by mistake in some runners)
        while self.test_name.startswith('/') or self.test_name.startswith('.') :
            self.test_name = self.test_name[1:]

        try :
            if self.start_time != '' :
                self.start_time = common.parse_time(self.start_time)
                self.start_time = common.sql_time(self.start_time)
        except ValueError :
            print("")
            print("INVALID START TIME, line",line_count)

        try :
            if self.end_time != '' :
                self.end_time = common.parse_time(self.end_time)
                self.end_time = common.sql_time(self.end_time)
        except ValueError :
            print("")
            print("INVALID END TIME, line",line_count)

        self.tda = { }
        self.tra = { }

        for x in self.dict:
            if x.startswith("tda_"):
                self.tda[x[4:]] = self._lookup(x)
            if x.startswith("tra_"):
                self.tra[x[4:]] = self._lookup(x)

        #print()
        #print('TDAs for %s are %s' %(self.test_name, str(self.tda)))
        #print('TRAs for %s are %s' %(self.test_name, str(self.tra)))
        #print()


        if len(self.missing) > 0 :
            print("FIELDS MISSING",self.missing,line_count)
            exit_status = 1

    def try_insert(self, db, key_id) :

        global reimport_count, reimport_parm

        if self.has_okfile :
            okf = 'T'
        else :
            okf = 'F'
        if key_id :
            ss = 'key_id, '
            ss1 = ', :14'
            parm = [key_id]
        else :
            parm = [ ]
            ss = ''
            ss1 = ''
        parm += [self.test_run, self.host, self.project, self.test_name, self.context, self.custom, self.status,
                  self.start_time, self.end_time, self.location, self.attn, self.test_runner, okf]

        hash_str = self.test_run+self.host+self.project+self.test_name+self.context+self.custom

        # return a string of length 32
        h = hashlib.md5(hash_str.encode())
        self.hash = h.hexdigest()
        parm += [self.hash]

        a = db.execute("select status from result_scalar where test_hash = :1", (self.hash,))
        y = a.fetchone()
        if y is not None:
            db.execute("delete from result_scalar where test_hash = :1", (self.hash,))
            reimport_count += 1
            reimport_parm[reimport_count] = parm
            if not quiet:
                print("WARNING: About to reimport the test result, please take a look at the reimport_tests.txt file after the import is done")


        return db.execute(
            "INSERT INTO result_scalar ( %s test_run, host, project, test_name, context, custom, status, start_time, end_time, location, attn, test_runner, has_okfile, test_hash ) values "
            " ( :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14 %s )" % (ss, ss1), parm)

    def insert(self, db) :

        global insert_count

        if len(self.missing) > 0 :
            print("NOT INSERTED DUE TO MISSING FIELDS", self.missing, self.test_name,line_count)
            exit_status = 1
            return

        if self.test_name.endswith("nose.failure.Failure.runTest"):
            print("NOT INSERTING ",self.test_name," (not an error)")
            print("Can we have the nose plugin stop reporting these?")
            return

        self.test_name = self.test_name.replace("//","/")

        # compute attention automatically
        if self.status == 'P':
            self.attn = 'N'
        else :
            self.attn = 'Y'

        # but use the value in the input record if there is one
        self.attn = self._lookup("attn",self.attn)

        # if this database engine does not have a usable auto-increment
        # field, get a key_id from the sequence in the database
        key_id = None
        if db.next :
            key_id = db.next('sequence_key_id')

        try :
            res = self.try_insert(db, key_id)
            if not db.next :
                key_id = res.lastrowid
            insert_count += 1

            assert key_id is not None, 'ERROR: key_id should not be None!'

        except db.IntegrityError as e:
            print('ERROR: we hit an integrity error in import_data.py! (key_id = %s)' %str(key_id))
            db.rollback()
            # if it is already there, look it up - if it is status 'M' then we are just now receiving
            # a record for a test marked missing.  delete the one that is 'M' and insert it.
            c = db.execute("select status from result_scalar where "
                "test_run = :1 and host = :2 and context = :3 and custom = :4 and project = :5 and test_name = :6 and status = 'M'",
                (self.test_run, self.host, self.context, self.custom, self.project, self.test_name )
            )
            x = c.fetchone()
            if x is not None :
                db.execute("delete from result_scalar where "
                    "test_run = :1 and host = :2 and context = :3 and custom = :4 and project = :5 and test_name = :6 and status = 'M'",
                    (self.test_run, self.host, self.context, self.custom, self.project, self.test_name )
                    )
                res = self.try_insert(db, key_id)
                insert_count += 1
            else :
                raise e

        #Check for legal lengths & truncate if necessary
        #Not handling this with try/except because there's no generic way to catch the
        #specific exception raised when a field is too long.
        for x in self.tda :
            if len(x) > maxlen_txa_name:
                #Truncate the middle so the name is more likely to be unique
                xsafe = x[0:40] + "..." + x[-40:]
            else:
                 xsafe = x

            tda_value = self.tda[x]
            if len(tda_value) > maxlen_txa_value:
                valsafe = tda_value[0:maxlen_txa_value-3] + "..."
            else:
                valsafe = tda_value

            db.execute("INSERT INTO result_tda ( key_id, name, value ) values ( :1, :2, :3 )" ,
                    ( key_id, xsafe, valsafe ) )


        for x in self.tra:

            if len(x) > maxlen_txa_name:
                #Truncate the middle so the name is more likely to be unique
                xsafe = x[0:40] + "..." + x[-40:]
            else:
                xsafe = x

            tra_value = self.tra[x]
            if len(tra_value) > maxlen_txa_value:
                valsafe = tra_value[0:maxlen_txa_value-3] + "..."
            else:
                valsafe = tra_value

            db.execute("INSERT INTO result_tra ( key_id, name, value ) values ( :1, :2, :3 )" ,
                 ( key_id, xsafe, valsafe ) )

        # BUG: this is stupid.  Do something about it.

        if len(self.log) > 990000 :
            # hack around mysql's "max_allowed_packet" limit.  Somehow this still results in
            # /ssbwebv1/data2/pandokia/c38/lib/python/pandokia/db_mysqldb.py:115: Warning: Data truncated for column 'log' at row 1
            # but at least it doesn't crash the import...
            self.log = self.log[0:990000] + '\n\n\nLOG TRUNCATED BECAUSE MYSQL CANNOT HANDLE RECORDS > 1 MB\n'
            print("LOG TRUNCATED: key_id=%d" % key_id)

        db.execute("INSERT INTO result_log ( key_id, log ) values ( :1, :2 )",
                ( key_id, self.log ) )

        db.commit()

        if not self.test_run in all_test_runs :
            # if we don't know about this test run,
            try :
                # add it to the list of known test runs
                db.execute("INSERT INTO distinct_test_run ( test_run, valuable ) VALUES ( :1, 0 )",(self.test_run,))
                db.commit()
            except db.IntegrityError :
                db.rollback()
            # remember that we saw it so we don't have to touch the database again
            all_test_runs[self.test_run] = 1


def run(args, hack_callback = None) :
    global insert_count, line_count, reimport_count, reimport_parm

    pdk_db = pandokia.cfg.pdk_db

    default_test_runner = ''
    default_context = 'unk'
    default_custom = ''
    for filename in args :
        if filename.startswith("-") :
            if '=' in filename :
                prefix,value=filename.split('=',1)
            else :
                prefix, value= ( filename, '' )
            if filename == '-q' :
                global quiet
                quiet=1
                continue
            if filename.startswith("-host=") :
                default_host = value
                continue
            if filename.startswith("-context=") :
                default_context = value
                continue
            if filename.startswith("-custom=") :
                default_custom = value
                continue
            if filename.startswith("-project=") :
                default_project = value
                continue
            if filename.startswith("-test_runner=") :
                default_test_runner = value
                continue
            if filename.startswith("-test_run=") :
                default_test_run = value
                continue
        if filename == '-' :
            f = sys.stdin
        else :
            f = open(filename,"r")

        insert_count = 0
        reimport_count = 0
        reimport_parm = { }
        line_count = 0

        print("FILE:",filename)

        while 1 :
            x = read_record(f)
            if x == None :
                break
            try :
                if not "test_run" in x :
                    x["test_run"] = default_test_run
                if not "context" in x :
                    x["context"] = default_context
                if not "custom" in x :
                    x["custom"] = default_custom
                if not "host" in x :
                    x["host"] = default_host
                if not "project" in x :
                    x["project"] = default_project
                if not "test_runner" in x :
                    x["test_runner"] = default_test_runner
            except Exception as e:
                print(e, line_count)
                continue

            # bug: remove this when the old nose plugin is no longer running around
            if "name" in x :
                x["test_name"] = x["name"]
                del x["name"]

            #
            if not 'test_name' in x :
                # should not happen, but don't want to let it kill the import
                print("warning: no test name on line: %4d" % line_count)
                print("   %s" % [zz for zz in x ])
                continue

            if x["test_name"].endswith(".xml") or x["test_name"].endswith(".log") :
                x["test_name"] = x["test_name"][:-4]


            rx = test_result(x)

            # the hack_callback allows us to insert something to modify the
            # record before we insert it; we also have the option of ignoring
            # the record.
            if hack_callback :
                if not hack_callback(rx) :
                    continue
            try :
                rx.insert(pdk_db)
                if not quiet:
                    print('Imported: {}'.format(rx.test_name))
            except pdk_db.IntegrityError as e:
                if debug:
                    print('IntegrityError: Cannot insert {} due to "{}"'.format(rx.test_name, e))
                if not quiet:
                    print('Skipped: {}'.format(rx.test_name))
                duplicate_count += 1

            pdk_db.commit()

        if f != sys.stdin :
            f.close()

        print("%d records\n\n"%insert_count)

        if reimport_count != 0:
            print("%s tests were re-imported during this run" % reimport_count)

            # split file path from filename and store the reimport_tests txt file
            # in the same place where the log is from
            file_path = ""
            if "/" in filename:
                file_path = filename.rsplit('/',1)[0]+"/"
                filename = filename.rsplit('/',1)[1]

            reimport_file = file_path+"reimport_tests_"+filename+".txt"
            print("See details in %s" % reimport_file)
            with open(reimport_file, 'w') as f:
                for key, value in reimport_parm.items():
                    f.write(str(key)+" : "+str(value)+"\n")

    # could use all_test_run here to clear the cgi cache

    sys.exit(exit_status)


def hack_import(args) :
    run(args, hack_callback = pyetchack)

def pyetchack(arg) :
    # for a hack_callback, arg is a dict.  Modify the dict in any way
    # that you like to change what gets imported.  Return true if
    # the record should be imported, false if it should be ignored.

    n = arg.test_name

    if not n.endswith('.all') :
        return False

    arg.test_name = arg.test_name.replace(".peng.all","")
    return True

