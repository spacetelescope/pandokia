import pandokia.helpers.cases

def tran(ob, tbname, infmt, outfmt) :
    infile  = "%s.%s.in"    %(tbname,infmt)
    outfile = "%s.%s.%s.out"%(tbname,infmt,outfmt)
    c="tbconv %s %s < %s > %s"%(infmt,outfmt,infile,outfile)
    print "C=",c
    ob.command(c)
    ob.check_file(outfile,'text')


class input(pandokia.helpers.cases.FileTestCase) :

    def test_awk(self):
        tran(self, '1','awk','csv')

    def test_csv(self):
        tran(self, '1','csv','csv')

    def test_rst(self):
        tran(self, '1','rst','csv')

    def test_tabs(self):
        tran(self, '1','tabs','csv')

    def test_trac_wiki(self) :
        tran(self, '1','trac_wiki','csv')

    def test_tw(self):
        tran(self, '1','tw','csv')


class output(pandokia.helpers.cases.FileTestCase) :

    def test_csv(self) :
        tran(self, '2', 'awk', 'csv')

    def test_html(self):
        tran(self, '2', 'awk', 'html')

    def test_rst(self):
        tran(self, '2', 'awk', 'rst')

    def test_tabs(self):
        tran(self, '2', 'awk', 'tabs')

    def test_trac_wiki(self):
        tran(self, '2', 'awk', 'trac_wiki')

    def test_tw(self):
        tran(self, '2', 'awk', 'tw')

