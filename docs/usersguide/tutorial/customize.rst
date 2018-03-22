..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.


.. _customise_invenio:

Customise Invenio
=================

The goal of this tutorial is to demonstrate basic Invenio customisation. We
shall modify the size logo, the page templates, the search facets, the sort
options, and more.

Install "beauty" module
-----------------------

First go in the virtual machine:

.. code-block:: console

    laptop> vagrant ssh web
    vagrant> workon invenio


Install the module ``invenio-beauty``:

.. code-block:: console

    vagrant> cd /vagrant/2-customization/invenio-beauty
    vagrant> pip install .
    vagrant> invenio collect
    vagrant> invenio run -h 0.0.0.0

Customize logo and templates
----------------------------

If you go to ``http://192.168.50.10/``, you will see the default Invenio,
but how we can customize it? Let's first stop invenio server.

Open with your favorite editor the ``~/.virtualenvs/invenio/var/instance/invenio.cfg``

1. Modify the logo
^^^^^^^^^^^^^^^^^^
Let's make our theme beautiful by replacing the logo

in the ``~/.virtualenvs/invenio/var/instance/invenio.cfg`` add the following:

.. code-block:: python

    THEME_LOGO = 'images/unicorn.png'
    THEME_FRONTPAGE_TITLE = 'Unicorn Institute'

Now if you run

.. code-block:: console

  vagrant> invenio run -h 0.0.0.0

and navigate to ``http://192.168.50.10`` you will see the new logo and front
page title.

2. Add facets
^^^^^^^^^^^^^

Let's replace the facets with the ``Authors`` adding the field
``main_entry_personal_name.personal_name``

in the ``~/.virtualenvs/invenio/var/instance/invenio.cfg`` add the following:

.. code-block:: python

    from invenio_records_rest.facets import terms_filter

    RECORDS_REST_FACETS = {
      'marc21': {
        'aggs': {
          'author': {
            'terms': {
              'field': 'main_entry_personal_name.personal_name'
            }
          }
        },
        'post_filters': {
          'author': terms_filter('main_entry_personal_name.personal_name')
        }
      }
    }

Now if you run

.. code-block:: console

  vagrant> invenio run -h 0.0.0.0

and navigate to ``http://192.168.50.10/search`` you will see that the facets
have been replaced with the ``Authors``.

3. Add sort options
^^^^^^^^^^^^^^^^^^^

in the ``~/.virtualenvs/invenio/var/instance/invenio.cfg`` add the following:

.. code-block:: python

  RECORDS_REST_SORT_OPTIONS = {
    'records': {
      'title': {
        'fields': ['title_statement.title'],
        'title': 'Record title',
        'order': 1,
      }
    }
  }

Now if you run

.. code-block:: console

  vagrant> invenio run -h 0.0.0.0

and navigate to ``http://192.168.50.10/search`` you will see that the sort list
have been replaced with the ``Record title``.


4. Change a detail view
^^^^^^^^^^^^^^^^^^^^^^^

We will now replace the template for the detail view of the record, this is possible
by changing ``RECORDS_UI_ENDPOINTS`` with the desired template. In our case
we have created the following:

in the ``/vagrant/2-customization/invenio-beauty/invenio_beauty/templates/detail.html``

.. code-block:: python

  {%- extends config.RECORDS_UI_BASE_TEMPLATE %}

  {%- macro record_content(data) %}
    {% for key, value in data.items() recursive %}
      <li class="list-group-item">
      {% if value is mapping %}
          <strong>{{ key }}:</strong>
          <ul class="list-group">{{ loop(value.items()) }}</ul>
      {% elif value is iterable and value is not string %}
          <strong>{{ key }}:</strong>
          <ol>
          {% for item in value %}
            <li>
            {% if item is mapping %}
              <ul class="list-group">
                {{ record_content(item) }}
              </ul>
            {% else %}
              {{ item }}
            {% endif %}
            </li>
          {% endfor %}
          </ol>
      {% else %}
        <strong>{{ key }}:</strong> {{ value }}
      {% endif %}
      </li>
    {% endfor %}
  {%- endmacro %}

  {%- block page_body %}
    <div class="container">
      <div class="row">
        <div class="col-md-12">
          <h2> {{ record.title_statement.title }}</h2>
          <hr />
          <p class="lead">{{ record.summary[0].summary }}</p>
          <hr />
          <h3> {{ _('Metadata') }}</h3>
          <div calss="well">
            {{ record_content(record) }}
          </div>
        </div>
      </div>
    </div>
  {%- endblock %}



