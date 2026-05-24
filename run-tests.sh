#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2015-2018 CERN.
# SPDX-License-Identifier: MIT

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Always bring down services
function cleanup {
  eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

python -m check_manifest --ignore ".*-requirements.txt"
python -m sphinx.cmd.build -qnNW docs docs/_build/html
eval "$(docker-services-cli up --db ${DB:-postgresql} --search ${SEARCH:-elasticsearch} --cache ${CACHE:-redis} --mq ${MQ:-rabbitmq} --env)"
python -m pytest
tests_exit_code=$?
exit "$tests_exit_code"
