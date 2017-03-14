Part 3: Develop a module
========================

Let's create a module that contains the forms of our project

in ``invenio_unicorn/forms.py``

```python
from flask_wtf import Form
from wtforms.validators import DataRequired


class RecordForm(Form):

    title = StringField('title', validators=[DataRequired()])
    description = StringField('description', validators=[DataRequired()])
```

in ``invenio_unicorn/views.py``

The ``views.py`` registers all the views of our application

```python
from __future__ import absolute_import, print_function

from flask import Blueprint, render_template, request
from flask_babelex import gettext as _

from .forms import RecordForm
from .utils import create_record

blueprint = Blueprint(
    'invenio_unicorn',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
  """The index view."""
  form = RecordForm(request.form)
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
  return render_template('create.html', form=form)


@blueprint.route("/success")
def success():
  """The success view."""
  return render_template('success.html')
```

in ``invenio_unicorn/utils.py``

On the ``utils.py`` module will create a helper function that creates a record.

```python

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
```

And now, let's modify the templates used by the views

in ``invenio_unicorn/templates/invenio_unicorn/create.html``

```html
{%- extends config.BASE_TEMPLATE %}

{% block page_body %}
  <form action="url_for('invenio_unicorn.index')" method="post">
    {{ form.title }}
    {{ form.description }}
  </form>
{% endblock page_body %}
```

in ``invenio_unicorn/templates/invenio_unicorn/success.html``

```html
{%- extends config.BASE_TEMPLATE %}

{% block page_body %}
  <center>
    <img src="https://media.giphy.com/media/3osxYamKD88c6pXdfO/giphy.gif" />
  </center>
{% endblock page_body %}
```
