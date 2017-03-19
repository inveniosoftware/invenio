.. _accessing_content:

Accessing content
=================

JSON representation
-------------------

Records are internally stored in JSON following a certain JSON Schema.
They can be obtained using REST API to records.

Using CLI:

.. code-block:: console

   $ curl http://192.168.50.10/api/records/117
   {

       "created": "2017-03-21T00:01:27.933711+00:00",
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
               "id": "oai:invenio:recid/118",
               "updated": "2017-03-21T00:01:27Z"
           },
           "control_number": "118",
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
       "updated": "2017-03-21T00:01:27.933721+00:00"

   }

Using Python:

.. code-block:: console

   $ ipython
   In [1]: import requests
   In [2]: r = requests.get('http://192.168.50.10/api/records/117')
   In [3]: r.status_code
   Out[3]: 200
   In [4]: r.json()
   Out[4]:
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
appropriate record serialisation. For example, to obtain a BibTeX representation
of a record:

.. code-block:: console

   $ curl -H 'Accept: application/x-bibtex' https://zenodo.org/api/records/46643
   @misc{himpe_2016_46643,
     author       = {Himpe, Christian and
                     Ohlberger, Mario},
     title        = {{Accelerating the Computation of Empirical Gramians
                      and Related Methods}},
     month        = feb,
     year         = 2016,
     note         = {Extended Abstract},
     doi          = {10.5281/zenodo.46643},
     url          = {https://doi.org/10.5281/zenodo.46643}

Getting record fields
---------------------

Getting title
~~~~~~~~~~~~~

If we would like to obtain only some part of information, for example record
title, we can simply filter the output fields.

Using CLI:

.. code-block:: console

   $ curl -s http://192.168.50.10/api/records/117 | \
     jq -r '.metadata.title_statement.title'
   This is title

Using Python:

.. code-block:: console

   $ ipython
   In [1]: import requests
   In [2]: r = requests.get('http://192.168.50.10/api/records/117')
   In [3]: r.json()['metadata'].get('title_statement',{}).get('title','')
   Out[3]: 'This is title'

Getting co-authors
~~~~~~~~~~~~~~~~~~

If we would like to print all co-author names, we can iterate over respective
JSON field as follows:

Using CLI:

.. code-block:: console

   $ curl -s http://192.168.50.10/api/records/97 | \
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
   In [2]: r = requests.get('http://192.168.50.10/api/records/97')
   In [2]: for coauthor in r.json()['metadata']['added_entry_personal_name']:
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

   $ curl http://192.168.50.10/api/records?q=model

Note the pagination of the output done by the "links" output field.

How many records are there that contain the word "model"? We need to iterate
over results:

.. code-block:: Python

    nb_hits = 0

    def get_nb_hits(json_response):
        return len(json_response['hits']['hits'])

    def get_next_link(json_response):
        return json_response['links'].get('next', None)

    response = requests.get('http://192.168.50.10/api/records?q=model').json()
    nb_hits += get_nb_hits(response)
    while get_next_link(response):
        response = requests.get(get_next_link(response)).json()
        nb_hits += get_nb_hits(response)

    print(nb_hits)
