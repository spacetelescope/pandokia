#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#

import CGIHTTPServer
import BaseHTTPServer

class my_handler( CGIHTTPServer.CGIHTTPRequestHandler ) :

    # by default, I don't want any directory where everything is assumed
    # to be a cgi
    cgi_directories = [ ]

    def __init__(self, request, client_address, server) :
        CGIHTTPServer.CGIHTTPRequestHandler.__init__(self, request, client_address, server)

    def is_cgi(self) :

        l = self.path.split("?",1)
        if l[0].endswith(".cgi") or l[0].endswith(".bat") :
            # it is a cgi if the file name ends ".cgi"
            # l[0] is the name of the cgi
            # l[1] is the query string
            cgi = l[0]
            if len(l) == 2 :
                args = l[1]
            else :
                args = ''
            # get the base name of the program out of the url
            l = cgi.rsplit('/',1)
            # the rest of the object wants the the directory name
            # and the base name with the args still attached
            self.cgi_info = ( l[0], l[1] + "?" + args )

            # yes, it was a cgi
            return True

        # this is compatible with the old behaviour:  anything in
        # a cgi directory must be a cgi.  You can have args after
        # another / which the CGI can find in PATH_INFO
        for x in self.cgi_directories :
            if self.path.startswith(x) :
                i = len(x)
                if self.path[i] == '/' :
                    print "/"
                    self.cgi_info = self.path[:i], self.path[i+1:]
                    return True

        # ok, it must not be a cgi
        return False

    # This translate_path prevents attempts to escape the directory
    # tree by walking through ".." -- this is not a great way to
    # do it, but it works and there does not appear to be any more
    # suitable hook available.
    def translate_path( self, path ) :
        if path.find("/../") >= 0 :
            path = "/"
        path = CGIHTTPServer.CGIHTTPRequestHandler.translate_path(self,path)
        return path


def run( args = [ ] ) :
    # you could parse args here if you wanted to.  I don't care to spend
    # the time.  This is just here for people who can't (or don't want to)
    # install a full featured web server just to try things out.
    ip = '127.0.0.1'
    port = 7070

    httpd = BaseHTTPServer.HTTPServer( (ip, port) , my_handler)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    while 1 :
        httpd.handle_request()

if __name__ == '__main__' :
    run()
