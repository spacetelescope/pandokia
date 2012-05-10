========
FAQ
========


= Pandokia FAQ =

== General ==

 * Why did you write Pandokia?  What is it for?

  I used to come to work and find an email message listing all the
  tests that failed last night, but it is hard to work with just a
  list of the names of hundreds of failed tests.  (We run tens of
  thousands of tests, distributed across many operating systems;
  even a tiny change to one part of the system can cause many tests
  to fail.)

  Pandokia is a reporting system to organize all those results.  Of
  course, you can't view a report until you have data, so it also
  includes a mechanism to run a testing tool (such as py.test) and gather
  the test results.

  Having Pandokia has enabled us to increase our automatic testing
  substantially.  Some nights, we run over 150 000 tests, and we
  can easily manage the case where thousands of tests fail.

 * Why "pandokia"? Does it mean anything?

  We made up the word from the Greek morphemes "pan" = all and "dokimi" = test.

 * Where can I get help?

  You can send email to help@stsci.edu: you must put "STSDAS/pandokia"
  in the message for the system to route it to us. We also follow
  the TIP list (testing-in-python@idyll.org).

== Design ==

 * Why didn't you use Zope, Django, Ruby on Rails, ASP.NET, etc?

  Tools like that can be useful, but when you have a lot of work
  to do, sometimes it is best to use something you already know
  instead of evaluating a bunch of new tools.  I recommend that
  software developers should read the short story "Superiority" by
  Arthur C Clarke.

  The simple CGI implementation is very easy to install on a web
  server, without root privileges.

 * Why did you invent your own file format for pdk log files instead of using XML, JSON, YAML, INI, etc?

     It is easier to read and easier to write than most standard
     formats.  We even create pdk log files from shell scripts.

    If a test crashes while part way through writing a pandokia log
    file, another test can come along and append to that log file
    without any data corruption; this is not true for many standard
    formats.

    In the pandokia format, the report from the crashed test will
    not be complete, but the reports from the tests that follow are
    still readable.  This is important because core dumps are a
    fact of life when you use continuous integration.

 * What databases are supported?

    * sqlite 

        Sqlite does not require a database server.  We initially
        set up a database without getting the IT department involved.

    * MySQL

        When we wanted more granular locking than sqlite, 

    * Postgres - maybe

        I have postgres on my home computer, and I have run pandokia
        there from time to time.  I don't routinely test in postgres.

 * Why not use an ORM ?

    I know SQL fairly well for a causal database user.  For me,
    object-relation managers are hard to use, but SQL is easy.

== Trivia ==

 * Why is there a cat on the top of the web displays?

   We chose to use a cat shortly after an overdose of goats at the testing BOF at PyCon 2010.

   This cat is Vicki's cat, Sienna.  She is alertly watching your test reports, as you should be.

 * But what about the goat?

   1. You can change the file pandokia/head.png to a png file of whatever image you would like.

   2. If you just need to see a goat, we recommend: http://en.wikipedia.org/wiki/File:ZodiacalConstellationCapricornus.jpg

