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
if [ "${INVENIO_SRCDIR}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_SRCDIR before runnning this script."
    echo "[ERROR] Example: export INVENIO_SRCDIR=/vagrant"
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

# unattended installation:
export DEBIAN_FRONTEND=noninteractive

provision_web_ubuntu_precise () {

    # update list of available packages
    $sudo DEBIAN_FRONTEND=noninteractive apt-get update

    # install useful system packages
    $sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
          apache2-mpm-worker \
          automake \
          clisp \
          curl \
          cython \
          gettext \
          giflib-tools \
          git \
          gnuplot poppler-utils \
          html2text \
          ipython \
          libapache2-mod-wsgi \
          libapache2-mod-xsendfile \
          libffi-dev \
          libfreetype6-dev \
          libjpeg-dev \
          libmsgpack-dev \
          libmysqlclient-dev \
          libpng-dev \
          libssl-dev \
          libtiff-dev \
          libxml2-dev \
          libxslt-dev \
          make \
          mysql-client \
          netpbm \
          openOffice.org \
          pdftk \
          pep8 \
          postfix \
          pstotext \
          pylint \
          python-dev \
          python-gnuplot \
          python-libxml2 \
          python-libxslt1 \
          python-nose \
          python-nosexcover \
          python-pip \
          python-uno \
          redis-server \
          rlwrap \
          sbcl \
          screen \
          texlive \
          unzip \
          vim

    # grant Apache user the nobody user rights for OpenOffice integration:
    echo "www-data  ALL=(nobody) NOPASSWD: ALL" | $sudo tee /etc/sudoers.d/www-data
    $sudo chmod o-r /etc/sudoers.d/www-data

}

provision_web_centos6 () {

    # update list of available packages
    $sudo yum update -y

    # add EPEL external repository:
    $sudo yum install -y epel-release

    # install useful system tools:
    $sudo yum install -y \
         automake \
         curl \
         cython \
         file \
         freetype-devel \
         gcc \
         gcc-c++ \
         gettext \
         gettext-devel \
         git \
         gnuplot-py \
         hdf5-devel \
         ipython \
         libffi-devel \
         libpng-devel \
         libreoffice \
         libreoffice-headless \
         libreoffice-pyuno \
         libxml2-devel \
         libxml2-python \
         libxslt-devel \
         libxslt-python \
         mod_ssl \
         mod_wsgi \
         mysql-devel \
         poppler-utils \
         python-devel \
         python-pip \
         redis \
         rlwrap \
         screen \
         sendmail \
         sudo \
         texlive \
         unzip \
         vim \
         w3m \
         wget

    # open firewall ports:
    if [ -e /sbin/iptables ]; then
        thisinputchain="INPUT"
        if sudo /sbin/iptables -nL | grep -q 'Chain RH-Firewall-1-INPUT'; then
            thisinputchain="RH-Firewall-1-INPUT"
        fi
        if ! sudo /sbin/iptables -nL | grep -q dpt:http; then
            sudo /sbin/iptables -I $thisinputchain -p tcp -m tcp --dport 80 -j ACCEPT
            sudo /sbin/iptables -I OUTPUT -p tcp -m tcp --dport 80 -j ACCEPT
        fi
        if ! sudo /sbin/iptables -nL | grep -q dpt:https; then
            sudo /sbin/iptables -I $thisinputchain -p tcp -m tcp --dport 443 -j ACCEPT
            sudo /sbin/iptables -I OUTPUT -p tcp -m tcp --dport 443 -j ACCEPT
        fi
    fi

    # save new firewall rules to survive reboot:
    sudo /etc/init.d/iptables save

    # enable Apache upon reboot:
    sudo /sbin/chkconfig httpd on

    # start Redis:
    sudo /etc/init.d/redis start

    # enable Redis upon reboot:
    sudo /sbin/chkconfig redis on

    # grant Apache user the nobody user rights for OpenOffice integration:
    echo "apache  ALL=(nobody) NOPASSWD: ALL" | $sudo tee /etc/sudoers.d/apache
    $sudo chmod o-r /etc/sudoers.d/apache

}

provision_web_pypi () {

    # install Python packages from PyPI
    olddir=$(pwd)
    cd "${INVENIO_SRCDIR}"
    for reqfile in requirements*.txt; do
        if [ -e "$reqfile" ]; then
            if [ "$VIRTUAL_ENV" != "" ]; then
                pip install -r "$reqfile"
            else
                sudo pip install -r "$reqfile"
            fi
        fi
    done
    cd "${olddir}"

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
            provision_web_ubuntu_precise
            provision_web_pypi
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "6" ]; then
            provision_web_centos6
            provision_web_pypi
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
