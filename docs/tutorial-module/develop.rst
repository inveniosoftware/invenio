..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

.. _develop:

Form, views and templates
=========================
In this tutorial we'll see how to add data to our Invenio application.
To accomplish this we will cover several parts of the development process such as:

- How to create a form
- How to create a new view
- How to add a utility function
- How to add new templates
- How to use Jinja2
- How to define your own JSON Schema

Flask extensions
^^^^^^^^^^^^^^^^
It is important to understand that Invenio modules are just regular
`Flask extensions
<http://flask.pocoo.org/docs/1.0/extensiondev/#extension-dev>`_. The Flask
documentation contains extensive documentation on the APIs, design patterns
and in general how to develop with Flask, and it is highly recommended that you
follow Flask tutorials to understand the basics of Flask.

1. Create the form
^^^^^^^^^^^^^^^^^^
First, let's create a Python module that contains the forms of our project, we
will use `Flask-WTF <http://flask-wtf.readthedocs.io/en/stable/>`_.


In ``invenio_unicorn/forms.py``

.. code-block:: python

    """Forms module."""

    from __future__ import absolute_import, print_function

    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, validators


    class RecordForm(FlaskForm):
        """Custom record form."""

        title = StringField(
            'Title', [validators.DataRequired()]
        )
        description = TextAreaField(
            'Description', [validators.DataRequired()]
        )

2. Create the views
^^^^^^^^^^^^^^^^^^^

In ``invenio_unicorn/views.py`` we'll create the endpoints for

- ``create``: Form template
- ``success``: Success template

and register all the views to our application.

.. code-block:: python

    """Invenio module that adds more fun to the platform."""

    from __future__ import absolute_import, print_function

    from flask import Blueprint, redirect, render_template, request, url_for
    from flask_babelex import gettext as _
    from invenio_records import Record
    from invenio_records.models import RecordMetadata

    from .forms import RecordForm
    from .utils import create_record

    blueprint = Blueprint(
        'invenio_unicorn',
        __name__,
        template_folder='templates',
        static_folder='static',
    )


    @blueprint.route("/")
    def index():
        """Basic view."""
        return render_template(
            "invenio_unicorn/index.html",
            module_name=_('Invenio-Unicorn'))


    @blueprint.route('/create', methods=['GET', 'POST'])
    def create():
        """The create view."""
        form = RecordForm()
        # if the form is valid
        if form.validate_on_submit():
            # create the record
            create_record(
                dict(
                    title=form.title.data,
                    description=form.description.data
                )
            )
            # redirect to the success page
            return redirect(url_for('invenio_unicorn.success'))

        records = _get_all()
        return render_template('invenio_unicorn/create.html', form=form, records=records)


    def _get_all():
        """Return all records."""
        return [Record(obj.json, model=obj) for obj in RecordMetadata.query.all()]


    @blueprint.route("/success")
    def success():
        """The success view."""
        return render_template('invenio_unicorn/success.html')


3. Create the templates
^^^^^^^^^^^^^^^^^^^^^^^

And now, let's create the templates.

We create a `create.html` template in ``invenio_unicorn/templates/invenio_unicorn/``
where we can override the ``page_body`` block, to place our form:

.. code-block:: html

    {% extends config.UNICORN_BASE_TEMPLATE %}

    {% macro errors(field) %}
      {% if field.errors %}
      <span class="help-block">
        <ul class=errors>
        {% for error in field.errors %}
          <li>{{ error }}</li>
        {% endfor %}
        </ul>
      </span>
      {% endif %}
    {% endmacro %}

    {% block page_body %}
      <div class="container">
        <div class="row">
          <div class="col-md-12">
            <div class="alert alert-warning">
              <b>Heads up!</b> This example is for demo proposes only
            </div>
            <h2>Create record</h2>
          </div>
          <div class="col-md-offset-3 col-md-6 well">
            <form action="{{ url_for('invenio_unicorn.create') }}" method="POST">
                <div class="form-group {{ 'has-error' if form.title.errors }}">
                  <label for="title">{{ form.title.label }}</label>
                  {{ form.title(class_="form-control")|safe }}
                  {{ errors(form.title) }}
                </div>
                <div class="form-group {{ 'has-error' if form.description.errors }}">
                  <label for="description">{{ form.description.label }}</label>
                  {{ form.description(class_="form-control")|safe }}
                  {{ errors(form.description) }}
                </div>
                {{ form.csrf_token }}
                <button type="submit" class="btn btn-default">Submit</button>
            </form>
          </div>
        </div>
        <hr />
        <div class="row">
          <div class="col-md-12">
            {% if records %}
            <h2>Records created</h2>
            <ol id="custom-records">
                {% for record in records %}
                <li>{{record.title}}</li>
                {% endfor %}
            </ol>
            {% endif %}
          </div>
        </div>
      </div>
    {% endblock page_body %}

