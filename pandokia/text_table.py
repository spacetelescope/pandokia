#
# pandokia - a test reporting and execution system
# Copyright 2009, Association of Universities for Research in Astronomy (AURA) 
#


#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################
# text_table

__all__ = [ "text_table" ]

import cStringIO as StringIO
import cgi
import urllib
import csv

#
# A text_table contains a list of text_table_row.  
# Each text_table_row contains a list of text_table_cell.  
# Each text_table_cell contains text (not necessarily a string) and
#   various html related values.
#

# 
def pad_list( l, n, value=None ) :
    """
    pad_list( list, n, value=None) - append value to list until it list[n] exists
    """
    while n >= len(l) :
            l.append(value)


###
###
###

class text_table_cell :

    """
    private - single cell of a text_table
    """

    # this is a single cell of the table

    def __init__(self) :
        # text is the value to display; it is not necessarily a string
        self.text = ''
        self.sort_key = ''
        # link is where an href covering the whole table cell should point
        self.link = None
        # html is displayed instead of text in HTML output (if set)
        self.html = None
        # html_attributes are applied to table cells
        self.html_attributes = None

    # need __repr__ for debugging
    def __repr__ (self) :
        return repr(self.text)

    def set_value( self, text=None, link=None, html=None, sort_key=None ) :
        self.text = text
        self.link = link
        self.html = html
        if sort_key is None :
            self.sort_key = text
        else :
            self.sort_key = sort_key

    def get_text(self) :
        return self.text

###
###
###

class text_table_row :

    """
    private - single row of a text_table
    """

    def __init__(self) :

        # list is the list of what cells are in this row
        self.list = [ ]

        # sort_order is needed for the __cmp__ function; you have to set
        # the same sort_order into all the rows before sorting the table
        self.sort_order = [ 0 ]


    # the sort_order is a list of column numbers. N means sort by column N
    # ascending;  -N means sort by column N descending.  Maybe we could get
    # fancier here and allow a way to specify data types for the sort...
    def __cmp__(self, other) :
        for x in self.sort_order :
            if x < 0 :
                r = -1
            else :
                r = 1
            if self.list[x].sort_key < other.list[x].sort_key :
                return -r
            if self.list[x].sort_key > other.list[x].sort_key :
                return r 
        return 0

    def def_sort_order(self, sort_order) :
        self.sort_order = sort_order

    def pad(self, n) :
        l = self.list
        while len(l) < n:
            l.append(text_table_cell())

        x = 0
        while x < n :
            if l[x] is None :
                l[x] = text_table_cell()
            x += 1



###
###
###

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################

## BUG: text_table.number_of_columns doesn't work correctly.  If you
## use define_column(), it is pretty close, but if you create columns
## by just stuffing values into them, then number_of_columns may not
## match the actual number of columns. [[ check if this is still accurate ]]

class text_table :

    """
    text_table - a row/column table creator

    A text_table is a table of rows and columns.  You create the table, 
    fill the individual cells, then extract the table in various formats.

    Supported output formats include 
        HTML
        CSV
        awk
            Columns of text are separated by tabs.

    Create the table with the class constructor:

        t = text_table.text_table()

    The table begins as 0 rows and 0 columns.  New rows and columns appear 
    when set.  Each row may have a different number of columns.

    Declare column names if necessary:
        t.define_column("Thing")    # next available column
        t.define_column("Thing",0)  # title for column 0

    Fill column values:
        t.set_value(row=0, col=0, value="foo")

    Extract the output:
        print t.get_html()


    Methods: (see individual method documentation for details)

    define_column()
        defines the name of a column

    set_value()
        sets the value in a row/column; values are normally text, but
        this is not required.

    set_html_table_attributes()
        set a string to be included in the <table> directive

    set_html_cell_attributes()
        set a string to be included in the <td> directive

    sort()
        sort the table

    pad()
        force all rows to have as many columns as the widest row
    
    join()
        combine another text_table into this one, with new columns to
        the right.
    
    get_html()
    get_csv()
    get_awk()
        return the table content as a string in selected defined format.

    """
