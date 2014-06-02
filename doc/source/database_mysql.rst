MySQL databases
--------------------------------

This chapter is a few notes about using mysql databases.


You usually need to install a MySQL server on your database server and
a MySQL client on the machine that will access the database.  Often
you can run both on the same machine.


After initial mysql install
----------------------------

mysql -u root
    # as any user

select host, user, password from mysql.user;
    # shows all the users

update mysql.user set password = password('newpwd') where user = 'root';
    # set a password for the root user

delete from mysql.user where user = '';
    # delete anonymous users

flush privileges;
    # do this any time you change privs in mysql

delete from mysql.db where db like 'test%';
drop database test;
    # delete special access for test databases

create database jwstetc_test;
    # create a new database

create user d00d identified by 'banana';
    # create a new user named "d00d" with a password of "banana"

grant usage on *.* to 'd00d'@'%';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE TEMPORARY TABLES, SHOW VIEW ON jwstetc_test.* to d00d;

show grants for d00d;
grant all on jwstetc_test.* to d00d;


