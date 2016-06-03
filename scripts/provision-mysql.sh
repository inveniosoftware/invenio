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

# quit on unbound symbols:
set -o nounset

provision_mysql_ubuntu12 () {

    # update list of available packages
    sudo DEBIAN_FRONTEND=noninteractive apt-get update

    # install MySQL server:
    sudo DEBIAN_FRONTEND=noninteractive apt-get -y install \
         mysql-server

    # allow network connections:
    if ! grep -q "${INVENIO_MYSQL_HOST}" /etc/mysql/my.cnf; then
        sudo sed -i "s/127.0.0.1/${INVENIO_MYSQL_HOST}/" /etc/mysql/my.cnf
    fi

    # restart MySQL server:
    sudo /usr/sbin/service mysql restart

}

provision_mysql_ubuntu14 () {
    provision_mysql_ubuntu12
}

provision_mysql_centos6 () {

    # update list of available packages
    sudo yum update -y

    # install MySQL server:
    sudo yum install -y \
         mysql-server

    # open firewall ports:
    if [ -e /sbin/iptables ]; then
        thisinputchain="INPUT"
        if sudo /sbin/iptables -nL | grep -q 'Chain RH-Firewall-1-INPUT'; then
            thisinputchain="RH-Firewall-1-INPUT"
        fi
        if ! sudo /sbin/iptables -nL | grep -q dpt:3306; then
            sudo /sbin/iptables -I $thisinputchain -p tcp -m tcp --dport 3306 -j ACCEPT
            sudo /sbin/iptables -I OUTPUT -p tcp -m tcp --dport 3306 -j ACCEPT
        fi
        if ! sudo /sbin/iptables -nL | grep -q dpt:3306; then
            sudo /sbin/iptables -I $thisinputchain -p tcp -m tcp --dport 3306 -j ACCEPT
            sudo /sbin/iptables -I OUTPUT -p tcp -m tcp --dport 3306 -j ACCEPT
        fi
    fi

    # save new firewall rules to survive reboot:
    sudo /sbin/service iptables save

    # enable MySQL upon reboot:
    sudo /sbin/chkconfig mysqld on

    # restart MySQL server:
    sudo /sbin/service mysqld restart

}

setup_db () {

    # create database if it does not exist:
    echo "CREATE DATABASE IF NOT EXISTS ${INVENIO_MYSQL_DBNAME} DEFAULT CHARACTER SET utf8;" | \
        mysql -u root -B

    # grant privileges to the user on this database:
    echo "GRANT ALL PRIVILEGES ON ${INVENIO_MYSQL_DBNAME}.* TO ${INVENIO_MYSQL_DBUSER}@${INVENIO_WEB_HOST} IDENTIFIED BY '${INVENIO_MYSQL_DBPASS}';" | \
        mysql -u root -B
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
            provision_mysql_ubuntu12
        elif [ "$os_release" = "14" ]; then
            provision_mysql_ubuntu14
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "6" ]; then
            provision_mysql_centos6
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    else
        echo "[ERROR] Sorry, unsupported distribution ${os_distribution}."
        exit 1
    fi

    # finish with common setups:
    setup_db

}

main