#-------------------------------------------------------------------------------####################################################
    ##

    def __init__(self) :
        self.colmap = { }
        self.number_of_columns = 0
        self.rows = [ ]
        self.html_table_attributes = ""
        self.suppressed  = [ ]
        self.titles      = [ ]
        self.title_links = [ ]
        self.title_html  = [ ]
        pass

    ##

    def define_column(self, name, num = -1, link=None, html=None, showname=None ):
        if num < 0 :
            # we are defining a new column without specifying a column number
            # The name matches an existing column, or we add a new one.
            if name in self.colmap :
                num = self.colmap[name]
            else :
                num = self.number_of_columns
                self.number_of_columns = self.number_of_columns + 1

        self.colmap[name] = int(num)

        # make sure the title lists are all long enough
        pad_list(self.titles,      num, '' )
        pad_list(self.title_links, num, None )
        pad_list(self.title_html,  num, None )

        # fill in the values
        if showname is not None :
            self.titles[num]      = showname
        else :
            self.titles[num]      = name
        self.title_links[num] = link
        self.title_html[num]  = html

        # return column number.  not so important if it was passed in, but
        #  useful if we assigned it
        return num

    ##

    def set_value(self, row, col, text=None, link=None, html=None, sort_key=None) :
        # value = text to save
        # link = href to use
        # html = text to use in place of value in html table
        #       (you would really rather not do this)

        o = self._row_col_cell(row,col)

        o.set_value(text, link, html, sort_key)

    ##
    def get_cell(self, row, col) :
        if row >= len(self.rows) :
            return None
        row = self.rows[row]
        if col >= len(row.list) :
            return None
        return row.list[col]

    ##
    def get_title(self, col) :

        if col in self.colmap :
            col = self.colmap[col]
        return self.titles[col].get_text()

    ##
    def get_row_count(self) :
        return len(self.rows)

    ##

    def set_html_table_attributes(self, attr) :
        self.html_table_attributes = attr

    ##

    def set_html_cell_attributes(self, row, col, attr) :
        o = self._row_col_cell(row, col)
        o.html_attributes = attr

    ##

    def sort( self, sort_order, reverse=False ) :
        so = [ ]
        for x in sort_order :
            if type(x) is type("") :
                if x in self.colmap :
                    so.append(self.colmap[x])
            else :
                so.append(x)
        for x in self.rows :
            x.def_sort_order(so)
        self.pad()
        self.rows.sort(reverse=reverse)

    ##

    def set_sort_key( self, col, func ) :
        fail = 0
        for row in range(0,len(self.rows)) :
            o = self._row_col_cell(row, col)
            try :
                o.sort_key = func(o.text)
            except Exception, e :
                o.sort_key = o.text
                fail = fail + 1
        conv = len(self.rows) - fail

    ##

    def pad(self) :
        # find how many columns we have
        # fill in every row to be that wide with blank columns
        count = 0
        for r in self.rows :
            this_width = len(r.list)
            if this_width > count :
                count = this_width
        self.number_of_columns = count
        for i,r in enumerate(self.rows) :
            if r is None :
                self.rows[i] = r = text_table_row()
            r.pad(count)

    ##

    def join(self, other) :
        # bring in columns from another table as further columns of this table
        # MAY CHANGE BOTH TABLES

        # Make sure all of our rows are padded out to the max width.  Count
        # out max width.
        self.pad()

        # if there is no data in the second table, there is nothing to do
        if len(other.rows) == 0 :
            return

        # make sure self has at least as many rows as other
        x = len(self.rows)
        while x < len(other.rows) :
            self.set_value(x, 0, '')
            x=x+1

        # make sure other has at least as many rows as self
        x = len(other.rows)
        while x < len(self.rows) :
            other.set_value(x, 0, '')
            x=x+1
        

        # For each row, append the other row to our row.  Yes, we are keeping
        # references to the text_table_cell objects, so future changes to
        # the other table might screw us up.
        x = 0
        while x < len(self.rows) :
            self.rows[x].list.extend(other.rows[x].list)
            x = x + 1

        # Bring in the column names from the other table.  Do not write
        # over an existing column name.  If the new column has the same name
        # as an old column, you can't get to the new one by name.  bummer.
        # The name is still displayed on the column, though.
        for x in other.colmap :
            if not x in self.colmap :
                self.colmap[x] = other.colmap[x] + self.number_of_columns

        # Bring in the actual title strings. (These are the column names
        # that get displayed.)
        self.titles.extend(other.titles)

        self.title_links.extend(other.title_links)
        self.title_html .extend(other.title_html )

        self.number_of_columns = len(self.titles)
        return

    ##

    def _row_object(self, row) :
        # find the object that represents a specific row of the table
        while len(self.rows) <= row :
            self.rows.append(text_table_row())
        return self.rows[row]

    ##

    def _row_col_cell(self, row, col) :
        # find the object that represents a specific row/col of the table
        # note that columns can have names ( see define_column() )
        o = self._row_object(row)
        this_row = o.list

        if col in self.colmap :
            col = self.colmap[col]

        try :
            col = int(col)
        except ValueError :
            self.define_column(col)
            col = self.colmap[col]

        while len(this_row) <= col :
            this_row.append(text_table_cell())

        if col > self.number_of_columns :
            self.number_of_columns = col + 1

        return this_row[col]

    ##

    def suppress(self, col, flag=1) :
        """
        Declare whether this column should be displayed in the output.

        col     - column number or name
        flag    - true=suppress, false=display
        """
        if col in self.colmap :
            col = self.colmap[col]
        while len(self.suppressed) <= col :
            self.suppressed.append(0)
        self.suppressed[col] = flag

    ##

    def is_suppressed(self, colcount ) :
        """
        Return whether this column should be displayed in the output.

        true=suppressed, false=displayed
        """
        while colcount >= len(self.suppressed) :
            self.suppressed.append(0)
        return self.suppressed[colcount]

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################
    ##
    ## GENERATE HTML
    ##

    def get_html(self, headings=True, color_rows=0) :
        """"
        Return HTML of the table.

        str = o.get_html( headings=True )
        headings    - True=show headings, False=do not show headings

        If the table rows are not all the same length, the display will 
        not look good on most browsers.  use o.pad() first.

        See also:
            define_column - determines table headings
            set_html_table_attributes - values in <table> directive
            set_html_cell_attributes - values in <td> directive

        """

        s = StringIO.StringIO()

        s.write("<table "+self.html_table_attributes+">\n")

        if headings :
            s.write("<tr>")
            colcount = -1
            for r in self.titles :
                colcount = colcount + 1
                if self.is_suppressed(colcount) :
                    continue
                s.write("<th>")
                if self.title_html[colcount] :
                    s.write(self.title_html[colcount])
                elif self.title_links[colcount] :
                    s.write("<a href='"+self.title_links[colcount]+"'>")
                    s.write(cgi.escape(str(r)))
                    s.write("</a>")
                else :
                    s.write(r)
                s.write("</th>")
            s.write("</tr>\n")

        row = 0
        for r in self.rows :
            row = row + 1
            if color_rows and (row % color_rows) == 0 :
                s.write("<tr bgcolor=lightgray>")
            else :
                s.write("<tr>")
            r = r.list
            if r is None :
                # there is a row here, but nothing in it.  We are happy
                # to have sent the <tr>, but can't do anything more.
                pass
            else :
                colcount = -1
                for c in r :
                    colcount = colcount + 1
                    if self.is_suppressed(colcount) :
                        continue
                    if c is None :
                        # an empty cell
                        s.write( "<td>&nbsp</td>\n")
                        continue
                    if c.html_attributes :
                        s.write("<td ")
                        if not 'valign' in c.html_attributes :
                            s.write("valign=top ")
                        s.write(c.html_attributes)
                        s.write(">")
                    else :
                        s.write("<td valign=top>")
                    if c.link :
                        s.write("<a href='"+c.link+"'>")
                    if c.html :
                        if c.html == "" :
                            s.write("&nbsp;")
                        else :
                            s.write(c.html)
                    else :
                        if c.text is None  or c.text == "":
                            s.write("&nbsp;")
                        else :  
                            s.write(cgi.escape(str(c.text)))
                    if c.link :
                        s.write("</a>")
                    s.write("</td>\n")
            s.write("</tr>\n")

        s.write("</table>")

        rval = s.getvalue()
        s.close()
        del s
        return rval

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################
    ##
    ## GENERATE CSV
    ##

    def get_csv(self, newline="\n", headings=False) :
        """
        str = o.get_csv()
        str = o.get_csv(newline='\r\n')

        Generate table output in CSV format, using the standard python csv module.
        The newline parameter specifies the line terminator, default is "\n".

        Returns a string.

        """
        s = StringIO.StringIO()
        w = csv.writer(s, lineterminator=newline)

        if headings :
            l = [ ]
            colcount = -1
            for r in self.titles :
                colcount = colcount + 1
                if self.is_suppressed(colcount) :
                    continue
                l.append(r)
            w.writerow(l)

        for r in self.rows :
            r = r.list
            if r is None :
                w.writerow([ ])
            else :
                l = [ ]
                colcount = -1
                for c in r :
                    colcount = colcount + 1
                    if self.is_suppressed(colcount) :
                        continue
                    if c is None :
                        l.append("")
                    else :
                        l.append(c.text)
                w.writerow(l)
        rval = s.getvalue()
        s.close()
        return rval

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################
    ##
    ## GENERATE AWK
    ##  awk output is columns separated by tabs; useful for
    ##  output to be processed by awk 
    ##


    def get_awk(self, blank="-", tabwidth=8, separator="\t", headings=False ) :
        """
        string = o.get_awk(blank="-", tabwidth=8, separator="\t" )

        Generate table output suitable for processing by awk:
            - each column is printed as plain text
            - separator is printed between columns
            - tabs in the text are converted to spaces (with 8 column tab stops)
            - newline

        Columns are separated by tabs.

        Parameter blank is printed for columns that are empty.
        Columns that are missing (i.e. this row is not as wide
        as some other row) are not printed.

        Data values that contain tabs have tabs expanded to spaces
        according to parameter tabwidth.

        """
        s = StringIO.StringIO()

        if headings :
            for col, x in enumerate(self.titles) :
                if self.is_suppressed(col) :
                    continue
                s.write(x)
                s.write(separator)
            s.write('\n')

        for r in self.rows :
            if r and r.list :
                for col, cell in enumerate(r.list) :
                    if self.is_suppressed(col) :
                        continue
                    if cell is None or cell.text == None or cell.text == '' :
                        s.write(blank)
                    else :
                        s.write(str(cell.text).expandtabs(tabwidth))
                    s.write(separator)
            s.write("\n")
        
        rval = s.getvalue()
        s.close()
        return rval

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################
    ##
    ## GENERATE RESTRUCTURED TEXT
    ##  creates the restructured text "simple" table format
    ##

    def _rst_border(self, col_widths) :
        l = [ ]
        for col, wid in enumerate(col_widths) :
            if self.is_suppressed(col) :
                continue
            l.append("="*wid)
            l.append("  ")
        l.append('\n')
        return ''.join(l)

    def get_rst(self, include_border=True, headings=False ) :
        """
        string = o.get_rst()

        generate table output suitable for use in restructured text

        uses ==== above and below the table

        """
        s = StringIO.StringIO()

        # count up the widest field in each column

        col_widths = [ ]

        # if using headings, initialize the column widths to the width of each heading
        if headings :
            for x in self.titles :
                col_widths.append(len(x))

        # raise each column width to match the widest that we find
        for r in self.rows :
            if r and r.list :
                for col in range(0,len(r.list)) :
                    while col >= len(col_widths) :
                        col_widths.append(0)
                    l = len(str(r.list[col].text))
                    if col_widths[col] < l :
                        col_widths[col] = l

        # calculate and write the top border line
        if include_border :
            border = self._rst_border(col_widths)
            s.write(border)

        # display column headings in the first line, if necessary
        if headings :
            for col, title in enumerate(self.titles) :
                if self.is_suppressed(col) :
                    continue
                s.write("%-*s"%(col_widths[col],str(title)))
                s.write("  ")
            s.write('\n')

        # display the table content
        for r in self.rows :
            if r and r.list :
                for col in range(0,len(r.list)) :
                    if self.is_suppressed(col) :
                        continue
                    s.write("%-*s"%(col_widths[col],str(r.list[col].text)))
                    s.write("  ")
            s.write("\n")

        # write the last border line
        if include_border :
            s.write(border)

        #
        rval = s.getvalue()
        s.close()
        return rval

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################

    def get_text(self) :
        """
        string = o.get_text()

        generate table output suitable for use in plain text
        """
        # yes, there is a stunning resemblance between plain text and rst.
        return self.get_rst(include_border=False)

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################
    ##
    ## GENERATE TRAC WIKI
    ##  format suitable for pasting into a Trac wiki page
    ##

    def get_trac_wiki(self, headings=False) :
        """
        string = o.get_trac_wiki()

        generate table output suitable for use in a trac wiki

        """
        col_widths = [ 0 for x in self.titles ]
        s = StringIO.StringIO()


        if headings :
            for col, x in enumerate(self.titles) :
                if self.is_suppressed(col) :
                    continue
                col_widths[col] = len(str(x))

        for r in self.rows :
            if r and r.list :
                for x in range(0,len(r.list)) :
                    while x >= len(col_widths) :
                        col_widths.append(0)
                    l = len(str(r.list[x].text))
                    if col_widths[x] < l :
                        col_widths[x] = l

        if headings :
            for col, x in enumerate(self.titles) :
                if self.is_suppressed(col) :
                    continue
                s.write("|| %-*s "%(col_widths[col],str(x)))
            s.write("||\n")

        for r in self.rows :
            if r and r.list :
                for col in range(0,len(r.list)) :
                    if self.is_suppressed(col) :
                        continue
                    s.write("|| %-*s "%(col_widths[col],str(r.list[col].text)))
            s.write("||\n")

        rval = s.getvalue()
        s.close()
        return rval


    ## generic getter with a format
    def get( self, format='rst', headings=False ) :
        if format == 'html' :
            return self.get_html(headings=headings)
        elif format == 'csv' :
            return self.get_csv(headings=headings)
        elif format == 'awk' :
            return self.get_awk(headings=headings)
        elif format == 'rst' or format == 'text' :
            return self.get_rst(headings=headings)
        elif format == 'trac_wiki' or format == 'tw' :
            return self.get_trac_wiki(headings=headings)
        else :
            return "Format %s not recognized in text_table.get" % format

    ##
    ## end class text_table

