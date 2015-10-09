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

Quick installation guide
========================

If you would like to see what Invenio looks like, the quickest way is to use
Docker. For example, you can get Invenio v2.0 demo site up and running in
fifteen minutes by doing::

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
  w3m http://127.0.0.1:28080/
