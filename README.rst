=================
custref_to_sql.py
=================

Transform a customer reference dump-file into SQL commands representing the
same data.

Installation
------------

Install `Python 2.7`_. Make sure to have it adjust your system ``PATH`` so that
you can run ``python`` and ``pip`` from the command-line.

Make sure ``pip`` is the latest version:

.. code:: shell

   pip install -U pip

Then install this script:

.. code:: shell

   pip install git+https://github.com/jonathanj/custref-to-sql-py.git

You can ensure that it was successful and that the scripts are installed to your
system ``PATH``:

.. code:: shell

   custref-to-sql --help

The command-line help should be printed out.


Upgrading
---------

To install new versions of this script at a later stage use:

.. code:: shell

   pip install --upgrade git+https://github.com/jonathanj/custref-to-sql-py.git

.. _Python 2.7: https://www.python.org/downloads/release/python-2715/


Usage
-----

(Note: You'll need to run this script from the command line.)

To generate just the SQL "INSERT" statements use:

.. code:: shell

   custref-to-sql --create input_file.csv output_file.sql

To generate SQL that also includes the necessary "CREATE TABLE" statements use:

.. code:: shell

   custref-to-sql --create input_file.csv output_file.sql
