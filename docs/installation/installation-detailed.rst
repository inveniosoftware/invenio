..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

Detailed installation guide
===========================

.. admonition:: CAVEAT LECTOR

   Invenio v3.0 alpha is a bleeding-edge developer preview version that is
   scheduled for public release in Q1/2016.

Prerequisites
-------------

Invenio v3.0 needs several prerequisite software packages to function:

- `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_
- `PostgreSQL <http://www.postgresql.org/>`_
- `RabbitMQ <http://www.rabbitmq.com/>`_
- `Redis <http://redis.io/>`_

For example, on Debian GNU/Linux, you can install them as follows:

.. code-block:: shell

   sudo apt-get install elasticsearch \
                        postgresql \
                        rabbitmq-server \
                        redis-server

Installation
------------

Let's start by creating a new virtual environment that will hold our Invenio
v3.0 instance:

.. code-block:: shell

   mkvirtualenv invenio3mysite

Install Invenio v3.0 base package and most of their available modules (using
option ``full`` as opposed to using option ``minimal``):

.. code-block:: shell

   cdvirtualenv
   mkdir src && cd src
   pip install invenio[full]

Create a new instance of Invenio named "mysite":

.. code-block:: shell

   inveniomanage instance create mysite

Run bower to install any necessary JavaScript assets the Invenio modules
depend on:

.. code-block:: shell

   cd mysite
   python manage.py bower
   cdvirtualenv var/mysite-instance/
   bower install
   cd -
   python manage.py collect -v
   python manage.py assets build

Create database to hold persistent data:

.. code-block:: shell

   python manage.py db init
   python manage.py db create

Create a user account:

.. code-block:: shell

   python manage.py accounts usercreate -e info@inveniosoftware.org -a

Start Celery worker to execute tasks:

.. code-block:: shell

   # temporary step (ensures celery tasks are discovered)
   echo "from invenio_records.tasks import *" >> mysite/celery.py
   # run celery worker (in a new window)
   celery worker -A mysite.celery -l INFO

Now we can create our first record:

.. code-block:: shell

   echo '{"title":"Invenio 3 Rocks", "recid": 1}'| \
        python manage.py records create

Start the web application (in debugging mode):

.. code-block:: shell

   python manage.py --debug run

We should now see our record on ``http://localhost:5000/records/1`` and we can
access it via REST API:

.. code-block:: shell

   curl -i -H "Accept: application/json" \
        http://localhost:5000/api/records/1
