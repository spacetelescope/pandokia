Pandokia Test Result File Format
--------------------------------

TODO: move this to Adding Test Runners section

A test report file is a series of one ore more test result records, 
with each record represented by several lines of ASCII text that
comply with the following format::


    name=value
        indicates a one-line value for <<name>>

    name: 
    .line 
    .line 
    .line
        \n
        indicates a multi-line value for <<name>>.  There
        is a newline immediately after the colon, and each
        following line begins with a period.  A blank line
        ends the field.  The \n after the ':' is not part
        of the string.  The blank line at the end is not
        part of the string.  The '.' at the beginning of
        each line is not. Because of database limitations,
        nul characters are converted to \0 when imported into
        the database.

    Blank lines and comment lines (beginning with "#") are ignored.

The following special commands are also recognized:

START 
   The START command will reset the state of the input processor.  This
   includes clearning any defaults.  You can write "\n\nSTART\n" to
   ensure a clean state when appending to a file.

END 
   REQUIRED. Indicates end of a record; the record is entered in the database.
   This command must be present for the record to be imported.

SETDEFAULT
   this record is not entered in the database, but the values are
   filled in as default values for all following records.  You can
   still set a field, even if there is a default.  The last value you
   set will be used.
