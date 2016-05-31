#!/usr/bin/env bash
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

# quit on errors:
set -o errexit

# check environment variables:
if [ "${INVENIO_WEB_DSTDIR}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_DSTDIR before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_DSTDIR=/opt/invenio"
    exit 1
fi
if [ "${INVENIO_WEB_USER}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_USER before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_USER=www-data"
    exit 1
fi

# quit on unbound symbols:
set -o nounset

# install sources and restart WSGI application:
(make -s && sudo -u "${INVENIO_WEB_USER}" make -s install && \
        sudo -u "${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --update-all && \
        sudo -u "${INVENIO_WEB_USER}" touch "${INVENIO_WEB_DSTDIR}/var/www-wsgi/invenio.wsgi") > /dev/null
