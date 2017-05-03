..
    This file is part of Invenio.
    Copyright (C) 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

Develop a module
================

The goal of this tutorial is to add data to Invenio v3. We'll create a
form that inserts the data in the database. Also we will touch different
part of the development process such as:

- How to create a new view
- How to create a form
- How to add a utility function
- How to add new templates
- How to use Jinja2

Requirements
------------

Before starting let's make sure we have ``custom-data-module`` installed on
your environment. We need that to ensure that we have the data model.

1. Create the form
^^^^^^^^^^^^^^^^^^

Ok, let's create a module that contains the forms of our project, we will use
Flask-WTF.


in ``invenio_unicorn/forms.py``

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

in ``invenio_unicorn/views.py`` we'll create the endpoints for

- ``create``: Form template
- ``success``: Success template

The ``views.py`` registers all the views of our application

.. code-block:: python

    """Invenio module that adds more fun to the platform."""

    from __future__ import absolute_import, print_function

    from flask import Blueprint, redirect, render_template, request, url_for
    from flask_babelex import gettext as _

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
        return render_template('invenio_unicorn/create.html', form=form)


    @blueprint.route("/success")
    def success():
        """The success view."""
        return render_template('invenio_unicorn/success.html')


3. Create the templates
^^^^^^^^^^^^^^^^^^^^^^^

And now, let's create the templates

in ``invenio_unicorn/templates/invenio_unicorn/create.html`` we override
two ``blocks`` from the invenio ``BASE_TEMPLATE`` and those are:

- javascript
- page_body

In the ``javascript`` block we will right a small fetcher, to get the
created records from the API, and in the ``page_body`` we will add the
form and the placeholder for the records list.

.. code-block:: html

    {%- extends config.BASE_TEMPLATE %}

    {% macro errors(field) %}
      {% if field.errors %}
      <span class="help-block">
        <ul class=errors>
        {% for error in field.errors %}
          <li>{{ error }}</li>
        {% endfor %}
        </ul>
      {% endif %}
      </span>
    {% endmacro %}

    {% block javascript %}
      {{ super() }}
      <script>
        $(document).ready(function() {
          $.get('/api/custom_records')
            .then(
              function(response) {
                $('#custom-records').html('');
                $.each(response.hits.hits, function(index, record) {
                  $('#custom-records').append(
                    '<li>' +
                      '<h4><a href="/custom_records/' + record.metadata.custom_pid + '">' + record.metadata.title + '</a></h4>' +
                      '<p>' + record.metadata.description + '</p>' +
                     '</li>'
                  );
                })
              }, function() {
                $('#custom-records').html('');
              }
            );
        });
      </script>
    {% endblock javascript %}

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
            <h2>Records created</h2>
            <ol id="custom-records">
              <div class="text-center">
                Loading records...
              </div>
            </ol>
          </div>
        </div>
      </div>
    {% endblock page_body %}

in ``invenio_unicorn/templates/invenio_unicorn/success.html``

.. code-block:: html

    {%- extends config.BASE_TEMPLATE %}

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

in ``invenio_unicorn/utils.py``

On the ``utils.py`` module will create a helper function that creates a record.

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
        with db.session.begin_nested():
            # create uuid
            rec_uuid = uuid.uuid4()
            # add the schema
            host = current_app.config.get('JSONSCHEMAS_HOST')
            data["$schema"] = \
                current_app.extensions['invenio-jsonschemas'].path_to_url(
                'custom_record/custom-record-v1.0.0.json')
            # create PID
            current_pidstore.minters['custid'](
              rec_uuid, data, pid_value='custom_pid_{}'.format(rec_uuid)
            )
            # create record
            created_record = Record.create(data, id_=rec_uuid)
            # index the record
            indexer.index(created_record)
        db.session.commit()

Demo time
---------

Let's start our server again.

.. code-block:: console

    vagrant> invenio run -h 0.0.0.0

Then go to ``http://192.168.50.10/create`` and you will see the form we just
created. There are two fields ``Title`` and ``Description``.

Let's try the form, add something to the ``Title`` and click submit, you will
see the validation errors on the form, fill in the ``Description`` and click
submit. The form is now valid and it navigates you to the ``/success`` page.
