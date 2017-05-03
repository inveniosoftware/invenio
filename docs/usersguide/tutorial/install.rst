.. _install_invenio:

Install Invenio
===============

Now that all the prerequisites have been set up in :ref:`install_prerequisites`,
we can proceed with the installation of the Invenio itself. The installation is
happening on the web node (192.168.50.10).

We start by creating and configuring a new Invenio instance, continue by
populating it with some example records, and finally we start the web
application. This can be done in an automated unattended way by running the
following scripts:

.. code-block:: shell

   source .inveniorc
   ./scripts/create-instance.sh
   ./scripts/populate-instance.sh
   ./scripts/start-instance.sh

.. note::

   If you want to install the very-bleeding-edge Invenio packages from GitHub,
   you can run the ``create-instance.sh`` script with the ``--devel`` argument::

     ./scripts/create-instance.sh --devel

Let’s see in detail about every Invenio installation step.

Create instance
~~~~~~~~~~~~~~~

We start by creating a fresh new Python virtual environment that will hold our
brand new Invenio v3.0 instance:

.. include:: ../../../scripts/create-instance.sh
   :start-after: # sphinxdoc-create-virtual-environment-begin
   :end-before: # sphinxdoc-create-virtual-environment-end
   :literal:

We continue by installing Invenio v3.0 Integrated Library System flavour demo
site from PyPI:

.. include:: ../../../scripts/create-instance.sh
   :start-after: # sphinxdoc-install-invenio-full-begin
   :end-before: # sphinxdoc-install-invenio-full-end
   :literal:

Let's briefly customise our instance with respect to the location of the
database server, the Redis server, the Elasticsearch server, and all the other
dependent services in our multi-server environment:

.. include:: ../../../scripts/create-instance.sh
   :start-after: # sphinxdoc-customise-instance-begin
   :end-before: # sphinxdoc-customise-instance-end
   :literal:

In the instance folder, we run Npm to install any JavaScript libraries that
Invenio needs:

.. include:: ../../../scripts/create-instance.sh
   :start-after: # sphinxdoc-run-npm-begin
   :end-before: # sphinxdoc-run-npm-end
   :literal:

We can now collect and build CSS/JS assets of our Invenio instance:

.. include:: ../../../scripts/create-instance.sh
   :start-after: # sphinxdoc-collect-and-build-assets-begin
   :end-before: # sphinxdoc-collect-and-build-assets-end
   :literal:

Our first new Invenio instance is created and ready for loading some example
records.

Populate instance
~~~~~~~~~~~~~~~~~

We proceed by creating a dedicated database that will hold persistent data of
our installation, such as bibliographic records or user accounts. The database
tables can be created as follows:

.. include:: ../../../scripts/populate-instance.sh
   :start-after: # sphinxdoc-create-database-begin
   :end-before: # sphinxdoc-create-database-end
   :literal:

We continue by creating a user account:

.. include:: ../../../scripts/populate-instance.sh
   :start-after: # sphinxdoc-create-user-account-begin
   :end-before: # sphinxdoc-create-user-account-end
   :literal:

We can now create the Elasticsearch indexes and initialise the indexing queue:

.. include:: ../../../scripts/populate-instance.sh
   :start-after: # sphinxdoc-index-initialisation-begin
   :end-before: # sphinxdoc-index-initialisation-end
   :literal:

We proceed by populating our Invenio demo instance with some example demo
MARCXML records:

.. include:: ../../../scripts/populate-instance.sh
   :start-after: # sphinxdoc-populate-with-demo-records-begin
   :end-before: # sphinxdoc-populate-with-demo-records-end
   :literal:

Start instance
~~~~~~~~~~~~~~

Let's now start the web application:

.. include:: ../../../scripts/start-instance.sh
   :start-after: # sphinxdoc-start-application-begin
   :end-before: # sphinxdoc-start-application-end
   :literal:

and the web server:

.. include:: ../../../scripts/start-instance.sh
   :start-after: # sphinxdoc-start-nginx-begin
   :end-before: # sphinxdoc-start-nginx-end
   :literal:

We should now see our demo records on the web:

.. code-block:: shell

   firefox http://${INVENIO_WEB_HOST}/records/1

and we can access them via REST API:

.. code-block:: shell

   curl -i -H "Accept: application/json" \
        http://${INVENIO_WEB_HOST}/api/records/1

We are done! Our first Invenio v3.0 demo instance is fully up and running.
