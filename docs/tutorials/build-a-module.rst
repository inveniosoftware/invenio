..
    This file is part of Invenio.
    Copyright (C) 2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Build a module
==============

Invenio modules are independent, interchangeable components that add functionality.
A full invenio application consists of a set of modules, and can be customized easily by adding or
removing specific modules.
All modules have the same structure, which is defined in the
`cookiecutter-invenio-module <https://github.com/inveniosoftware/cookiecutter-invenio-module>`_
template.

Invenio module layout
---------------------

A simple module may have the following folder structure::

    invenio-foo/
        docs/
        examples/
        invenio_foo/
            templates/invenio_foo/
            __init__.py
            config.py
            ext.py
            version.py
            views.py
        tests/
        *.rst
        run-tests.sh
        setup.py

These files are described in the sections below.

\*.rst files
++++++++++++

All these files are used by people who want to know more about your module (mainly developers).

- ``README.rst`` is used to describe your module. You can see the short
  description written in the Cookiecutter here. You should update it with
  more details.
- ``AUTHORS.rst`` should list all contributors to this module.
- ``CHANGES.rst`` should be updated at every release and store the list of
  versions with the list of changes (changelog).
- ``CONTRIBUTING.rst`` presents the rules to contribute to your module.
- ``INSTALL.rst`` describes how to install your module.

setup.py
++++++++

First, there is the ``setup.py`` file, one of the most important: this file is
executed when you install your module with *pip*. If you open it, you can see
several parts.

On the top, the list of the requirements:

- For normal use.
- For development.
- For tests.

Depending on your needs, you can install only part of the requirements, or
everything (``pip install invenio-foo[all]``).

Then, in the ``setup()`` function, you can find the description of your module with
the values entered in cookiecutter. At the end, you can find the
``entrypoints`` section.

run-tests.sh
++++++++++++
This is used to run a list of tests locally, to make sure that your module works
as intended. It will generate the documentation, run *pytest* and any remaining
checks.

docs folder
+++++++++++
This folder contains the settings to generate documentation for your module,
along with files where you can write the documentation. When you run the
``run-tests.sh`` script, it will create the documentation in HTML files in a
sub-folder.

examples folder
+++++++++++++++
Here you can find a small example of how to use your module. You can test it,
follow the steps described in the :ref:`run-the-example-app` section.

tests folder
++++++++++++
Here are all the tests for your application, that will be run when
you execute the ``run-tests.sh`` script. If all these tests pass, you can
safely commit your work.

See `pytest-invenio <https://pytest-invenio.readthedocs.io/en/latest/>`_ for
how to structure your tests.

invenio_foo folder
++++++++++++++++++
This folder has the name of your module, in lower case with the dash changed
to an underscore. It contains the code of your module. You can add any code files
here, organized as you wish.

The files that already exist are standard, and are covered 
in the following sections. A rule of thumb is that if you need multiple
files for one action (for instance, 2 ``views``: one for the API and a standard
one), create a folder having the name of the file you want to split (here, a
``views`` folder with ``ui.py`` and ``api.py`` inside).

MANIFEST.in
>>>>>>>>>>>
This file lists all the files included in the sub-folders. It should
be updated before the first commit.

config.py
>>>>>>>>>
All configuration variables should be declared in this file.

ext.py
>>>>>>
This file contains a class that extends the Invenio application
with your module. It registers the module during the initialization of the application
and loads the default configuration from ``config.py``. 

version.py
>>>>>>>>>>
File containing the version of your module.

views.py
>>>>>>>>
Here you declare the views or endpoints you want to expose. By default, it creates a
simple view on the root end point that renders a template.

templates
>>>>>>>>>
All your Jinja templates should be stored in this folder. A Jinja template is an HTML file that can be modified according to some parameters.

static
>>>>>>
If your module contains JavaScript or CSS files, they should go in a folder called ``static``. Also, if you want to group them in bundles,
you should add a ``bundles.py`` file next to the ``static`` folder.

Module naming conventions
-------------------------

Invenio modules are standalone independent components that implement some
functionality used by the rest of the Invenio ecosystem. Modules provide API
to other modules and use API of other modules.

A module is usually called:

1. with plural noun, meaning "database (of things)", for example
   ``invenio-records``, ``invenio-tags``, ``invenio-annotations``,

2. with singular noun, meaning "worker (using things)", for example
   ``invenio-checker``, ``invenio-editor``.

