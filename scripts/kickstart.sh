#!/usr/bin/env bash
#
# >>> About
#
# This helper script installs Invenio 3.0 development environment on a fresh
# (virtual) machine in a fully automated, unassisted way. It is used to test
# Invenio 3.0 installation instructions presented in the documentation:
# http://pythonhosted.org/invenio/installation/installation-detailed.html
#
# Tested on the following operating systems:
# - Ubuntu 14.04 LTS (Trusty Tahr) amd64
# - CentOS 7
#
# >>> Copyright
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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
#
# >>> Usage
#
# First, start a new VM like this:
#
#   laptop> mkdir -p ~/private/vm/invenio3trusty64
#   laptop> cd ~/private/vm/invenio3trusty64
#   laptop> vim Vagrantfile # enter following content:
#   Vagrant.configure("2") do |config|
#     config.vm.box = "trusty64"
#     config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"
#     config.vm.network :forwarded_port, host: 5000, guest: 5000
#     config.vm.provider :virtualbox do |vb|
#       vb.customize ["modifyvm", :id, "--memory", "2048"]
#       vb.customize ["modifyvm", :id, "--cpus", 2]
#     end
#   end
#   laptop> vagrant up
#
# Second, connect to VM and launch kickstarter:
#
#   laptop> vagrant ssh
#   vm> wget https://raw.githubusercontent.com/inveniosoftware/invenio/master/scripts/kickstart.sh
#   vm> chmod u+x ./invenio2-kickstart.sh
#   vm> ./kickstart.sh --yes-i-know --yes-i-really-know
#
# Third, go brew some tea, come back in ten minutes, enjoy!
#
#   laptop> firefox http://0.0.0.0:5000/
#
# Howgh!

# sanity check: CLI confirmation
if [[ "$@" != *"--yes-i-know"* ]]; then
    echo "[ERROR] You did not use --yes-i-know.  Not going to kickstart Invenio on this machine."
    exit 1
fi
if [[ "$@" != *"--yes-i-really-know"* ]]; then
    echo "[ERROR] You did not use --yes-i-really-know.  Not going to kickstart Invenio on this machine."
    exit 1
fi

# quit on errors and potentially unbound symbols:
#  (commented because of virtualenvwrapper)
#set -o errexit
#set -o nounset

configure_iptables () {

    # FIXME The instructions below are taken from Invenio 2. This will be needed
    # later for Invenio 3 as well when the site will be running on HTTP or HTTPS
    # ports. For the time being, the site is running on port 5000, so let's
    # simply exit for now.
    exit

    # open HTTP and HTTPS ports in the firewall:
    if [ -e /sbin/iptables ]; then
        thisinputchain="INPUT"
        if sudo /sbin/iptables -nL | grep -q 'Chain RH-Firewall-1-INPUT'; then
            thisinputchain="RH-Firewall-1-INPUT"
        fi
        httpport=$(echo ${CFG_INVENIO2_SITE_URL} | cut -d: -f 3)
        httpsport=$(echo ${CFG_INVENIO2_SITE_SECURE_URL} | cut -d: -f 3)
        if [ -n $httpport ]; then
            if ! sudo /sbin/iptables -nL | grep -q dpt:$httpport; then
                sudo /sbin/iptables -I $thisinputchain -p tcp -m tcp --dport $httpport -j ACCEPT
                sudo /sbin/iptables -I OUTPUT -p tcp -m tcp --dport $httpport -j ACCEPT
            fi
        fi
        if [ -n $httpsport ]; then
            if ! sudo /sbin/iptables -nL | grep -q dpt:$httpsport; then
                sudo /sbin/iptables -I $thisinputchain -p tcp -m tcp --dport $httpsport -j ACCEPT
                sudo /sbin/iptables -I OUTPUT -p tcp -m tcp --dport $httpsport -j ACCEPT
            fi
        fi
    fi
}

