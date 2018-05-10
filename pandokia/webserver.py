#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA)
#

import os

try:
    from http.server import CGIHTTPRequestHandler, HTTPServer
except ImportError:
    from CGIHTTPServer import CGIHTTPRequestHandler
    from BaseHTTPServer import HTTPServer


class my_handler(CGIHTTPRequestHandler):

    cgi_directories = ["/cgi-bin/"]

    def __init__(self, request, client_address, server):
        CGIHTTPRequestHandler.__init__(self, request, client_address, server)

    def is_cgi(self):

        l = self.path.split("?", 1)
        if l[0].endswith(".cgi") or l[0].endswith(".bat"):
            # it is a cgi if the file name ends ".cgi"
            # l[0] is the name of the cgi
            # l[1] is the query string
            cgi = l[0]
            if len(l) == 2:
                args = l[1]
            else:
                args = ''
            # get the base name of the program out of the url
            l = cgi.rsplit('/', 1)
            # the rest of the object wants the the directory name
            # and the base name with the args still attached
            self.cgi_info = (l[0], l[1] + "?" + args)

            # yes, it was a cgi
            return True

        # this is compatible with the old behaviour:  anything in
        # a cgi directory must be a cgi.  You can have args after
        # another / which the CGI can find in PATH_INFO
        for x in self.cgi_directories:
            if self.path == x:
                return False

            if self.path.startswith(x):
                i = len(x)
                self.cgi_info = self.path[:i], self.path[i:]
                return True

        # ok, it must not be a cgi
        return False

    # This translate_path prevents attempts to escape the directory
    # tree by walking through ".." -- this is not a great way to
    # do it, but it works and there does not appear to be any more
    # suitable hook available.
    def translate_path(self, path):
        if path.find("/../") >= 0:
            path = "/"
        path = CGIHTTPRequestHandler.translate_path(self, path)
        return path


def run(args=[]):
    # you could parse args here if you wanted to.  I don't care to spend
    # the time.  This is just here for people who can't (or don't want to)
    # install a full featured web server just to try things out.
    if len(args) > 0:
        ip = args[0]
    else:
        import platform
        ip = platform.node()

    print("ip: %s" % ip)
    port = 7070

    # make sure pdk.cgi is here somewhere - if not, make a symlink
    # this is just to save a little typing
    try:
        f = open('cgi-bin/pdk.cgi', 'r')
    except IOError:
        try:
            f = open('pdk.cgi', 'r')
        except IOError:
            os.system('ln -s `which pdk` pdk.cgi')
        else:
            f.close()
    else:
        f.close()

    httpd = HTTPServer((ip, port), my_handler)

    sa = httpd.socket.getsockname()
    print("Serving HTTP on %s port %s ..." % (sa[0], sa[1]))
    while True:
        httpd.handle_request()

if __name__ == '__main__':
    run()
