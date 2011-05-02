import pandokia.config
import os

print "db driver=",pandokia.config.pdk_db.pdk_db_driver
print "context=",os.environ['PDK_CONTEXT']

assert pandokia.config.pdk_db.pdk_db_driver == os.environ['PDK_CONTEXT'], "context does not match the db driver name - you probably do not have a correct setup"