setup_ubuntu_trusty () {

    # sphinxdoc-install-useful-system-tools-begin
    sudo DEBIAN_FRONTEND=noninteractive apt-get -y install \
         curl \
         git \
         rlwrap \
         screen \
         vim \
         wget
    # sphinxdoc-install-useful-system-tools-end

    # sphinxdoc-add-elasticsearch-external-repository-begin
    if [[ ! -f /etc/apt/sources.list.d/elasticsearch-2.x.list ]]; then
        wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
        echo "deb http://packages.elastic.co/elasticsearch/2.x/debian stable main" | \
            sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
    fi
    # sphinxdoc-add-elasticsearch-external-repository-end

    # sphinxdoc-add-nodejs-external-repository-begin
    if [[ ! -f /etc/apt/sources.list.d/nodesource.list ]]; then
        curl -sL https://deb.nodesource.com/setup_4.x | sudo bash -
    fi
    # sphinxdoc-add-nodejs-external-repository-end

    # sphinxdoc-install-prerequisites-begin
    sudo DEBIAN_FRONTEND=noninteractive apt-get -y install \
         build-essential \
         elasticsearch \
         ipython \
         libffi-dev \
         libfreetype6-dev \
         libjpeg-dev \
         libmsgpack-dev \
         libssl-dev \
         libtiff-dev \
         libxml2-dev \
         libxslt-dev \
         nodejs \
         postgresql \
         python-dev \
         python-pip \
         rabbitmq-server \
         redis-server \
         software-properties-common
    # sphinxdoc-install-prerequisites-end

    # sphinxdoc-install-bower-and-css-js-filters-begin
    sudo su -c "npm install -g bower"
    sudo su -c "npm install -g less clean-css requirejs uglify-js"
    # sphinxdoc-install-bower-and-css-js-filters-end

    # sphinxdoc-install-virtualenvwrapper-begin
    sudo pip install -U virtualenvwrapper pip
    if ! grep -q virtualenvwrapper ~/.bashrc; then
        mkdir -p $HOME/.virtualenvs
        echo "export WORKON_HOME=$HOME/.virtualenvs" >> $HOME/.bashrc
        echo "source $(which virtualenvwrapper.sh)" >> $HOME/.bashrc
    fi
    export WORKON_HOME=$HOME/.virtualenvs
    source $(which virtualenvwrapper.sh)
    # sphinxdoc-install-virtualenvwrapper-end
}

setup_centos7 () {

    # add EPEL external repository:
    sudo yum install -y epel-release

    # add Elasticsearch external repository:
    if [[ ! -f /etc/yum.repos.d/elasticsearch.repo ]]; then
        sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
        echo "[elasticsearch-2.x]
name=Elasticsearch repository for 2.x packages
baseurl=http://packages.elastic.co/elasticsearch/2.x/centos
gpgcheck=1
gpgkey=http://packages.elastic.co/GPG-KEY-elasticsearch
enabled=1" | \
            sudo tee -a /etc/yum.repos.d/elasticsearch.repo
    fi

    # install pre-requisite software:
    sudo yum update -y
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y \
         elasticsearch \
         git \
         libffi-devel \
         libxml2-devel \
         libxslt-devel \
         npm \
         openssl-devel \
         postgresql \
         python-devel \
         python-pip \
         rabbitmq-server \
         redis \
         wget

    # start Elasticsearch:
    sudo chkconfig --add elasticsearch
    sudo /etc/init.d/elasticsearch start

    # start Redis:
    sudo systemctl start redis

    # install Bower globally:
    sudo su -c "npm install -g bower"

    # install CSS/JS asset filters globally:
    sudo su -c "npm install -g less clean-css requirejs uglify-js"

    # install Python virtual environments
    sudo pip install -U virtualenvwrapper pip
    if ! grep -q virtualenvwrapper ~/.bashrc; then
        mkdir -p $HOME/.virtualenvs
        echo "export WORKON_HOME=$HOME/.virtualenvs" >> $HOME/.bashrc
        echo "source $(which virtualenvwrapper.sh)" >> $HOME/.bashrc
    fi
    export WORKON_HOME=$HOME/.virtualenvs
    source $(which virtualenvwrapper.sh)
}

