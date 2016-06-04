# -*- coding: utf-8 -*-
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

# This Vagrant configuration is suitable for Invenio demo site installation as
# governed by `.inveniorc`. It uses separate dedicated VMs for various services
# in order to better emulate production environment conditions. You can install
# an Invenio demo site by running:
#
# $ vagrant up --no-parallel
# $ vagrant ssh web -c 'source .inveniorc && /vagrant/scripts/create-instance.sh'
# $ vagrant ssh web -c 'source .inveniorc && /vagrant/scripts/populate-instance.sh'
# $ firefox http://192.168.50.10/record/1
# $ vagrant ssh web -c 'source .inveniorc && sudo -u www-data /opt/invenio/bin/inveniocfg --run-unit-tests'
# $ vagrant ssh web -c 'source .inveniorc && sudo -u www-data /opt/invenio/bin/inveniocfg --run-regression-tests --yes-i-know'

# Tested on:
#
# OS = 'hfm4/centos6' # CentOS 6
# OS = 'ubuntu/precise64' # Ubuntu 12.04 LTS Precise Pangolin -- used by Travis CI
OS = 'ubuntu/trusty64' # Ubuntu 14.04 LTS Trusty Tahr

Vagrant.configure("2") do |config|

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  config.vm.define "web" do |web|
    web.vm.box = OS
    web.vm.hostname = 'web'
    web.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    web.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-web.sh", privileged: false
    web.vm.network "forwarded_port", guest: 80, host: 80
    web.vm.network "forwarded_port", guest: 443, host: 443
    web.vm.network "private_network", ip: ENV.fetch('INVENIO_WEB_HOST','192.168.50.10')
    web.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--memory", "4096"]
      vb.customize ["modifyvm", :id, "--cpus", 2]
    end
  end

  config.vm.define "mysql" do |mysql|
    mysql.vm.box = OS
    mysql.vm.hostname = 'mysql'
    mysql.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    mysql.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-mysql.sh", privileged: false
    mysql.vm.network "private_network", ip: ENV.fetch('INVENIO_MYSQL_HOST','192.168.50.11')
  end

end
