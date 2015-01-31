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

# Using CentOS-5 with Python-2.4 and MySQL-5.0, fitting our minimal
# requirements for Invenio v1.0:
FROM centos:5

# Installing OS prerequisites:
RUN yum update -y && \
    yum install -y epel-release && \
    yum install -y MySQL-python PyXML alsa-lib apr apr-devel apr-util \
        apr-util-devel cyrus-sasl-devel db4-devel distcache epydoc \
        expat-devel freetype-devel gettext-devel gpm httpd libXtst \
        libart_lgpl libgcj libgcrypt-devel libgpg-error-devel \
        libxslt libxslt-devel libxslt-python lynx mod_ssl \
        mod_wsgi mx mysql mysql-devel mysql-server numpy openldap-devel \
        perl-DBD-MySQL postgresql-libs python-devel python-setuptools \
        python-wsgiref screen vim-enhanced w3m git pylint ipython \
        python-dateutil python-simplejson python-reportlab pyPdf \
        python-mechanize python-hashlib python-feedparser \
        openoffice.org-calc openoffice.org-impress \
        openoffice.org-graphicfilter openoffice.org-javafilter \
        openoffice.org-math openoffice.org-writer openoffice.org-draw \
        openoffice.org-pyuno openoffice.org-ure openoffice.org-core \
        openoffice.org-base openoffice.org-headless \
        openoffice.org-xsltfilter automake make wget sudo supervisor \
        exim tetex-latex gnuplot poppler-utils python-lxml && \
    yum clean all && \
    rpm -Uvh http://simko.home.cern.ch/simko/rpm/pdftk-1.41-1.el5.rf.x86_64.rpm \
        http://simko.home.cern.ch/simko/rpm/pyRXP-1.13-1.20090612.slc5.x86_64.rpm \
        http://simko.home.cern.ch/simko/rpm/gnuplot-py-1.8-1.slc5.noarch.rpm \
        http://simko.home.cern.ch/simko/rpm/PyStemmer-1.0.1-1.slc5.x86_64.rpm \
        http://simko.home.cern.ch/simko/rpm/rdflib-2.4.1-1.slc5.x86_64.rpm

# Run container as `apache` user, with forced UID of 1000, which
# should match current host user in most situations:
RUN usermod -u 1000 apache && \
    echo "apache ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Creating Python symlink:
RUN mkdir -p /opt/invenio/lib/python/invenio && \
    ln -s /opt/invenio/lib/python/invenio /usr/lib/python2.4/site-packages && \
    ln -s /opt/invenio/lib/python/invenio /usr/lib64/python2.4/site-packages && \
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
    echo "[program:exim]" >> /etc/supervisord.conf && \
    echo "command=/usr/sbin/exim -bd -q1h" >> /etc/supervisord.conf && \
    echo "user=exim" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:mysqld]" >> /etc/supervisord.conf && \
    echo "command=/usr/bin/mysqld_safe" >> /etc/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisord.conf && \
    echo "user=root" >> /etc/supervisord.conf && \
    echo "" >> /etc/supervisord.conf && \
    echo "[program:httpd]" >> /etc/supervisord.conf && \
    echo "command=/usr/sbin/apachectl -D FOREGROUND" >> /etc/supervisord.conf

# Adding current directory as `/code`; assuming people have `maint-1.0` branch checked out:
# (note: this invalidates cache, but most of hard yum install is done by now)
ADD . /code
WORKDIR /code
RUN chown -R apache /code

# Installing Invenio:
USER apache
RUN sudo /sbin/service mysqld restart && \
    rm -rf autom4te.cache/ && \
    aclocal && \
    automake -a && \
    autoconf && \
    ./configure && \
    make -s clean && \
    make -s && \
    ls -ld /opt/invenio && \
    ls -l /opt/invenio && \
    make -s install && \
    make -s install-jquery-plugins && \
    make -s install-mathjax-plugin && \
    make -s install-ckeditor-plugin && \
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
