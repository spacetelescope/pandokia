import sys
#
#
def setimages( filename ) :
    import os
    import base64
    f = open( filename, "rb" )
    header = f.read()
    f.close()
    header = base64.b64encode(header)

    if filename.endswith('.png') :
        format = 'png'
    elif filename.endswith('.jpg') :
        format = 'jpeg'

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
    f.write("B64IMG_FORMAT = '%s'\n"%format)
    f.close()

if __name__ == '__main__' :
    setimages( sys.argv[1] )

