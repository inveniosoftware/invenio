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

# runs inside virtual environment?
VIRTUAL_ENV=${VIRTUAL_ENV:=}

# runs as root or needs sudo?
if [[ "$EUID" -ne 0 ]]; then
    sudo='sudo'
else
    sudo=''
fi

create_demo_site () {
   $sudo -u "${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --create-demo-site --yes-i-know
}

load_demo_records () {
    $sudo -u "${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --load-demo-records --yes-i-know
}

apache_wsgi_restart () {
    $sudo -u "${INVENIO_WEB_USER}" touch "${INVENIO_WEB_DSTDIR}/var/www-wsgi/invenio.wsgi"
}

start_apache_ubuntu12 () {
    $sudo /usr/sbin/service apache2 start
}

stop_apache_ubuntu12 () {
    $sudo /usr/sbin/service apache2 stop
}

start_apache_ubuntu14 () {
    start_apache_ubuntu12
}

stop_apache_ubuntu14 () {
    stop_apache_ubuntu12
}

start_apache_centos6 () {
    $sudo /sbin/service httpd start
}

stop_apache_centos6 () {
    $sudo /sbin/service httpd stop
}

main () {

    # detect OS distribution and release version:
    if hash lsb_release 2> /dev/null; then
        os_distribution=$(lsb_release -i | cut -f 2)
        os_release=$(lsb_release -r | cut -f 2 | grep -oE '[0-9]+\.' | cut -d. -f1 | head -1)
    elif [ -e /etc/redhat-release ]; then
        os_distribution=$(cut -d ' ' -f 1 /etc/redhat-release)
        os_release=$(grep -oE '[0-9]+\.' /etc/redhat-release | cut -d. -f1 | head -1)
    else
        os_distribution="UNDETECTED"
        os_release="UNDETECTED"
    fi

    # call appropriate provisioning functions:
    if [ "$os_distribution" = "Ubuntu" ]; then
        if [ "$os_release" = "12" ]; then
            stop_apache_ubuntu12
            create_demo_site
            start_apache_ubuntu12
            load_demo_records
            apache_wsgi_restart
        elif [ "$os_release" = "14" ]; then
            stop_apache_ubuntu14
            create_demo_site
            start_apache_ubuntu14
            load_demo_records
            apache_wsgi_restart
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "6" ]; then
            stop_apache_centos6
            create_demo_site
            start_apache_centos6
            load_demo_records
            apache_wsgi_restart
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    else
        echo "[ERROR] Sorry, unsupported distribution ${os_distribution}."
        exit 1
    fi

}

main
