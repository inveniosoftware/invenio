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

# check optional environment variables:
INVENIO_WEB_SMTP_PORT=${INVENIO_WEB_SMTP_PORT:=25}

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

create_apache_vhost_ubuntu_precise () {
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y ssl-cert
    sudo mkdir -p /etc/apache2/ssl
    if [ ! -e /etc/apache2/ssl/apache.pem ]; then
        sudo DEBIAN_FRONTEND=noninteractive /usr/sbin/make-ssl-cert \
            /usr/share/ssl-cert/ssleay.cnf /etc/apache2/ssl/apache.pem
    fi
    if [ ! -L /etc/apache2/sites-available/invenio.conf ]; then
        sudo ln -fs "${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf" \
            /etc/apache2/sites-available/invenio.conf
    fi
    if [ ! -e "${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf" ]; then
        # create them empty for the time being so that apache would start
        sudo mkdir -p "${INVENIO_WEB_DSTDIR}/etc/apache/"
        sudo touch "${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf"
        sudo chown -R "${INVENIO_WEB_USER}.${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}"
    fi
    if [ ! -L /etc/apache2/sites-available/invenio-ssl.conf ]; then
        sudo ln -fs "${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf" \
            /etc/apache2/sites-available/invenio-ssl.conf
    fi
    if [ ! -e "${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf" ]; then
        # create them empty for the time being so that apache would start
        sudo mkdir -p "${INVENIO_WEB_DSTDIR}/etc/apache/"
        sudo touch "${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf"
        sudo chown -R "${INVENIO_WEB_USER}.${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}"
    fi
    if [ -e /etc/apache2/sites-available/default-ssl ]; then
        sudo /usr/sbin/a2dissite "*default*"
    fi
    sudo /usr/sbin/a2ensite "invenio*"
    sudo /usr/sbin/a2enmod ssl
    sudo /usr/sbin/a2enmod version || echo "[WARNING] Ignoring 'a2enmod version' command; hoping IfVersion is built-in."
    sudo /usr/sbin/a2enmod xsendfile
    sudo /etc/init.d/apache2 restart
}

create_apache_vhost_centos6 () {
    if ! grep -q "Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf" /etc/httpd/conf/httpd.conf; then
        echo "Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost.conf" | sudo tee -a /etc/httpd/conf/httpd.conf
    fi
    if ! grep -q "Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf" /etc/httpd/conf/httpd.conf; then
        echo "Include ${INVENIO_WEB_DSTDIR}/etc/apache/invenio-apache-vhost-ssl.conf" | sudo tee -a /etc/httpd/conf/httpd.conf
    fi
    if ! grep -q "TraceEnable off" /etc/httpd/conf/httpd.conf; then
        echo "TraceEnable off" | sudo tee -a /etc/httpd/conf/httpd.conf
    fi
    if ! grep -q "SSLProtocol all -SSLv2" /etc/httpd/conf/httpd.conf; then
        echo "SSLProtocol all -SSLv2" | sudo tee -a /etc/httpd/conf/httpd.conf
    fi
    sudo sed -i 's,^Alias /error/,#Alias /error/,g' /etc/httpd/conf/httpd.conf
}

create_symlinks () {
    $sudo mkdir -p "${INVENIO_WEB_DSTDIR}"
    $sudo chown "${INVENIO_WEB_USER}.${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}"
    $sudo -u "${INVENIO_WEB_USER}" mkdir -p "${INVENIO_WEB_DSTDIR}/lib/python/invenio"
    for pythonversion in python2.4 python2.6 python2.7; do
        for libversion in lib lib64 local/lib local/lib64; do
            for packageversion in site-packages dist-packages; do
                if [ -d "/usr/$libversion/$pythonversion/$packageversion/" ] && [ ! -L "/usr/$libversion/$pythonversion/$packageversion/invenio" ]; then
                    $sudo ln -s "${INVENIO_WEB_DSTDIR}/lib/python/invenio" "/usr/$libversion/$pythonversion/$packageversion/invenio"
                fi
            done
        done
    done
}