And finally, the `success.html` page in
`invenio_unicorn/templates/invenio_unicorn/` which will be rendered after a
record is created.

.. code-block:: html

    {% extends config.UNICORN_BASE_TEMPLATE %}

    {% block page_body %}
      <div class="container">
        <div class="row">
          <div class="col-md-12">
            <div class="alert alert-success">
              <b>Success!</b>
            </div>
            <a href="{{ url_for('invenio_unicorn.create') }}" class="btn btn-warning">Create more</a>
            <hr />
            <center>
              <iframe src="//giphy.com/embed/WZmgVLMt7mp44" width="480" height="480" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/kawaii-colorful-unicorn-WZmgVLMt7mp44">via GIPHY</a></p>
            </center>
          </div>
        </div>
      </div>
    {% endblock page_body %}

4. Create the record creation function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``utils.py`` file contains all helper functions of our module,
so let's write the first utility that will create a record.

In ``invenio_unicorn/utils.py``

.. code-block:: python

    """Utils module."""
    from __future__ import absolute_import, print_function

    import uuid

    from flask import current_app

    from invenio_db import db
    from invenio_indexer.api import RecordIndexer
    from invenio_pidstore import current_pidstore
    from invenio_records.api import Record


    def create_record(data):
        """Create a record.

        :param dict data: The record data.
        """
        indexer = RecordIndexer()
        # create uuid
        rec_uuid = uuid.uuid4()
        # add the schema
        data["$schema"] = \
            current_app.extensions['invenio-jsonschemas'].path_to_url(
                'records/custom-record-v1.0.0.json'
            )
        # create PID
        current_pidstore.minters['recid'](rec_uuid, data)
        # create record
        created_record = Record.create(data, id_=rec_uuid)
        db.session.commit()

        # index the record
        indexer.index(created_record)

5. Create the custom-record JSON Schema
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As you can see, our records use a custom schema. To define and use this schema,
we need to write the ``custom-record-v1.0.0.json`` inside the ``records``
folder of your data model project (``my-datamodel`` from the Quickstart
tutorial :ref:`customize`).

In ``my-datamodel/my-datamodel/jsonschemas/records/custom-record-v1.0.0.json``

.. code-block:: json

    {
      "$schema": "http://json-schema.org/draft-04/schema#",
      "id": "http://localhost/schemas/records/custom-record-v1.0.0.json",
      "additionalProperties": true,
      "title": "my-datamodel v1.0.0",
      "type": "object",
      "properties": {
        "title": {
          "description": "Record title.",
          "type": "string"
        },
        "description": {
          "description": "Record description.",
          "type": "string"
        },
        "id": {
          "description": "Invenio record identifier (integer).",
          "type": "string"
        }
      },
      "required": [
        "title",
        "description"
      ]
    }


Demo time
---------

Let's now see our Invenio module in action when integrated with our Invenio
instance.

First we install our new Invenio-Unicorn module. For the purposes of this guide,
our instance folder is `my-site`, and it's placed in the same root folder as
`invenio-unicorn`.

.. code-block:: console

    $ workon my-repository-venv
    (my-repository-venv)$ pip install --editable .[all]

Then, if you've followed the steps in the Quickstart guide, you can go to the
instance folder, `my-repository`, and start the ``server`` script:

    (my-repository-venv)$ cd ../my-site
    (my-repository-venv)$ ./scripts/server

Then go to ``http://localhost:5000/create`` and you will see the form we just
created. There are two fields ``Title`` and ``Description``.

Let's try the form, add something to the ``Title`` and click submit, you will
see the validation errors on the form, fill in the ``Description`` and click
submit. The form is now valid and it navigates you to the ``/success`` page.
