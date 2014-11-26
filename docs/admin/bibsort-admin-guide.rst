..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _bibsort-admin-guide:

BibSort Admin Guide
===================

1. Overview
-----------

BibSort main goal is to make the sorting of search results faster. It does this by creating
several sorting buckets (that hold recids) that are then loaded by the search_engine and cached.

BibSort module is active if the search_engine is using the sorting buckets to fast sort the
search results. BibSort module can be deactivated by setting the ``CFG_BIBSORT_BUCKETS=0`` in
the ``invenio.conf`` file. Also, if ``bsrMETHOD`` table does not contain any data,
it also means that the BibSort module is not active. The search engine will look into the
BibSort data structures to see if the method that was requested to sort the search results
exists or not. If it does not exist, then the old style sorting function (using bibxxx tables)
will be used.

2. Define Sorting Options
-------------------------

2.1 Define Sorting Options
~~~~~~~~~~~~~~~~~~~~~~~~~~

The different sort options that can be chosen are the logical fields defined in BibIndex.
Which sorting methods that should be shown to the user are defined in WebSearch,
collection parameters, point 8 “Modify sort option for collection .. ”.
By default, all sub-collections will have the same settings as the main collection. To change from default
settings, add a new sorting option for the specific collections you would like to change.

2.2 Translate the Sorting Options for Multilingual Sides
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Translation of the name is done for each specific logical field in BibIndex
(manage logical fields).

3. Configure BibSort
--------------------

3.1 Introduction
~~~~~~~~~~~~~~~~~~~~~~~~~~

When the user choose a sorting option, for example “title”, the arument “title” will
be added to the url. If no sorting method is defined in BibSort, sorting will still be enabled and executed
by live SQL queries, hence slower than with BibSort.

To enable BibSort for the specific sorting option, the argument need to be equal to the name in
BibSort. Then it will execute the task according to the definition/washer.

3.1 Configure
~~~~~~~~~~~~~

A new sorting method are added via a configuration file. The location of this file is:
``CFG_ETCDIR/bibsort/bibsort.cfg``
Each sorting method has a section in this config file, that looks like this:

::

    [sort_field_1]
    name = title
    washer = sort_alphanumerically_remove_leading_articles
    definition = FIELD: title

Each section of the file corresponds to a method:
  - The name property holds the name of the sorting method, that should be unique.
  - The washer property holds the name of the function that will process the values of the records, for this method, before they get sorted (in this case, it will remove the leading articles). This functions are implemented in bibsort_washer.py. One can also set the washer to 'NOOP' which will mean that no washer should be applied to the data before the sorting. Bibsort supports string collation. There is the possibility of selecting a specific language for this, by adding at the end of the washer ':ln', where 'ln' is the language according to which the string comparison should be done. Ex: "washer = sort_alphanumerically_remove_leading_articles:fr" means that the string comparison would be done using the French rules.
  - The definition property holds the name of the place from where the data should be taken for this sorting method. There are several options for defining this property:

    - definition = RNK: method_name means that the data should be taken from the rnkMETHODDATA table, based on the method_name (the method_name should correspond to a method in rnkMETHOD table)
    - definition = MARC: marc1,marc2,marc3.. means that BibSort will sequentially look in all the MARC fields (bibxxx tables) and retrieve the data (the order of the MARC fields is important, since for a given record, BibSort will keep the value from the first MARC field that has data).
    - definition = FIELD: foo is similar with the above option, but for cases were we already have logical fields defined in Invenio, BibSort can look into them in order to retrieve the list of MARC fields that need to be queried.

For adding a new sorting method, one needs to add a new section to the ``bibsort.cfg`` file. Once this is done, the config file needs to be loaded into the database:

.. code-block:: console

    $ ./bibsort --load-config

Similar, for deleting a method, one needs to remove the corresponding section from the bibsort.cfg file, and load the config into the database.
To dump the configuration from the database into a file:

.. code-block:: console

    $ ./bibsort --dump-config

.. note::

    It is necessary to run rebalance (-R) before sorting/updating (-S), after changing
    configuration.

3. Running BibSort
------------------

There are several command line instructions that can be used in order to update the BibSort data. For each instruction, one can define the methods and the records that the command should run on, like this:

.. code-block:: console

    $ ./bibsort --methods=method1,method2 --recids=4,7-17,23,1

If these options will be let empty it will mean that the bibsort operations will run on all the defined methods, and either on all the records existing in the database, or on the all updated records (depending on the operation, see 3.1 and 3.2).

3.1 Rebalancing
~~~~~~~~~~~~~~~

Rebalancing is the operation that will redo from scratch the sorting and recreate the sorting buckets. This should be performed once at the beginning and then maybe once per day, to be sure that the database is in complete sync with the BibSort data structures, and also, to be sure that the buckets are balanced (Imagine a big upload of new records, that will have the same publication year. All these records will be added to the same bucket for the 'publication date' method, making it much bigger then the others, and slower to perform any data calculations on it, including intersecting with the search engine output). If you have a clear idea of how the data is changing during one day, you can set up the rebalancing only for several methods, that contain data that is frequently updated.

.. code-block:: console

    $ ./bibsort -B [--methods=method1,method2]

3.2. Inserting/Updating/Deleting records in BibSort
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inserting/Updating/Deleting records in BibSort is done via the update-sorting operation. Theoretically, this operation should run at short intervals, and for the benefit of the user it would be good to run after BibIndex, so that the updates can be viewed as soon as possible. If no methods are defined it will run for all the methods defined in bibsort.cfg. But, if you have a good overview of the nature of the changes in the data during a period of time, the update-sorting can run more frequently for some methods (like sort by year or sort by title) or less frequently (like sort by most cited, since the citation dictionaries are not updated so frequently). Defining the recids, will result in the update-sorting to run only on those records. If no records are defined bibsort will grab all the modified records since its last run. Since for ranking methods it will anyway grab all the data, update-sorting for a ranking method is basically a rebalancing.

.. code-block:: console

    $ ./bibsort -S [--methods=method1,method2] [--recids=4,7-17,23,1]

4. Impact on the sorted search results
--------------------------------------

Using the BibSort functionality will have the following impact on the 'Sort by' functionality of Invenio:

Sorting will no longer need to be limited to CFG_WEBSEARCH_NB_RECORDS_TO_SORT currently set to 200.
Not all the search results will be sorted, but only those up to jrec, so only up to those 'seen' by the user. This means that using of=id to retrieve the list of recids will not give the full list of recids in case these also need to be sorted.
If in the search results there are records that have no value for the selected sorting method, they will be added at the end, in the order of their insertion date. This records might have just been inserted, this is why it would be important to keep them in the sorted output.
