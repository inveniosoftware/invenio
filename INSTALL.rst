Installation
============

The best way to get Invenio up running immediately is using our provided
Docker image:

.. code-block:: console

   $ pip install invenio[minimal]
   $ inveniomanage instance create mysite
   $ cd mysite
   $ docker-compose build
   $ docker-compose up

This will start an Invenio instance with all the related services you need such
as PostgreSQL, ElasticSearch, Redis, RabbitMQ.

For a detailed walk-through on how to setup your instance on Invenio, see `our
documentation
<http://pythonhosted.org/invenio/installation/installation-detailed.html>`_.