install_invenio () {

    # sphinxdoc-create-virtual-environment-begin
    mkvirtualenv invenio3
    cdvirtualenv
    # sphinxdoc-create-virtual-environment-end

    # sphinxdoc-install-invenio-full-begin
    mkdir -p src && cd src
    pip install invenio[full] --pre
    # sphinxdoc-install-invenio-full-end

    # sphinxdoc-create-instance-begin
    inveniomanage instance create mysite
    # sphinxdoc-create-instance-end

    # sphinxdoc-run-bower-begin
    cd mysite
    pip install ipaddr # FIXME this seems explicitly needed on Python-2.7
    python manage.py bower
    cdvirtualenv var/mysite-instance/
    CI=true bower install
    cd -
    # sphinxdoc-run-bower-end

    # sphinxdoc-collect-and-build-assets-begin
    python manage.py collect -v
    python manage.py assets build
    # sphinxdoc-collect-and-build-assets-end

    # sphinxdoc-create-database-begin
    python manage.py db init
    python manage.py db create
    # sphinxdoc-create-database-end

    # sphinxdoc-create-user-account-begin
    python manage.py users create \
           --email info@inveniosoftware.org --password mypass123 \
           --active
    # sphinxdoc-create-user-account-end

    # sphinxdoc-start-celery-worker-begin
    # temporary step (ensures celery tasks are discovered)
    echo "from invenio_records.tasks import *" >> mysite/celery.py
    # run celery worker (in a new window)
    celery worker -A mysite.celery -l INFO &
    # sphinxdoc-start-celery-worker-end

    # sphinxdoc-populate-with-demo-records-begin
    echo '{"title":"Invenio 3 Rocks", "recid": 1}'| \
        python manage.py records create
    # sphinxdoc-populate-with-demo-records-end

    # sphinxdoc-register-pid-begin
    echo "from invenio_db import db; \
    from invenio_pidstore.models import PersistentIdentifier; \
    pid = PersistentIdentifier.create('recid', '1', 'recid'); \
    pid.assign('rec', '1'); \
    pid.register(); \
    db.session.commit()" | python manage.py shell
    # sphinxdoc-register-pid-end

    # sphinxdoc-start-application-begin
    python manage.py --debug run &
    # sphinxdoc-start-application-end
}

main () {

    # detect OS and call appropriate setup functions:
    if hash lsb_release 2> /dev/null; then
        os_distribution=$(lsb_release -i | cut -f 2)
        os_release=$(lsb_release -r | cut -f 2)
    elif [ -e /etc/redhat-release ]; then
        os_distribution=$(cat /etc/redhat-release | cut -d ' ' -f 1)
        os_release=$(cat /etc/redhat-release | grep -oE '[0-9]+\.' | cut -d. -f1 | head -1)
    else
        os_distribution="UNDETECTED"
        os_release="UNDETECTED"
    fi
    if [ "$os_distribution" = "Ubuntu" ]; then
        if [ "$os_release" = "14.04" ]; then
            setup_ubuntu_trusty
            install_invenio
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            echo "[ERROR] Please contact authors.  Exiting."
        fi
    elif [ "$os_distribution" = "CentOS" ]; then
        if [ "$os_release" = "7" ]; then
            setup_centos7
            install_invenio
        else
            echo "[ERROR] Sorry, unsupported release ${os_release}."
            echo "[ERROR] Please contact authors.  Exiting."
        fi
    else
        echo "[ERROR] Sorry, unsupported distribution ${os_distribution}."
        echo "[ERROR] Please contact authors.  Exiting."
        exit 1;
    fi
}

main

# end of file
