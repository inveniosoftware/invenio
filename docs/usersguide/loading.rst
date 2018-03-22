..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _loading_content:

Loading content
===============

Loading records
---------------

In the Invenio demo site example using ILS flavour, we have seen the ``invenio
marc21`` command that can load records directly from a MARCXML file.

You can use ``dojson`` to convert MARCXML format to its JSON representation:

.. code-block:: console

   $ dojson -i book.xml -l marcxml do marc21 \
       schema "http://192.168.50.10/schema/marc21/bibliographic/bd-v1.0.0.json" \
      > book.json
   $ cat book.json | jq .
   [
     {
       "title_statement": {
         "title": "This is title",
         "__order__": [
           "title"
         ]
       },
       "main_entry_personal_name": {
         "personal_name": "Doe, John",
         "__order__": [
           "personal_name"
         ]
       },
       "__order__": [
         "title_statement",
         "main_entry_personal_name"
       ],
       "$schema": "http://192.168.50.10/schema/marc21/bibliographic/bd-v1.0.0.json"
     }
   ]

You can load JSON records using the ``invenio records`` command:

.. code-block:: console

   $ cat book.json | invenio records create --pid-minter recid --pid-minter oaiid
   efac2fc2-29af-40bb-a85e-77af0349c0fe

The new record that we have just uploaded got the UUID
efac2fc2-29af-40bb-a85e-77af0349c0fe that uniquely identifies it inside the
Invenio record database. It was also minted persistent identifiers ``recid``
representing record ID and ``oaiid`` representing OAI ID.

UUIDs and PIDs
--------------

Objects managed by Invenio use "internal" UUID identifiers and "external"
persistent identifiers (PIDs).

Starting from a persistent identifier, you can see which UUID a persistent
identifier points to by using the ``invenio pid`` command:

.. code-block:: console

   $ invenio pid get recid 117
   rec a11dad76-5bd9-471c-975a-0b2b01d74831 R

Starting from the UUID of a record, you can see which PIDs the record was
assigned by doing:

.. code-block:: console

   $ invenio pid dereference rec a11dad76-5bd9-471c-975a-0b2b01d74831
   recid 117 None
   oai oai:invenio:recid/117 oai

You can unassign persistent identifiers:

.. code-block:: console

   $ invenio pid unassign recid 117
   R
   $ invenio pid unassign oai oai:invenio:recid/117
   R

What happens when you try to access the given record ID?

.. code-block:: console

   $ firefox http://192.168.50.10/api/records/117

You can assign another record the same PID:

.. code-block:: console

   $ invenio pid assign -s REGISTERED -t rec -i 29351009-5e6f-4754-95cb-508f89f4de39 recid 117

What happens when you try to access the given record ID now?

.. code-block:: console

   $ firefox http://192.168.50.10/api/records/117

Deleting records
----------------

If you want to delete a certain record, you can use:

.. code-block:: console

   $ invenio records delete -i efac2fc2-29af-40bb-a85e-77af0349c0fe

Beware of any registered persistent identifiers, though.

Loading files
-------------

Loading full-text files, such as PDF papers or CSV data files together with the
records, will be addressed later.

.. todo:: Describe records, files, buckets.
