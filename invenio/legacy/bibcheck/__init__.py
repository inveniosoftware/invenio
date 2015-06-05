# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""
BibCheck API

This API lets other modules interact with bibcheck.
"""

import warnings

from invenio.utils.deprecation import RemovedInInvenio22Warning

warnings.warn("Legacy BibCheck will be removed in 2.2.",
              RemovedInInvenio22Warning)

from invenio.legacy.bibcheck import task as bibcheck_task

def check_record(record, enabled_rules=None):
    """
    Check a record agains some bibcheck rules.

    @param record: Record to check
    @type record: recstruct
    @param enabled_rules: List of rules to run. Default None (run all rules)
    @type enabled_rules: list
    @returns: AmendableRecord with the list of errors/amendments
    """
    plugins = bibcheck_task.load_plugins()
    rules = bibcheck_task.load_rules(plugins)
    record = bibcheck_task.AmendableRecord(record)

    rule_names = set(rules.keys())
    if enabled_rules is not None:
        rule_names.intersection_update(enabled_rules)

    for rule_name in rule_names:
        rule = rules[rule_name]
        record.set_rule(rule)
        plugin = plugins[rule["check"]]
        if plugin["batch"]:
            plugin["check_records"]([record], **rule["checker_params"])
        else:
            plugin["check_record"](record, **rule["checker_params"])

    return record
