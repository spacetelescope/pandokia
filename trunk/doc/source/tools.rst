.. index:: single: tools

===============================================================================
Assorted Tools
===============================================================================

Pandokia contains some programming tools that were convenient to
dump into this project.  These are not necessarily related to
testing.

.. contents::

pdk_sphinxweb - automatically build several sphinx documents
-------------------------------------------------------------------------------

pdk_sphinxweb searches for sphinx documents nested below the current directory.
A directory might contain a sphinx document if one of these conditions is true:

 - it is named "doc"
 - it is named "docs"
 - it contains a file named ".this_is_a_sphinx_doc"

In order for the document to be built, the directory must not contain
a file named "no_auto_build" and must contain a file named "Makefile".

Invoke pdk_sphinxweb with the name of the directory where you want
the built documents installed: ::

    pdk_sphinxweb /x/y/z/output_directory

It will find things that look like sphinx documents in the **current** directory,
attempt to build them as HTML and PDF, and place the results in the output
directory.  When finished, it will construct index.shtml with document titles,
links to HTML and PDF documents, and links to HTML and PDF build logs.

If the output_directory already contains header.html or footer.html,
those files will be included in the index.shtml file.  Otherwise,
you get a bare table, which any reasonable web browser will be able
to display.


xtname - set the title of an xterm
-------------------------------------------------------------------------------

Use: ::

    xtname this is a window title

to set the title of an xterm from your shell prompt.

tbconv - simple text table conversion tool
-------------------------------------------------------------------------------

Pandokia contains a table generator that it uses to produce the
tables on the web page.  tbconv reads standard input in one of a
few different table formats then displays the table on standard
output in one of a few different table formats.

input formats:

 - csv - CSV files; uses the python csv module
 - rst - reStructuredText; only knows Simple tables, not Grid tables
 - tabs - columns are separated by tab characters
 - trac_wiki - table format used by track wiki ( can also specify as "tw" )

output formats are the same as input formats, plus:

 - html - HTML 

sendto - subversion branching tool
-------------------------------------------------------------------------------

tbd

junittopdk - convert JUnit/XML output to Pandokia format
-------------------------------------------------------------------------------

tbd

