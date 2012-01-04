import time

def test():
    import os
    print "PDK_TIMEOUT ",os.environ['PDK_TIMEOUT']
    print "start sleep 60"
    time.sleep(60)
    print "end"

