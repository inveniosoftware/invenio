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

FROM python:2.7
MAINTAINER CERN <info@invenio-software.org>

# nodejs repo
# detects distribution and adds the right repo
# See: https://github.com/joyent/node/wiki/Installing-Node.js-via-package-manager#debian-and-ubuntu-based-linux-distributions
RUN curl -sL https://deb.nodesource.com/setup | bash -

# install requirements from repos
RUN apt-get update && \
    apt-get -qy install poppler-utils git subversion nodejs mysql-client sudo --fix-missing

# install python requirements
RUN pip install --upgrade pip && \
    pip install mock && \
    pip install unittest2 && \
    pip install watchdog

# install nodejs requirements
RUN npm update && \
    npm install --silent -g bower less clean-css uglify-js requirejs

# add invenio user
RUN useradd --home-dir /home/invenio --create-home --shell /bin/bash --uid 1000 invenio


###############################################################################
## 2. Requirements (semi-stable)                                             ##
###############################################################################

# select proper requierments level
#ENV REQUIREMENTS lowest
ENV REQUIREMENTS release
#ENV REQUIREMENTS devel
ENV REXTRAS development,docs

# add requirement files
COPY ./requirements-devel.txt ./requirements.py ./setup.cfg ./setup.py /code/
COPY ./invenio/version.py /code/invenio/version.py
WORKDIR /code

# install python requirements
# the different levels get composed from different sources
# higher levels include all requirements of lower levels
RUN python requirements.py --extras=$REXTRAS --level=min > requirements.py.lowest.txt && \
    python requirements.py --extras=$REXTRAS --level=pypi > requirements.py.release.txt && \
    python requirements.py --extras=$REXTRAS --level=dev > requirements.py.devel.txt && \
    pip install -r requirements.py.$REQUIREMENTS.txt --allow-all-external --quiet


###############################################################################
## 3. Code (changing)                                                        ##
###############################################################################

# add current directory as `/code`.
COPY . /code


###############################################################################
## 4. Build (changing)                                                       ##
###############################################################################

# install invenio
RUN pip install -e .[$REXTRAS] --quiet

# build translation catalog
RUN python setup.py compile_catalog

# step back
# in general code should not be writeable, especially because we are using
# `pip install -e`
RUN mkdir -p /code/src && \
    mkdir -p /usr/local/var/invenio.base-instance && \
    chown -R invenio:invenio /code && \
    chown -R root:root /code/invenio && \
    chown -R root:root /code/scripts && \
    chown -R root:root /code/setup.* && \
    chown -R root:root /code/src && \
    chown -R invenio:invenio /usr/local/var/invenio.base-instance
USER invenio
