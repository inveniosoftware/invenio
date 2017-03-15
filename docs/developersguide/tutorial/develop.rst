Part 3: Develop a module
========================

The goal of this tutorial is to add data to Invenio v3. We'll create a
form that inserts the data in the database. Also we will touch different
part of the development process such as:

- How to create a new view
- How to create a form
- How to add a utility function
- How to add new templates
- How to use Jinja2

Let's create a module that contains the forms of our project, we will use
Flask-WTF.

in ``invenio_unicorn/forms.py``

.. code-block:: python

    from flask_wtf import FlaskForm
    from wtforms import StringField, TextAreaField, validators


    class RecordForm(FlaskForm):

        title = StringField(
            'Title', [validators.DataRequired()]
        )
        description = TextAreaField(
            'Description', [validators.DataRequired()]
        )

in ``invenio_unicorn/views.py`` we'll create the endpoints for

- ``create``: Form template
- ``success``: Success template

The ``views.py`` registers all the views of our application

.. code-block:: python

    from __future__ import absolute_import, print_function

    from flask import Blueprint, render_template, redirect, request, url_for
    from flask_babelex import gettext as _

    from .forms import RecordForm
    from .utils import create_record

    blueprint = Blueprint(
        'invenio_unicorn',
        __name__,
        template_folder='templates',
        static_folder='static',
    )


    @blueprint.route('/create', methods=['GET', 'POST'])
    def create():
        """The index view."""
        form = RecordForm()
        # If the form is valid
        if form.validate_on_submit():
            # Create the record
            create_record(
              dict(
                title=form.title.data,
                description=form.description.data
              )
            )
            # Redirect to the success page
            return redirect(url_for('invenio_unicorn.success'))
        return render_template('invenio_unicorn/create.html', form=form)


    @blueprint.route("/success")
    def success():
        """The success view."""
        return render_template('invenio_unicorn/success.html')


in ``invenio_unicorn/utils.py``

On the ``utils.py`` module will create a helper function that creates a record.

.. code-block:: python

    from __future__ import absolute_import, print_function

    import uuid

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
            # create PID
            current_pidstore.minters['recid'](
              rec_uuid, data
            )
            # create record
            created_record = Record.create(data, id_=rec_uuid)
            # index the record
            indexer.index(created_record)
        db.session.commit()


And now, let's create the templates

in ``invenio_unicorn/templates/invenio_unicorn/create.html``

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

    {% block page_body %}
      <div class="container">
        <div class="row">
          <div class="col-md-offset-3 col-md-6">
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
