#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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
#
#
# Sets the configuration of Invenio to defaults which are sutable for
# developers.
#
# !!!                             WARNING                               !!!
# !!! Do NOT use these configurations in production without adjustement !!!
#

echo "Load predefined configuration. Please ADJUST this before running in production mode!"

# initialize Invenio configuration and search for the reported config file path
inveniomanage config create secret-key
cfgfile=$(inveniomanage config locate)

# add a bunch of config flags to the config file this is faster than calling
# `inveniomanaga config set` multiple times
# WARNING: Be careful when modifying the Invenio configuration file directly
# because the file is parsed as python and therefore a mistake will lead to a
# non-starting Invenio setup.
cat <<EOF >> "$cfgfile"
CFG_EMAIL_BACKEND = u'flask_email.backends.console.Mail'
CFG_BIBSCHED_PROCESS_USER = u'`whoami`'
PACKAGES_EXCLUDE = []
CFG_TMPDIR = u'/tmp'
COLLECT_STORAGE = u'flask_collect.storage.link'
EOF

# fetch and build assets
inveniomanage bower -i bower-base.json > bower.json
bower install --silent
inveniomanage collect > /dev/null
inveniomanage assets build

echo "Load predefined configuration. Please ADJUST this before running in production mode!"
