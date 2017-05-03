..  This file is part of Invenio
    Copyright (C) 2014, 2015, 2016, 2017 CERN.

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

.. _quickstart:

Quickstart
==========

Using Docker
------------

You can get Invenio v3.0 demo site up and running using Docker::

  docker-compose build
  docker-compose up -d
  docker-compose run --rm web ./scripts/populate-instance.sh
  firefox http://127.0.0.1/records/1

Using Vagrant
-------------

You can get Invenio v3.0 demo site up and running using Vagrant::

  vagrant up
  vagrant ssh web -c 'source .inveniorc && /vagrant/scripts/create-instance.sh'
  vagrant ssh web -c 'source .inveniorc && /vagrant/scripts/populate-instance.sh'
  vagrant ssh web -c 'source .inveniorc && nohup /vagrant/scripts/start-instance.sh'
  firefox http://192.168.50.10/records/1

Using kickstart scripts
-----------------------

You can set some environment variables and run kickstart provisioning and
installation scripts manually::

  vim .inveniorc
  source .inveniorc
  scripts/provision-web.sh
  scripts/provision-postgresql.sh
  scripts/provision-elasticsearch.sh
  scripts/provision-redis.sh
  scripts/provision-rabbitmq.sh
  scripts/provision-worker.sh
  scripts/create-instance.sh
  scripts/populate-instance.sh
  scripts/start-instance.sh
  firefox http://192.168.50.10/records/1

See :ref:`install_prerequisites` for more information.
