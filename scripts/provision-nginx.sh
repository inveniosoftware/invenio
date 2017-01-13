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

# quit on unbound symbols:
set -o nounset

# detect pathname of this script:
scriptpathname=$(cd "$(dirname "$0")" && pwd)

# sphinxdoc-install-detect-sudo-begin
# runs as root or needs sudo?
if [[ "$EUID" -ne 0 ]]; then
    sudo='sudo'
else
    sudo=''
fi
# sphinxdoc-install-detect-sudo-end

# unattended installation:
export DEBIAN_FRONTEND=noninteractive

setup_ssl_configuration () {
    # sphinxdoc-install-web-nginx-create-certificates-begin

    # create ssl files for HTTPS support
    if ! [ -f /etc/ssl/private/nginx.key ] || ! [ -f /etc/ssl/certs/nginx.crt ]; then
        $sudo openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
              -keyout /etc/ssl/private/nginx.key \
              -out /etc/ssl/certs/nginx.crt -batch
    fi
    # sphinxdoc-install-web-nginx-create-certificates-end
}

setup_nginx_ubuntu () {
    # sphinxdoc-install-web-nginx-ubuntu14-begin

    # install Nginx web server:
    $sudo apt-get install -y nginx

    # configure Nginx web server:
    setup_ssl_configuration
    $sudo cp -f "$scriptpathname/../nginx/nginx.conf" /etc/nginx/
    $sudo cp -rf "$scriptpathname/../nginx/conf.d" /etc/nginx/
    $sudo sed -i "s,/home/invenio/,/home/$(whoami)/,g" /etc/nginx/conf.d/default.conf
    $sudo /usr/sbin/service nginx restart

    # sphinxdoc-install-web-nginx-ubuntu14-end
}

setup_nginx_centos7 () {
    # sphinxdoc-install-web-nginx-centos7-begin
    # install Nginx web server:
    $sudo yum install -y nginx

    # configure Nginx web server:
    setup_ssl_configuration
    $sudo cp -f "$scriptpathname/../nginx/nginx.conf" /etc/nginx/
    $sudo cp -rf "$scriptpathname/../nginx/conf.d" /etc/nginx/
    $sudo sed -i "s,/home/invenio/,/home/$(whoami)/,g" /etc/nginx/conf.d/default.conf
    $sudo sed -i 's,80,8888,g' /etc/nginx/conf.d/default.conf
    $sudo chmod go+rx "/home/$(whoami)/"
    $sudo /sbin/service nginx restart

    # open firewall:
    $sudo firewall-cmd --permanent --zone=public --add-service=http
    $sudo firewall-cmd --permanent --zone=public --add-service=https
    $sudo firewall-cmd --reload
    # sphinxdoc-install-web-nginx-centos7-end
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
    if [ -f /.dockerinit ] || [ -f /.dockerenv ]; then
        # running inside Docker
        setup_ssl_configuration
    elif [ "$os_distribution" = "Ubuntu" ]; then
        if [ "$os_release" = "14" -o "$os_release" = "16" ]; then
            setup_nginx_ubuntu
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            exit 1
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "7" ]; then
            setup_nginx_centos7
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
