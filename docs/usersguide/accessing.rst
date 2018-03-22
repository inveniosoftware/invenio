..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _accessing_content:

Accessing content
=================

JSON representation
-------------------

Records are internally stored in JSON following a certain JSON Schema.
They can be obtained using REST API to records.

Using CLI:

.. code-block:: console

    $ curl -H 'Accept: application/json' http://192.168.50.10/api/records/117
    {
      "created": "2017-03-21T10:33:59.245869+00:00",
      "id": 117,
      "links": {
        "self": "http://192.168.50.10/api/records/117"
      },
      "metadata": {
        "__order__": [
          "title_statement",
          "main_entry_personal_name"
        ],
        "_oai": {
          "id": "oai:invenio:recid/117",
          "updated": "2017-03-21T10:33:59Z"
        },
        "control_number": "117",
        "main_entry_personal_name": {
          "__order__": [
            "personal_name"
          ],
          "personal_name": "Doe, John"
        },
        "title_statement": {
          "__order__": [
            "title"
          ],
          "title": "This is title"
        }
      },
      "updated": "2017-03-21T10:33:59.245880+00:00"
    }

Using Python:

.. code-block:: console

   $ ipython
   In [1]: import requests
   In [2]: headers = {'Accept': 'application/json'}
   In [3]: r = requests.get('http://192.168.50.10/api/records/117', headers=headers)
   In [4]: r.status_code
   Out[4]: 200
   In [5]: r.json()
   Out[5]:
   {'created': '2017-03-21T00:01:27.933711+00:00',
    'id': 117,
    'links': {'self': 'http://192.168.50.10/api/records/117'},
    'metadata': {'__order__': ['title_statement', 'main_entry_personal_name'],
     '_oai': {'id': 'oai:invenio:recid/118', 'updated': '2017-03-21T00:01:27Z'},
     'control_number': '118',
     'main_entry_personal_name': {'__order__': ['personal_name'],
      'personal_name': 'Doe, John'},
     'title_statement': {'__order__': ['title'], 'title': 'This is title'}},
    'updated': '2017-03-21T00:01:27.933721+00:00'}

Multiple output formats
-----------------------

You can obtain information in other formats by setting an appropriate Accept
header. Invenio REST API endpoint will read this information and invoke
appropriate record serialisation.

For example, the Invenio demo site runs an ILS flavour and so returns MARCXML by
default:

.. code-block:: console

    $ curl http://192.168.50.10/api/records/117
    <?xml version='1.0' encoding='UTF-8'?>
    <record xmlns="http://www.loc.gov/MARC21/slim">
      <datafield tag="245" ind1=" " ind2=" ">
        <subfield code="a">This is title</subfield>
      </datafield>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Doe, John</subfield>
      </datafield>
    </record>

We can ask for Dublin Core:

.. code-block:: console

    $ curl -H 'Accept: application/xml' http://192.168.50.10/api/records/117
    <?xml version='1.0' encoding='UTF-8'?>
    <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
      <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">This is title</dc:title>
      <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Doe, John</dc:creator>
      <dc:type xmlns:dc="http://purl.org/dc/elements/1.1/"/>
      <dc:language xmlns:dc="http://purl.org/dc/elements/1.1/"/>
    </oai_dc:dc>

Getting record fields
---------------------

Getting title
~~~~~~~~~~~~~

If we would like to obtain only some part of information, for example record
title, we can simply filter the output fields.

Using CLI:

.. code-block:: console

   $ curl -s -H 'Accept: application/json' http://192.168.50.10/api/records/117 | \
     jq -r '.metadata.title_statement.title'
   This is title

Using Python:

.. code-block:: console

   $ ipython
   In [1]: import requests
   In [2]: headers = {'Accept': 'application/json'}
   In [3]: r = requests.get('http://192.168.50.10/api/records/117', headers=headers)
   In [4]: r.json()['metadata'].get('title_statement',{}).get('title','')
   Out[4]: 'This is title'

Getting co-authors
~~~~~~~~~~~~~~~~~~

If we would like to print all co-author names, we can iterate over respective
JSON field as follows:

Using CLI:

.. code-block:: console

   $ curl -s -H 'Accept: application/json' http://192.168.50.10/api/records/97 | \
     jq -r '.metadata.added_entry_personal_name[].personal_name'
   Lokajczyk, T
   Xu, W
   Jastrow, U
   Hahn, U
   Bittner, L
   Feldhaus, J

Using Python:

.. code-block:: console

   $ ipython
   In [1]: import requests
   In [2]: headers = {'Accept': 'application/json'}
   In [3]: r = requests.get('http://192.168.50.10/api/records/97', headers=headers)
   In [3]: for coauthor in r.json()['metadata']['added_entry_personal_name']:
   ......:     print(coauthor['personal_name'])
   Lokajczyk, T
   Xu, W
   Jastrow, U
   Hahn, U
   Bittner, L
   Feldhaus, J

Searching records
-----------------

Invenio instance can be searched programmatically via the REST API endpoint:

.. code-block:: console

   $ curl -H 'Accept: application/json' http://192.168.50.10/api/records?q=model

Note the pagination of the output done by the "links" output field.

How many records are there that contain the word "model"? We need to iterate
over results:

.. code-block:: Python

    nb_hits = 0

    def get_nb_hits(json_response):
        return len(json_response['hits']['hits'])

    def get_next_link(json_response):
        return json_response['links'].get('next', None)

    response = requests.get('http://192.168.50.10/api/records?q=model', headers=headers).json()
    nb_hits += get_nb_hits(response)
    while get_next_link(response):
        response = requests.get(get_next_link(response), headers=headers).json()
        nb_hits += get_nb_hits(response)

    print(nb_hits)
