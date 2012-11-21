Initializing the MySQL Database
................................................................................

.. :

    mysql -p
    create database pandokia;
    use pandokia;

    drop database pandokia;

.. :

    mysql -p
    source pandokia/sql/mysql.sql


Deleting the Pandokia Tables
................................................................................


.. :

    mysql -p
    source pandokia/sql/drops.sql



MySQL notes
................................................................................


.. :

    set password [ for user ] = password("xyzzy") ;

.. :

    use mysql;
    update user set password=PASSWORD("xyzzy") where user = 'dude' ;
    flush privileges;

.. :

    