A module may have split its user interface and REST API interface, for example
``invenio-records-ui`` and ``invenio-records-rest``, to clarify dependencies and
offer easy customisation.

To create a new module, make sure to have
`cookiecutter <https://cookiecutter.readthedocs.io/en/latest/installation.html>`_
installed and run:

.. code-block:: console

    $ cookiecutter gh:inveniosoftware/cookiecutter-invenio-module
    project_name [Invenio-FunGenerator]: Invenio-Foo
    project_shortname [invenio-foo]:
    package_name [invenio_foo]:
    github_repo [inveniosoftware/invenio-foo]:
    description [Invenio module that adds more fun to the platform.]:
    author_name [CERN]:
    author_email [info@inveniosoftware.org]:
    year [2018]:
    copyright_holder [CERN]:
    copyright_by_intergovernmental [True]:
    superproject [Invenio]:
    transifex_project [invenio-foo]:
    extension_class [InvenioFoo]:
    config_prefix [FOO]:

Integrating a new module to a full Invenio application
comes down to adding it as a dependency in the central ``setup.py``, an example of which can be
seen in `Invenio-App-ILS <https://github.com/inveniosoftware/invenio-app-ils/blob/master/setup.py>`_.

Install the module
------------------

Before installing the new module, we need to **stop** any running Invenio instance.
First, create a virtualenv for the module:

.. code-block:: bash

    $ mkvirtualenv my-module-venv

Installing the module is very easy, you just need to go to its root directory
and `pip install` it:

.. code-block:: bash

    (my-module-venv)$ cd invenio-foo/
    (my-module-venv)$ pip install --editable .[all]

Some explanations about the command:

- The ``--editable`` option is used for development. It means that if you change the
  files in the module, you won't have to reinstall it to see the changes. In a
  production environment, this option shouldn't be used.
- The ``.`` is in fact the path to your module. As we are in the root folder of
  the module, we can just say *here*, which is what the dot means.
- The ``[all]`` after the dot means we want to install all dependencies, which
  is common when developing. Depending on your use of the module, you can
  install only parts of it:

    - The default (nothing after the dot) installs the minimum to make the
      module run.
    - ``[tests]`` installs the requirements to test the module.
    - ``[docs]`` installs the requirements to build the documentation.
    - Some modules have extra options.

If you need multiple options, you can chain them: ``[tests,docs]``.

.. _run-the-tests:

Run the tests
-------------
In order to run the tests, you need to have a valid git repository. The
following step needs to be run only once. Go in the root folder of the module:

.. code-block:: bash

    (my-module-venv)$ git init
    (my-module-venv)$ git add --all
    (my-module-venv)$ check-manifest --update

What we have done:

- Change the folder into a git repository, so it can record the changes made to
  the files.
- Add all the files to this repository.
- Update the file ``MANIFEST.in`` (this file controls which files are included
  in your Python package when it is created and installed).

Now, we are able to run the tests:

.. code-block:: bash

    (my-module-venv)$ ./run-tests.sh

.. _run-the-example-app:

Run the example application
---------------------------
The example application is a minimal application that presents the features of your
module. The example application is useful during development for testing.
By default, it simply prints a welcome page.
To try it, go into the ``examples`` folder and run:

.. code-block:: console

    (my-module-venv)$ ./app-setup.sh
    (my-module-venv)$ ./app-fixtures.sh
    (my-module-venv)$ export FLASK_APP=app.py FLASK_DEBUG=1
    (my-module-venv)$ flask run

You can now open a browser and go to the URL http://localhost:5000/ where you
should be able to see a welcome page.

To clean the server, run the ``./app-teardown.sh`` script after stopping the
server.

Build the documentation
-----------------------
The documentation can be built with the ``run-tests.sh`` script, but you need
to have installed the package with its *tests* requirements. If you just want to build the
documentation, you will only need the *docs* requirements (see the install
section above). Make sure you are at the root directory
of the module and run:

.. code-block:: console

    (my-module-venv)$ python setup.py build_sphinx

Open ``docs/_build/html/index.html`` in browser and voilà, the documentation is
there.

Publishing on GitHub
--------------------
Before going further in the tutorial, we can publish your repository to GitHub.
This allows to integrate a continuous integration system such as TravisCI and allow for
easy publishing of your module to PyPI afterwards.

First, create an empty repository in your GitHub account. Be sure not to
generate any *.gitignore* or *README* files, as our code already has them. If
you don't have a GitHub account, you can skip this step, it is only necessary
if you plan to publish your module on PyPI.

