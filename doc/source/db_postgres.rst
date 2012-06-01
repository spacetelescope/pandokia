Initializing the Postgres Database
................................................................................

.. :

    su postgres

    psql postgres
    drop database pandokia;
    create database pandokia;
    grant all on database pandokia to mark ;

    ^D

    psql pandokia < pandokia/sql/postgres.sql


Deleting the Pandokia Tables
................................................................................


.. :

    psql pandokia < pandokia/sql/drops.sql