#-----------------------------------80 cols-------------------------------------##################### 132 cols #####################


def sequence_to_table( l ) :
    t = text_table()
    for row, x in enumerate(l) :
        for col,y in enumerate(x) :
            t.set_value(row, col, y)
    return t

if __name__ =="__main__":
    import sys
    t=text_table()
    t.set_html_table_attributes("border=1 bgcolor=blue")

    l = [   ( 'a', 1),
            ( 'z', 5),
            ( 'z', 7),
            ( 'b', 9),
            ( 'a', 2),
            ( 'b', 4),
            ( 'x', 6),
            ( 'a', 8),
     ]

    c = 0
    for x in l :
        (v1, v2) = x 
        v2 = v2 + 10
        t.set_value(c,0,c)
        t.set_value(c,1,v1)
        t.set_value(c,2,v2)
        t.set_html_cell_attributes(c,1,"bgcolor=gray")
        c += 1


    c = c + 2
    t.set_value(c,0,c)
    t.set_value(c,1,'arf')

    t.set_html_cell_attributes(3,2,"bgcolor=red")
    t.pad()


    print ""
    s = t.get_html()
    print s
    print ""
    s = t.get_awk()
    print s

    print ""
    t.sort( [ -1,2 ] )
    s = t.get_awk()
    print s
    print ""
    t.sort( [ 0 ] )
    s = t.get_awk()
    print s

    print ""
    print t.get_csv()

    t = text_table()
    t.set_value(0,0,'4')
    t.set_value(1,0,'3')
    t.set_value(2,0,'2')
    t.set_value(3,0,'1')
    t.set_value(4,0,'')
    t.set_value(5,0,'C')
    t.set_value(6,0,'B')
    t.set_value(7,0,'A')
    t.set_sort_key(0, float)
    print "XX"
    print t.get_awk()
    print "XX"
    t.sort( [ 0 ], reverse=True )
    print t.get_awk()
    print "XX"
    t.sort( [ 0 ], reverse=False )
    print t.get_awk()
    print "XX"
    
    print ""
    s = t.get_rst()
    print s

    print ""
    s = t.get_trac_wiki()
    print s