Now, go into the root directory of your module, and run

.. code-block:: bash

    $ git remote add origin URL-OF-YOUR-GITHUB-REPO

We can commit and push the generated files:

.. code-block:: bash

    $ git commit -am "Initial module structure"
    $ git push --set-upstream origin master

Finally, we create a new branch to develop on it

.. code-block:: bash

    $ git checkout -b dev

Form, views and templates
-------------------------
In this tutorial we'll see how to add data to our Invenio application.
To accomplish this we will cover several parts of the development process such as:

- How to create a form.
- How to create a new view.
- How to add a utility function.
- How to add new templates.
- How to use Jinja2.
- How to define your own JSON Schema.

Flask extensions
++++++++++++++++
It is important to understand that Invenio modules are just regular
`Flask extensions
<http://flask.pocoo.org/docs/1.0/extensiondev/#extension-dev>`_. The Flask
documentation contains extensive documentation on the APIs, design patterns
and in general how to develop with Flask, and it is highly recommended that you
follow Flask tutorials to understand the basics of Flask.

1. Create the form
++++++++++++++++++
First, let's create a Python module that contains the forms of our project, we
will use `Flask-WTF <http://flask-wtf.readthedocs.io/en/stable/>`_.


In ``invenio_foo/forms.py``

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
+++++++++++++++++++

In ``invenio_foo/views.py`` we'll create the endpoints for

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
        'invenio_foo',
        __name__,
        template_folder='templates',
        static_folder='static',
    )


    @blueprint.route("/")
    def index():
        """Basic view."""
        return render_template(
            "invenio_foo/index.html",
            module_name=_('invenio-foo'))


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
            return redirect(url_for('invenio_foo.success'))

        records = _get_all()
        return render_template('invenio_foo/create.html', form=form, records=records)


    def _get_all():
        """Return all records."""
        return [Record(obj.json, model=obj) for obj in RecordMetadata.query.all()]


    @blueprint.route("/success")
    def success():
        """The success view."""
        return render_template('invenio_foo/success.html')


3. Create the templates
+++++++++++++++++++++++

And now, let's create the templates.

We create a ``create.html`` template in ``invenio_foo/templates/invenio_foo/``
where we can override the ``page_body`` block, to place our form:

.. code-block:: html

    {% extends config.FOO_BASE_TEMPLATE %}

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
            <form action="{{ url_for('invenio_foo.create') }}" method="POST">
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
`invenio_foo/templates/invenio_foo/` which will be rendered after a
record is created.

.. code-block:: html

    {% extends config.FOO_BASE_TEMPLATE %}

    {% block page_body %}
      <div class="container">
        <div class="row">
          <div class="col-md-12">
            <div class="alert alert-success">
              <b>Success!</b>
            </div>
            <a href="{{ url_for('invenio_foo.create') }}" class="btn btn-warning">Create more</a>
            <hr />
            <center>
              <iframe src="//giphy.com/embed/WZmgVLMt7mp44" width="480" height="480" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/kawaii-colorful-unicorn-WZmgVLMt7mp44">via GIPHY</a></p>
            </center>
          </div>
        </div>
      </div>
    {% endblock page_body %}

4. Write the record creation function
+++++++++++++++++++++++++++++++++++++

The ``utils.py`` file contains all helper functions of our module,
so let's write the first utility that will create a record.

In ``invenio_foo/utils.py``

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
+++++++++++++++++++++++++++++++++++++++

Our records can use a custom schema. To define and use this schema,
we create the ``custom-record-v1.0.0.json`` file inside the ``records``
folder of your data model project (``my-datamodel`` from the Quickstart
tutorial :ref:`build-data-model`).

In ``my-datamodel/my-datamodel/jsonschemas/records/custom-record-v1.0.0.json``:

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

Let's now see our Invenio module in action after it is integrated with our Invenio instance.

First we install our new invenio-foo module:

.. code-block:: console

    $ pipenv install --editable .[all]

Then, if you've followed the steps in the :ref:`quickstart` guide, you can go to the
instance folder, `my-repository`, and start the ``server`` script:

.. code-block:: console

    $ cd ../my-site
    $ pipenv run ./scripts/server

Then go to ``http://localhost:5000/create`` and you will see the form we just
created. There are two fields ``Title`` and ``Description``.

Let's try the form, add something to the ``Title`` and click submit, you will
see the validation errors on the form, fill in the ``Description`` and click
submit. The form is now valid and it navigates you to the ``/success`` page.
