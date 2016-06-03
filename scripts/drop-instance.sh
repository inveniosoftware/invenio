#!/usr/bin/env bash
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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
if [ "${INVENIO_MYSQL_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_MYSQL_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_MYSQL_HOST=192.168.50.11"
    exit 1
fi
if [ "${INVENIO_MYSQL_DBNAME}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_MYSQL_DBNAME before runnning this script."
    echo "[ERROR] Example: INVENIO_MYSQL_DBNAME=invenio1"
    exit 1
fi
if [ "${INVENIO_MYSQL_DBUSER}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_MYSQL_DBUSER before runnning this script."
    echo "[ERROR] Example: INVENIO_MYSQL_DBUSER=invenio1"
    exit 1
fi
if [ "${INVENIO_MYSQL_DBPASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_MYSQL_DBPASS before runnning this script."
    echo "[ERROR] Example: INVENIO_MYSQL_DBPASS=dbpass123"
    exit 1
fi
if [ "${INVENIO_WEB_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_HOST=192.168.50.10"
    exit 1
fi
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

# runs as root or needs sudo?
if [[ "$EUID" -ne 0 ]]; then
    sudo='sudo'
else
    sudo=''
fi


start_apache_ubuntu_precise () {
    $sudo /usr/sbin/service apache2 start
}

stop_apache_ubuntu_precise () {
    $sudo /usr/sbin/service apache2 stop
}

start_apache_centos6 () {
    $sudo /sbin/service httpd start
}

stop_apache_centos6 () {
    $sudo /sbin/service httpd stop
}

drop_apache_vhost_ubuntu_precise () {
    stop_apache_ubuntu_precise
    if [ -e /etc/apache2/sites-available/default-ssl ]; then
        $sudo /usr/sbin/a2ensite "*default*"
    fi
    if [ -L /etc/apache2/sites-enabled/invenio.conf ]; then
        $sudo /usr/sbin/a2dissite "invenio*"
    fi
    start_apache_ubuntu_precise
}

drop_apache_vhost_centos6 () {
    stop_apache_centos6
    if grep -q "Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf" /etc/httpd/conf/httpd.conf; then
        sudo sed -i "s,^Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf,#Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf,g" /etc/httpd/conf/httpd.conf
    fi
    if grep -q "Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf" /etc/httpd/conf/httpd.conf; then
        sudo sed -i "s,^Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf,#Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf,g" /etc/httpd/conf/httpd.conf
    fi
    sudo sed -i 's,^#Alias /error/,Alias /error/,g' /etc/httpd/conf/httpd.conf
    start_apache_centos6
}

drop_symlinks () {
    for pythonversion in python2.4 python2.6 python2.7; do
        for libversion in lib lib64 local/lib local/lib64; do
            for packageversion in site-packages dist-packages; do
                if [ -d /usr/$libversion/$pythonversion/$packageversion/ ] && [ ! -L /usr/$libversion/$pythonversion/$packageversion/invenio ]; then
                    $sudo rm /usr/$libversion/$pythonversion/$packageversion/invenio
                fi
            done
        done
    done
}

drop_instance_folder () {
    $sudo rm -rf "${INVENIO_WEB_DSTDIR}/var/tmp/ooffice-tmp-files"
    # shellcheck disable=SC2086
    $sudo -u "${INVENIO_WEB_USER}" rm -rf ${INVENIO_WEB_DSTDIR}/*
}

drop_instance_tables () {
    if [ -e "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" ]; then
        $sudo -u "${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --drop-tables --yes-i-know
    fi
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
            stop_apache_ubuntu_precise
            drop_instance_tables
            start_apache_ubuntu_precise
            drop_apache_vhost_ubuntu_precise
            drop_instance_folder
            drop_symlinks
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "6" ]; then
            stop_apache_centos6
            drop_instance_tables
            start_apache_centos6
            drop_apache_vhost_centos6
            drop_instance_folder
            drop_symlinks
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
