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


# location of the folder that gets shared between containers
CFG_SHARED_FOLDER=/usr/local/var/invenio.base-instance

# prints help text and exists with the given status
print_help() {
    cat <<EOF
usage: docker_devboot (master|slave) COMMAND [ARGS...]

Helper script for running multiple docker containers while exactly one shared
Invenio setup is required. For synchronization purposes, a master-slave setup
is required. Beside the decision which container does the Invenio setup and
which container waits, there are no differences between master and slave.

Modes:
    master - run in master mode (exactly ONE container)
    slave - run in slave mode (0 or more containers)

The exit code of the subcommand is preserved.
EOF

    exit $1
}

# run the given command and return the exit code of that command
run() {
    $@
    exit $?
}

# run in master mode
# only one container should do that
run_master() {
    if [ ! -f $CFG_SHARED_FOLDER/initialized ]; then
        # prepare bower installation
        # bower is not able to handle absolute paths very well
        mkdir -p $CFG_SHARED_FOLDER/static/vendors
        ln -s $CFG_SHARED_FOLDER/static/vendors bower_components
        rm .bowerrc


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
CFG_SITE_URL = u'http://localhost:5000'
CFG_SITE_SECURE_URL = u'http://localhost:5000'
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

DEPOSIT_STORAGEDIR = u'/home/invenio/var/data/deposit/storage'

DEBUG = True
EOF

        # load dev config
        /code/scripts/setup_devmode.sh


        # final shot
        inveniomanage database init --user=root --password=mysecretpassword --yes-i-know
        inveniomanage database create

        # remember that we reached this point
        touch $CFG_SHARED_FOLDER/initialized
    fi
    run "$@"
}

# run in slave mode
# there can be multiple slaves
# don't forget to run also run a master
run_slave() {
    while [ ! -f $CFG_SHARED_FOLDER/initialized ]; do
        sleep 1
    done
    run "$@"
}

if [ "$#" -lt 2 ]; then
    print_help 0
fi

mode=$1
shift

if [ "$mode" == "master" ]; then
    run_master "$@"
elif [ "$mode" == "slave" ]; then
    run_slave "$@"
else
    print_help 1
fi
