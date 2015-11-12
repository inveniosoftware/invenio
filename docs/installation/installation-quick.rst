..  This file is part of Invenio
    Copyright (C) 2014, 2015 CERN.

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

Quick installation guide
========================

Using Docker
------------

You can get Invenio v2.0 demo site up and running in fifteen minutes using
Docker::

  mkdir -p ~/private/src
  cd ~/private/src
  git clone git@github.com/inveniosoftware/invenio
  git clone git@github.com/inveniosoftware/invenio-demosite
  cd ~/private/src/invenio
  git checkout maint-2.0
  docker build -t invenio:2.0 .
  cd ~/private/src/invenio-demosite
  git checkout maint-2.0
  docker-compose -f docker-compose-dev.yml build
  docker-compose -f docker-compose-dev.yml up
  # now wait until all daemons are fully up and running
  docker exec -i -t -u invenio inveniodemosite_web_1 \
      inveniomanage demosite populate \
      --packages=invenio_demosite.base --yes-i-know
  firefox http://127.0.0.1:28080/

Using Vagrant
-------------

You can get Invenio v3.0 demo site up and running using Vagrant::

  vagrant up
  vagrant ssh web -c 'source .inveniorc && /vagrant/scripts/install.sh'
  vagrant ssh web -c 'curl http://0.0.0.0:5000/records/1'

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
  scripts/install.sh
  firefox http://127.0.0.1:5000/

See :ref:`installation_detailed` for more information.
