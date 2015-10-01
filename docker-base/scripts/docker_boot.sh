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
export CFG_SHARED_FOLDER=${CFG_SHARED_FOLDER:=/opt/invenio}
export CFG_STATIC_FOLDER=${INVENIOBASE_STATIC_FOLDER:=/opt/invenio_static}

CFG_MARKER_LOCK=$CFG_SHARED_FOLDER/boot.lock
CFG_MARKER_DONE=$CFG_SHARED_FOLDER/boot.initialized
CFG_MARKER_RUNNING=$CFG_SHARED_FOLDER/boot.running
# echo function for stderr
echoerr() { echo "$@" 1>&2; }

# test if connection is reachable
# usage: test_connection_by_protocol PROTO URI
#     PROTO: {tcp,udp}
#     URI: HOST:PORT
#
# return 1 on success, 0 otherwise
test_connection_by_protocol()  {
    address=$(echo $2 | sed 's/:.*//')
    port=$(echo $2 | sed 's/[^:]*://')
    printf "$1://$address:$port..."

    # use builtin bash function
    timeout 1 bash -c "cat < /dev/null > /dev/$1/$address/$port" 2> /dev/null
    if [ $? == 0 ]; then
        echo YES
        return 1
    else
        echo NO
        return 0
    fi
}

# test if connection is reachable
# usage: test_connection NAME URI
#     NAME: name of the conneciton
#     URI: {tcp,udp}://HOST:PORT
#
# return 1 on success, 0 otherwise
test_connection() {
    printf "Test $1..."

    # TCP or UDP?
    if [[ $2 =~ ^tcp://.*$ ]]; then
        address_port=$(echo $2 | sed 's/tcp:\/\///')
        test_connection_by_protocol tcp $address_port
        return $?
    elif [[ $2 =~ ^udp://.*$ ]]; then
        address_port=$(echo $2 | sed 's/udp:\/\///')
        test_connection_by_protocol udp $address_port
        return $?
    fi

    # always succeed for unkown protocols
    return 1
}

# wait for all ports described in ENV variables of the form [A-Z]*_PORT
wait_for_services() {
    echo "Check if all services are reachable:"
    ok=0

    while [[ $ok == 0 ]]; do
        sleep 2
        ok=1
        for e in $(printenv); do
            # still ok or can we skip that cycle?
            if [[ $ok == 1 ]]; then
                k=$(echo $e | sed 's/=.*//')
                if [[ $k =~ ^[A-Z]*_PORT$  ]]; then
                    v=$(echo $e | sed 's/[^=]*=//')
                    test_connection $k $v
                    ok=$?
                fi
            fi
        done
    done
    echo "DONE, all services are up"
}

init() {
    # prepare bower installation
    # bower is not able to handle absolute paths very well
    mkdir -p $CFG_STATIC_FOLDER/vendors
    ln -s $CFG_STATIC_FOLDER/vendors bower_components
    rm .bowerrc

    # set some additional configs to be in sync with the docker-compose
    # setup. do this before the dev setup, because it sets some paths to
    # avoid permission problems. hardcoding the cfg file is required,
    # because starting invenio and asking for the path would try to create
    # the storage paths and will fail.
    # WARNING: Be careful when modifying the Invenio configuration file
    # directly because the file is parsed as python and therefore a mistake
    # will lead to a non-starting Invenio setup.
    cfgfile=$INVENIOBASE_INSTANCE_PATH/invenio.cfg
    mkdir -p $INVENIOBASE_INSTANCE_PATH
    cat <<EOF >> "$cfgfile"
CFG_SITE_URL = u'http://localhost:28080'
CFG_SITE_SECURE_URL = u'http://localhost:28080'

CFG_BATCHUPLOADER_DAEMON_DIR = u'/opt/invenio/var/batchupload'
CFG_BIBDOCFILE_FILEDIR = u'/opt/invenio/var/data/files'
CFG_BIBEDIT_CACHEDIR = u'/opt/invenio/var/tmp-shared/bibedit-cache'
CFG_BIBSCHED_LOGDIR = u'/opt/invenio/var/log/bibsched'
CFG_BINDIR = u'/usr/local/bin'
CFG_CACHEDIR = u'/opt/invenio/var/cache'
CFG_ETCDIR = u'/opt/invenio/etc'
CFG_LOCALEDIR = u'/opt/invenio/share/locale'
CFG_LOGDIR = u'/opt/invenio/var/log'
CFG_PYLIBDIR = u'/usr/local/lib/python2.7'
CFG_RUNDIR = u'/opt/invenio/var/run'
CFG_TMPDIR = u'/tmp/invenio-`hostname`'
CFG_TMPSHAREDDIR = u'/opt/invenio/var/tmp-shared'
CFG_WEBDIR = u'/opt/invenio/var/www'

DEPOSIT_STORAGEDIR = u'/opt/invenio/var/data/deposit/storage'
EOF

    # additional config through hook
    # this can be used by overlays and module testers
    if [ -n "$INVENIO_ADD_CONFIG" ]; then
        for c in $INVENIO_ADD_CONFIG; do
            cat $c >> "$cfgfile"
        done
    fi

    # load dev config
    /src/scripts/setup_devmode.sh

    # final shot
    echo "inveniomanage database init"
    inveniomanage database init --user=root --password=mysecretpassword --yes-i-know
    echo "inveniomanage database create"
    inveniomanage database create
}

# before doing anything, we wait for our services
wait_for_services

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
        echo "init done"

        # remember that we reached this point
        touch $CFG_MARKER_DONE
        rm -f $CFG_MARKER_RUNNING
    fi
) 200>$CFG_MARKER_LOCK

# run payload
exec $@
