
import pandokia
import pandokia.common as common

pdk_db = pandokia.cfg.pdk_db

def set_chronic( test_run_type, test_run=None, project=None, context=None, host=None ) :

    where_str, where_dict = pdk_db.where_dict( [
        ( 'test_run',  test_run ),
        ( 'project',  project ),
        ( 'context',  context ),
        ( 'host',     host )
        ],
        "( status != 'P' and status != 'D' )"
    
    )

    print where_str, where_dict 

    sql = "SELECT test_run, project, context, host, test_name, status FROM result_scalar %s ORDER BY test_run DESC " % where_str

    n = 0
    c = pdk_db.execute(sql, where_dict) 
    for x in c :
        print "EXAMINE",x
        n = n + 1
        try :
            date = common.looks_like_a_date( test_run )
            if date is None :
                print "NO DATE"
                continue
            print "DATE",date
            
            print "WANT CHRONIC",x
            pdk_db.execute("INSERT INTO chronic ( test_run_type, project, context, host, test_name, xwhen ) values ( :1, :2, :3, :4, :5, :6 )",
                ( test_run_type, x[1], x[2], x[3], x[4], date ) )
            print "CHRONIC",x
        except pdk_db.IntegrityError as e :
            pass
    pdk_db.commit()

    print "TOTAL WAS",n


def check_chronic( test_run_type, test_run=None, project=None, context=None, host=None ) :

    today_time = common.looks_like_a_date( test_run ) 
    print "XXX %s XXX"%today_time
    if today_time is None :
        raise Exception("test_run does not appear to have a date in it")

    today_time = common.parse_time( today_time )

    where_str, where_dict = pdk_db.where_dict( [
        ( 'test_run_type', test_run_type ),
        ( 'project',  project ),
        ( 'context',  context ),
        ( 'host',     host )
        ],
    
    )

    print where_str, where_dict 

    sql = "SELECT project, context, host, test_name, xwhen FROM chronic %s" % where_str


    c = pdk_db.execute(sql, where_dict)
    for x in c :
        print x, today_time
        project, context, host, test_name, xwhen = x

        c1 = pdk_db.execute( "SELECT key_id, status FROM result_scalar WHERE test_run = :1 AND project = :2 AND context = :3 AND host = :4 AND test_name = :5 ",
            ( test_run, project, context, host, test_name ) )

        tmp = c1.fetchone()
        if tmp is None :
            # there is a test in chronic that is not in the test run
            # this is not an error - just ignore it
            continue

        key_id, status = tmp

        if status == 'P' or status == 'D' :
            res = 'F'
        else :
            print "    ",xwhen
            xwhen = common.parse_time( xwhen )
            if xwhen is None :
                res = 'C'
            else :
                if ( today_time - xwhen ) . days > 10 :
                    res = 'C'
                else :
                    res = 'N'

        if res == 'C' :
            print "chronic", key_id
            pdk_db.execute("UPDATE result_scalar SET chronic = '1' WHERE key_id = :1",(key_id, ) )
            pdk_db.commit()
        elif res == 'F' :
            print "fixed"
            pdk_db.execute("DELETE FROM chronic WHERE test_run_type = :1 AND project = :2 AND context = :3 AND host = :4 AND test_name = :5 ",
                ( test_run_type, project, context, host, test_name ) )
        elif res == 'N' :
            print "not chronic"
        else :
            assert 0, "this never happens"

    pdk_db.commit()

            


def run( args ) :
    tr = 'user_sienkiew_2012-06-19-15-07-01'
    tr = 'daily_2012-06-01'
    set_chronic( 'daily', test_run=tr, )
    check_chronic( 'daily', test_run=tr, )