install_sources () {
    cd "${INVENIO_SRCDIR}"
    rm -rf autom4te.cache/
    aclocal
    automake -a
    autoconf
    ./configure --prefix="${INVENIO_WEB_DSTDIR}"
    make clean -s
    make -s
    sudo -u "${INVENIO_WEB_USER}" make -s install
    #sudo -u "${INVENIO_WEB_USER}" make -s install-jquery-plugins
    sudo -u "${INVENIO_WEB_USER}" make -s install-mathjax-plugin
    sudo -u "${INVENIO_WEB_USER}" make -s install-ckeditor-plugin
    sudo -u "${INVENIO_WEB_USER}" make -s install-pdfa-helper-files
    sudo -u "${INVENIO_WEB_USER}" make -s install-mediaelement
}

create_openoffice_tmp_space () {
    sudo mkdir -p "${INVENIO_WEB_DSTDIR}/var/tmp/ooffice-tmp-files"
    sudo chown -R nobody "${INVENIO_WEB_DSTDIR}/var/tmp/ooffice-tmp-files"
    sudo chmod -R 755 "${INVENIO_WEB_DSTDIR}/var/tmp/ooffice-tmp-files"
}

configure_instance () {
    # create invenio-local.conf
    echo "[Invenio]
CFG_SITE_URL = http://${INVENIO_WEB_HOST}
CFG_SITE_SECURE_URL = https://${INVENIO_WEB_HOST}
CFG_DATABASE_HOST = ${INVENIO_MYSQL_HOST}
CFG_DATABASE_NAME = ${INVENIO_MYSQL_DBNAME}
CFG_DATABASE_USER = ${INVENIO_MYSQL_DBUSER}
CFG_DATABASE_PASS = ${INVENIO_MYSQL_DBPASS}
CFG_SITE_ADMIN_EMAIL = ${INVENIO_ADMIN_EMAIL}
CFG_SITE_SUPPORT_EMAIL = ${INVENIO_ADMIN_EMAIL}
CFG_WEBALERT_ALERT_ENGINE_EMAIL = ${INVENIO_ADMIN_EMAIL}
CFG_WEBCOMMENT_ALERT_ENGINE_EMAIL = ${INVENIO_ADMIN_EMAIL}
CFG_WEBCOMMENT_DEFAULT_MODERATOR = ${INVENIO_ADMIN_EMAIL}
CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL = ${INVENIO_ADMIN_EMAIL}
CFG_BIBCATALOG_SYSTEM_EMAIL_ADDRESS = ${INVENIO_ADMIN_EMAIL}
CFG_BIBSCHED_PROCESS_USER = ${INVENIO_WEB_USER}
CFG_MISCUTIL_SMTP_PORT = ${INVENIO_WEB_SMTP_PORT}
" | \
        sudo -u "${INVENIO_WEB_USER}" tee "${INVENIO_WEB_DSTDIR}/etc/invenio-local.conf"

    # update instance with this information:
    sudo -u "${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --update-all
}

create_tables () {
    sudo -u "${INVENIO_WEB_USER}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --create-tables --yes-i-know
}

create_apache_configuration () {
    sudo -u "${INVENIO_WEB_USER}" VIRTUAL_ENV="${VIRTUAL_ENV}" "${INVENIO_WEB_DSTDIR}/bin/inveniocfg" --create-apache-conf
}

restart_apache_ubuntu_precise () {
    $sudo /etc/init.d/apache2 restart
}

restart_apache_centos6 () {
    $sudo /etc/init.d/httpd restart
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
            create_apache_vhost_ubuntu_precise
            create_symlinks
            install_sources
            create_openoffice_tmp_space
            configure_instance
            create_tables
            create_apache_configuration
            restart_apache_ubuntu_precise
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "6" ]; then
            create_apache_vhost_centos6
            create_symlinks
            install_sources
            create_openoffice_tmp_space
            configure_instance
            create_tables
            create_apache_configuration
            restart_apache_centos6
            exit 1
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
