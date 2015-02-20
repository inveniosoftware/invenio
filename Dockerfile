# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# Using CentOS-6 with Python-2.6 and MySQL-5.1, fitting our minimal
# requirements for Invenio v1.2:
FROM centos:6

# Installing OS prerequisites:
RUN yum update -y && \
    yum install -y epel-release && \
    yum install -y automake \
                   file \
                   freetype-devel \
                   gcc \
                   gcc-c++ \
                   gettext \
                   gettext-devel \
                   git \
                   hdf5-devel \
                   ipython \
                   libpng-devel \
                   libxslt-devel \
                   libreoffice \
                   libreoffice-headless \
                   libreoffice-pyuno \
                   mod_ssl \
                   mod_wsgi \
                   mysql-devel \
                   mysql-server \
                   poppler-utils \
                   python-devel \
                   python-magic \
                   python-pip \
                   redis \
                   sendmail \
                   sudo \
                   texlive \
                   unzip \
                   w3m \
                   wget && \
    yum clean all

# Installing Python prerequisites:
ADD requirements.txt /tmp/requirements.txt
ADD requirements-extras.txt /tmp/requirements-extras.txt
RUN pip install --upgrade distribute && \
    pip install supervisor && \
    pip install -r /tmp/requirements.txt && \
    pip install -r /tmp/requirements-extras.txt

# Run container as `apache` user, with forced UID of 1000, which
# should match current host user in most situations:
RUN usermod -u 1000 apache && \
    echo "apache ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Creating Python symlink:
RUN mkdir -p /opt/invenio/lib/python/invenio && \
    ln -s /opt/invenio/lib/python/invenio /usr/lib/python2.6/site-packages && \
    ln -s /opt/invenio/lib/python/invenio /usr/lib64/python2.6/site-packages && \
    chown -R apache.apache /opt/invenio && \
    mkdir /.texmf-var && \
    chown apache /.texmf-var

# Allowing sudo from non-tty connections:
RUN sed -i 's,Defaults    requiretty,#Defaults    requiretty,g' /etc/sudoers

# Creating DB:
RUN /sbin/service mysqld start && \
    mysqladmin -u root password '' && \
    echo "DROP DATABASE IF EXISTS invenio;" | mysql -u root -B && \
    echo "CREATE DATABASE invenio DEFAULT CHARACTER SET utf8;" | mysql -u root -B && \
    echo 'GRANT ALL PRIVILEGES ON invenio.* TO invenio@localhost IDENTIFIED BY "my123pass"' | mysql -u root -B

# Installing Supervisor:
RUN echo "[supervisord]" > /etc/supervisord.conf && \
    echo "nodaemon=true" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:sendmail]" >> /etc/supervisord.conf && \
    echo "command=/etc/init.d/sendmail start" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:redis-server]" >> /etc/supervisord.conf && \
    echo "command=/usr/sbin/redis-server /etc/redis.conf" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:mysqld]" >> /etc/supervisord.conf && \
    echo "command=/usr/bin/mysqld_safe" >> /etc/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisord.conf && \
    echo "user=root" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:httpd]" >> /etc/supervisord.conf && \
    echo "command=/usr/sbin/apachectl -D FOREGROUND" >> /etc/supervisord.conf

# Adding current directory as `/code`; assuming people have `master` branch checked out:
# (note: this invalidates cache, but most of hard yum install is done by now)
ADD . /code
WORKDIR /code
RUN chown -R apache /code

# Installing Invenio:
USER apache
RUN sudo /sbin/service mysqld restart && \
    sudo /sbin/service redis restart && \
    rm -rf autom4te.cache/ && \
    aclocal && \
    automake -a && \
    autoconf && \
    ./configure && \
    make -s clean && \
    make -s && \
    make -s install && \
    make -s install-jquery-plugins && \
    make -s install-mathjax-plugin && \
    make -s install-ckeditor-plugin && \
    make -s install-mediaelement && \
    make -s install-pdfa-helper-files && \
    mkdir -p /opt/invenio/var/tmp/ooffice-tmp-files && \
    sudo chgrp -R nobody /opt/invenio/var/tmp/ooffice-tmp-files && \
    sudo chmod -R 775 /opt/invenio/var/tmp/ooffice-tmp-files && \
    echo "[Invenio]" > /opt/invenio/etc/invenio-local.conf && \
    echo "CFG_SITE_URL = http://0.0.0.0" >> /opt/invenio/etc/invenio-local.conf && \
    echo "CFG_SITE_SECURE_URL = https://0.0.0.0" >> /opt/invenio/etc/invenio-local.conf && \
    echo "CFG_DATABASE_PASS = my123pass" >> /opt/invenio/etc/invenio-local.conf && \
    chown -R apache /opt/invenio && \
    /opt/invenio/bin/inveniocfg --update-all && \
    /opt/invenio/bin/inveniocfg --create-tables --yes-i-know && \
    /opt/invenio/bin/inveniocfg --load-bibfield-conf && \
    /opt/invenio/bin/inveniocfg --create-apache-conf --yes-i-know && \
    /opt/invenio/bin/inveniocfg --create-demo-site --yes-i-know && \
    /opt/invenio/bin/inveniocfg --load-demo-records --yes-i-know

# Configuring Apache:
USER root
RUN sed -i 's,^Alias /error,#Alias /error,g' /etc/httpd/conf/httpd.conf && \
    echo "Include /opt/invenio/etc/apache/invenio-apache-vhost.conf" >> /etc/httpd/conf/httpd.conf && \
    echo "Include /opt/invenio/etc/apache/invenio-apache-vhost-ssl.conf" >> /etc/httpd/conf/httpd.conf

# Starting the application:
EXPOSE 80 443
USER apache
CMD ["sudo", "-u", "root", "/usr/bin/supervisord"]
