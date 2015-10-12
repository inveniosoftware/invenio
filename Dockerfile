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

FROM ddaze/invenio-base

WORKDIR /src/invenio

###############################################################################
## 2. Requirements (semi-stable)                                             ##
###############################################################################

# global environment variables:
#  - proper requirements level
#  - Python extras
ENV REQUIREMENTS="devel" \
    REXTRAS="development,docs"
#ENV REQUIREMENTS lowest
#ENV REQUIREMENTS release

# add requirement files
COPY ./requirements-devel.txt ./requirements.py ./setup.cfg ./setup.py /src/invenio/
COPY ./invenio/version.py /src/invenio/invenio/version.py

# install python requirements
# the different levels get composed from different sources
# higher levels include all requirements of lower levels
# NOTE: the compilation step is not that important, because it also compiles some tests
#       for modules that contain syntax errors on purpose (e.g. flask-registry)
RUN python requirements.py --extras=$REXTRAS --level=min > requirements.py.lowest.txt && \
    python requirements.py --extras=$REXTRAS --level=pypi > requirements.py.release.txt && \
    python requirements.py --extras=$REXTRAS --level=dev > requirements.py.devel.txt && \
    cd / && \
    pip install --requirement /src/invenio/requirements.py.$REQUIREMENTS.txt --allow-all-external && \
    (python -O -m compileall /src || true)


###############################################################################
## 3. Code (changing)                                                        ##
###############################################################################

# add current directory as `/src/invenio`.
COPY . /src/invenio


###############################################################################
## 4. Build (changing)                                                       ##
###############################################################################

#  - install invenio
#  - update Python bytecode
#  - clean up
RUN cd / && \
    pip install --editable /src/invenio/.[$REXTRAS] && \
    (python -O -m compileall /src || true) && \
    rm -rf /tmp/* /var/tmp/* /var/lib/{cache,log}/ /root/.cache/*


###############################################################################
## 5. Final Steps (changing)                                                 ##
###############################################################################

# in general code should not be writable, especially because we are using
# `pip install -e`
RUN chown -R invenio:invenio /src/invenio

USER invenio

# add volumes
# do this AFTER `chown`, otherwise directory permissions are not  preserved
VOLUME ["/src/invenio"]
