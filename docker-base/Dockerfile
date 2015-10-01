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

# iojs, detects distribution and adds the right repo
RUN apt-get update && \
    apt-get -qy install --fix-missing --no-install-recommends \
        curl \
        && \
    curl -sL https://deb.nodesource.com/setup_iojs_2.x | bash -

#  - package cache updates
#  - install requirements from repos
#  - clean up
#  - install python requirements
#  - install iojs requirements
RUN apt-get update && \
    apt-get -qy upgrade --fix-missing --no-install-recommends && \
    apt-get -qy install --fix-missing --no-install-recommends \
        gcc \
        git \
        iojs \
        libffi-dev \
        libjpeg-dev \
        liblzma-dev \
        libmysqlclient-dev \
        libssl-dev \
        libxslt-dev \
        mysql-client \
        poppler-utils \
        sudo \
        vim-tiny \
        && \
    apt-get clean autoclean && \
    apt-get autoremove -y && \
    rm -rf /var/lib/{apt,dpkg}/ && \
    (find /usr/share/doc -depth -type f ! -name copyright -delete || true) && \
    (find /usr/share/doc -empty -delete || true) && \
    rm -rf /usr/share/man/* /usr/share/groff/* /usr/share/info/* && \
    ln -s /usr/bin/vim.tiny /usr/bin/vim && \
    pip install --upgrade pip && \
    pip install ipdb \
        ipython \
        mock \
        unittest2 \
        watchdog \
        && \
    npm update && \
    npm install --silent -g bower less clean-css uglify-js requirejs


# global environment variables:
#  - docker specific paths for Invenio
ENV INVENIOBASE_INSTANCE_PATH="/opt/invenio/instance" \
    INVENIOBASE_STATIC_FOLDER="/opt/invenio_static"

RUN mkdir -p $INVENIOBASE_INSTANCE_PATH && \
    mkdir -p $INVENIOBASE_STATIC_FOLDER && \
    chown -R invenio:invenio /opt/

COPY ./scripts /src/scripts

# add volumes
# do this AFTER `chown`, otherwise directory permissions are not preserved
VOLUME ["/tmp", "/opt/invenio"]

# install init scripts
ENTRYPOINT ["/src/scripts/docker_boot.sh"]

# default to bash
CMD ["bash"]

