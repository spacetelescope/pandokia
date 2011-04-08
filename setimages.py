#
#
def setimages() :
    import os
    import base64
    f = open( "delta.gif", "rb" )
    header = f.read()
    f.close()
    header = base64.b64encode(header)

    # f = open( os.path.dirname(__file__) + "pandokia/favicon.ico", "rb" )
    # favico = f.read()
    # f.close()
    # favico = base64.b64encode(favico)
    favico = 'None'

    f = open( os.path.dirname(__file__) + "pandokia/common.py", "r" )
    l = f.readlines()
    f.close()

    f = open( os.path.dirname(__file__) + "pandokia/common.py", "w" )
    for x in l :
        if not x.startswith("B64IMG_") :
            f.write(x)
    f.write("B64IMG_FAVICO = '%s'\n"%favico)
    f.write("B64IMG_HEADER = '%s'\n"%header)
    f.close()

setimages()
