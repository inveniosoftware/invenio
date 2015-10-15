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

###############################################################################
## 1. Base (stable)                                                          ##
###############################################################################

FROM python:2.7-slim
MAINTAINER CERN <info@invenio-software.org>

# expose the right port
EXPOSE 28080

# add invenio user
RUN useradd --home-dir /home/invenio --create-home --shell /bin/bash --uid 1000 invenio

# set work dir
WORKDIR /code

# nodejs, detects distribution and adds the right repo
RUN apt-get update && \
    apt-get -qy install --fix-missing --no-install-recommends \
        curl \
        && \
    curl -sL https://deb.nodesource.com/setup_4.x | bash -

#  - package cache updates
#  - install requirements from repos
#  - clean up
#  - install python requirements
#  - install nodejs requirements
RUN apt-get update && \
    apt-get -qy upgrade --fix-missing --no-install-recommends && \
    apt-get -qy install --fix-missing --no-install-recommends \
        cython \
        gcc \
        git \
        nodejs \
        libffi-dev \
        libfreetype6-dev \
        libjpeg-dev \
        liblzma-dev \
        libmysqlclient-dev \
        libssl-dev \
        libxslt-dev \
        mysql-client \
        poppler-utils \
        sudo \
        && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg}/ && \
    (find /usr/share/doc -depth -type f ! -name copyright -delete || true) && \
    (find /usr/share/doc -empty -delete || true) && \
    rm -rf /usr/share/man/* /usr/share/groff/* /usr/share/info/* && \
    pip install --upgrade pip && \
    pip install ipdb \
        ipython \
        mock \
        unittest2 \
        watchdog \
        && \
    npm update && \
    npm install --silent -g bower less clean-css uglify-js requirejs


###############################################################################
## 2. Requirements (semi-stable)                                             ##
###############################################################################

# global environment variables:
#  - docker specific paths for Invenio
#  - proper requirements level
#  - Python extras
ENV INVENIOBASE_INSTANCE_PATH="/home/invenio/instance" \
    INVENIOBASE_STATIC_FOLDER="/home/invenio/static" \
    REQUIREMENTS="devel" \
    REXTRAS="development,docs"
#ENV REQUIREMENTS lowest
#ENV REQUIREMENTS release

# add requirement files
COPY ./requirements-devel.txt ./requirements.py ./setup.cfg ./setup.py /code/
COPY ./invenio/version.py /code/invenio/version.py

# install python requirements
# the different levels get composed from different sources
# higher levels include all requirements of lower levels
# NOTE: the compilation step is not that important, because it also compiles some tests
#       for modules that contain syntax errors on purpose (e.g. flask-registry)
RUN python requirements.py --extras=$REXTRAS --level=min > requirements.py.lowest.txt && \
    python requirements.py --extras=$REXTRAS --level=pypi > requirements.py.release.txt && \
    python requirements.py --extras=$REXTRAS --level=dev > requirements.py.devel.txt && \
    pip install --requirement requirements.py.$REQUIREMENTS.txt --allow-all-external && \
    (python -O -m compileall || true)


###############################################################################
## 3. Code (changing)                                                        ##
###############################################################################

# add current directory as `/code`.
COPY . /code


###############################################################################
## 4. Build (changing)                                                       ##
###############################################################################

#  - install invenio
#  - update Python bytecode
#  - build translation catalog
#  - clean up
RUN pip install --editable .[$REXTRAS] && \
    (python -O -m compileall . || true) && \
    rm -rf /tmp/* /var/tmp/* /var/lib/{cache,log}/ /root/.cache/*


###############################################################################
## 5. Final Steps (changing)                                                 ##
###############################################################################

# step back
# in general code should not be writeable, especially because we are using
# `pip install -e`
RUN mkdir -p /code/src && \
    chown -R invenio:invenio /code && \
    chown -R root:root /code/invenio && \
    chown -R root:root /code/scripts && \
    chown -R root:root /code/setup.* && \
    chown -R root:root /code/src
USER invenio

# add volumes
# do this AFTER `chown`, because otherwise directory permissions are not
# preserved
VOLUME ["/code", "/home/invenio", "/tmp"]

# install init scripts
ENTRYPOINT ["/code/scripts/docker_boot.sh"]

# default to bash
CMD ["bash"]