in the ``~/.virtualenvs/invenio/var/instance/invenio.cfg`` add the following:

.. code-block:: python

  RECORDS_UI_ENDPOINTS = {
    "recid": {
        "pid_type": "recid",
        "route": "/records/<pid_value>",
        "template": "invenio_beauty/detail.html"
    },
  }

Now if you run

.. code-block:: console

  vagrant> invenio run -h 0.0.0.0

and navigate to ``http://192.168.50.10/records/1`` you will see the new template.

5. Modify search results template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now replace the search results template, in the search result we are
using angular templates and they can easily configured from the following vars:

- SEARCH_UI_JSTEMPLATE_COUNT
- SEARCH_UI_JSTEMPLATE_ERROR
- SEARCH_UI_JSTEMPLATE_FACETS
- SEARCH_UI_JSTEMPLATE_RANGE
- SEARCH_UI_JSTEMPLATE_LOADING
- SEARCH_UI_JSTEMPLATE_PAGINATION
- SEARCH_UI_JSTEMPLATE_RESULTS
- SEARCH_UI_JSTEMPLATE_SELECT_BOX
- SEARCH_UI_JSTEMPLATE_SORT_ORDER

For our example we will change only ``SEARCH_UI_JSTEMPLATE_RESULTS``, the
location of the angular templates are ``static/templates/<name of your module>``

in ``/vagrant/2-customization/invenio-beauty/invenio_beauty/static/templates/invenio_beauty/results.html``

.. code-block:: html

  <ol>
    <li ng-repeat="record in vm.invenioSearchResults.hits.hits track by $index">
      <span class="label label-success">{{ record.metadata.language_code[0].language_code_of_text_sound_track_or_separate_title[0] }}</span>
      <h4><a target="_self" ng-href="/records/{{ record.id }}">{{ record.metadata.title_statement.title }}</a></h4>
      <p>{{ record.metadata.summary[0].summary }}</p>
    </li>
  </ol>

On the angular templates, you have access to the record metadata object, so in you templates
you can use ``{{ record.metadata.foo }}``.

Now in the search results template, we will display the language tag on top of each record
``language_code``.

in the ``~/.virtualenvs/invenio/var/instance/invenio.cfg`` add the following:

.. code-block:: python

  SEARCH_UI_JSTEMPLATE_RESULTS = 'templates/invenio_beauty/results.html'

Now if you run

.. code-block:: console

  vagrant> invenio collect -v
  vagrant> invenio run -h 0.0.0.0

and navigate to ``http://192.168.50.10/search`` you will see the new template.

6. Change the homepage template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We will now replace the demo's homepage. You can change the whole homepage just
by replacing ``THEME_FRONTPAGE_TEMPLATE`` with your own template, for this
example we have created the following:

in ``/vagrant/2-customization/invenio-beauty/invenio_beauty/templates/invenio_beauty/home.html``

.. code-block:: python

    {%- extends "invenio_theme/page.html" %}

    {%- block navbar_search %}{% endblock %}
    {%- block page_body %}
      <div class="container">
        <div class="row">
          <div class="col-lg-12">
            <h1 class="text-center">
              {{_(config.THEME_FRONTPAGE_TITLE)}} Search
            </h1>
            <form action="/search">
              <div class="form-group">
                <input type="text" name="q" class="form-control" placeholder="Type and press enter to search">
              </div>
            </form>
          </div>
        </div>
      </div>
    {%- endblock %}

If you have a closer look, you will see that we have access to different config
variables on the template, by using the ``config``. For example if we want to
display the ``THEME_FRONTPAGE_TITLE`` we can you ``config.THEME_FRONTPAGE_TITLE``

So the only thing we should do is to edit the ``config.py``

in the ``~/.virtualenvs/invenio/var/instance/invenio.cfg`` add the following:

.. code-block:: python

  THEME_FRONTPAGE_TEMPLATE = 'invenio_beauty/home.html'


Now if you run

.. code-block:: console

  vagrant> invenio run -h 0.0.0.0

and navigate to ``http://192.168.50.10`` you will see the new template.

Everything together
-------------------

You want to see the results? Just run the following command.

.. code-block:: console

    vagrant> cd /vagrant/iugw2017/2-customization
    vagrant> cat final.cfg >> ~/.virtualenvs/invenio/var/instance/invenio.cfg
