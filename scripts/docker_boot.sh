#!/usr/bin/env bash
#
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
#
#
# usage: docker_devboot COMMAND [ARGS...]
#
# Helper script for running multiple docker containers while exactly one shared
# Invenio setup is required. For synchronization purposes, a master-slave setup
# will be used. The roles are automatically detected.
#
# The exit code of the subcommand is preserved.


# location of the folder that gets shared between containers
CFG_SHARED_FOLDER=/usr/local/var/invenio.base-instance

CFG_MARKER_LOCK=$CFG_SHARED_FOLDER/boot.lock
CFG_MARKER_DONE=$CFG_SHARED_FOLDER/boot.initialized
CFG_MARKER_RUNNING=$CFG_SHARED_FOLDER/boot.running

CFG_SSL_CURVE=secp521r1
CFG_SSL_DAYS=1024

# echo function for stderr
echoerr() { echo "$@" 1>&2; }

init() {
    # prepare bower installation
    # bower is not able to handle absolute paths very well
    mkdir -p $CFG_SHARED_FOLDER/static/vendors
    ln -s $CFG_SHARED_FOLDER/static/vendors bower_components
    rm .bowerrc


    # create certificates for celery
    PATH_CELERY_SSL=/home/invenio/ssl/celery
    mkdir -p $PATH_CELERY_SSL
    openssl ecparam -name $CFG_SSL_CURVE -genkey -param_enc explicit -out $PATH_CELERY_SSL/ca.key
    openssl req -x509 -new -nodes -key $PATH_CELERY_SSL/ca.key -days $CFG_SSL_DAYS -out $PATH_CELERY_SSL/ca.pem -subj "/C=CH/ST=Test/L=Geneva/O=Invenio/CN=Invenio Celery CA"
    openssl ecparam -name $CFG_SSL_CURVE -genkey -param_enc explicit -out $PATH_CELERY_SSL/client.key
    openssl req -new -nodes -key $PATH_CELERY_SSL/client.key -out $PATH_CELERY_SSL/client.csr -subj "/C=CH/ST=Test/L=Geneva/O=Invenio/CN=Invenio Celery Client"
    openssl x509 -req -days $CFG_SSL_DAYS -in $PATH_CELERY_SSL/client.csr -signkey $PATH_CELERY_SSL/ca.key -out $PATH_CELERY_SSL/client.pem
    rm $PATH_CELERY_SSL/client.csr


    # set some additional configs to be in sync with the docker-compose
    # setup. do this before the dev setup, because it sets some paths to
    # avoid permission problems. hardcoding the cfg file is required,
    # because starting invenio and asking for the path would try to create
    # the storage paths and will fail.
    # WARNING: Be careful when modifying the Invenio configuration file
    # directly because the file is parsed as python and therefore a mistake
    # will lead to a non-starting Invenio setup.
    cfgfile=/usr/local/var/invenio.base-instance/invenio.cfg
    cat <<EOF >> "$cfgfile"
CFG_SITE_URL = u'http://localhost:28080'
CFG_SITE_SECURE_URL = u'http://localhost:28080'
CFG_REDIS_HOSTS = {'default': [{'db': 0, 'host': 'cache', 'port': 6379}]}

CFG_BATCHUPLOADER_DAEMON_DIR = u'/home/invenio/var/batchupload'
CFG_BIBDOCFILE_FILEDIR = u'/home/invenio/var/data/files'
CFG_BIBEDIT_CACHEDIR = u'/home/invenio/var/tmp-shared/bibedit-cache'
CFG_BIBSCHED_LOGDIR = u'/home/invenio/var/log/bibsched'
CFG_BINDIR = u'/usr/local/bin'
CFG_CACHEDIR = u'/home/invenio/var/cache'
CFG_ETCDIR = u'/home/invenio/etc'
CFG_LOCALEDIR = u'/home/invenio/share/locale'
CFG_LOGDIR = u'/home/invenio/var/log'
CFG_PYLIBDIR = u'/usr/local/lib/python2.7'
CFG_RUNDIR = u'/home/invenio/var/run'
CFG_TMPDIR = u'/tmp/invenio-`hostname`'
CFG_TMPSHAREDDIR = u'/home/invenio/var/tmp-shared'
CFG_WEBDIR = u'/home/invenio/var/www'
CFG_WEBSUBMIT_BIBCONVERTCONFIGDIR = u'/home/invenio/etc/bibconvert/config'
CFG_WEBSUBMIT_COUNTERSDIR = u'/home/invenio/var/data/submit/counters'
CFG_WEBSUBMIT_STORAGEDIR = u'/home/invenio/var/data/submit/storage'

CELERY_TASK_SERIALIZER = u'auth'
CELERY_SECURITY_SERIALIZER = u'msgpack'
CELERY_SECURITY_DIGEST = u'sha256'
CELERY_SECURITY_KEY = u'/home/invenio/ssl/celery/client.key'
CELERY_SECURITY_CERTIFICATE = u'/home/invenio/ssl/celery/client.pem'
CELERY_SECURITY_CERT_STORE = u'/home/invenio/ssl/celery/ca.pem'

DEPOSIT_STORAGEDIR = u'/home/invenio/var/data/deposit/storage'
EOF

    # load dev config
    /code/scripts/setup_devmode.sh


    # final shot
    inveniomanage database init --user=root --password=mysecretpassword --yes-i-know
    inveniomanage database create
}

# locked block
(
    flock --exclusive 200

    # init required?
    if [ ! -f $CFG_MARKER_DONE ]; then
        # check if a process tried to init but somehow failed
        if [ -f $CFG_MARKER_RUNNING ]; then
            echoerr 'Something went wrong. System is partial initialized and not recoverable!'
            echoerr 'Deletion and recreation of containers is the recommended solution.'
            exit 1
        fi
        touch $CFG_MARKER_RUNNING

        init


        # remember that we reached this point
        touch $CFG_MARKER_DONE
        rm -f $CFG_MARKER_RUNNING
    fi
) 200>$CFG_MARKER_LOCK

# run payload
exec $@
