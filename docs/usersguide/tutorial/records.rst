..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _create_and_search_your_first_record:

Create and search your first record
===================================

Now that Invenio demo site has been installed in :ref:`install_invenio`, let us
see how we can load some records.

Upload a new record
-------------------

For the ILS flavour let us create a small example record in MARCXML format:

.. code-block:: console

   $ vim book.xml
   $ cat book.xml
   <?xml version="1.0" encoding="UTF-8"?>
   <collection xmlns="http://www.loc.gov/MARC21/slim">
   <record>
     <datafield tag="245" ind1=" " ind2=" ">
       <subfield code="a">This is title</subfield>
     </datafield>
     <datafield tag="100" ind1=" " ind2=" ">
       <subfield code="a">Doe, John</subfield>
     </datafield>
   </record>
   </collection>

We can upload it by using ``invenio marc21 import`` command:

.. code-block:: console

   $ invenio marc21 import --bibliographic book.xml
   Importing records
   Created record 117
   Indexing records

Search for the record
---------------------

Let us verify that it was well uploaded:

.. code-block:: console

   $ firefox http://192.168.50.10/records/117

and that it is well searchable:

.. code-block:: console

   $ firefox http://192.168.50.10/search?q=doe

Uploading content
-----------------

For more information on how to upload content to an Invenio instance, see the
documentation chapter on :ref:`loading_content`.
