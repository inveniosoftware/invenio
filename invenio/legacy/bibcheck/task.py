# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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
BibCheck task

This task will check the records against a defined set of rules.
"""
import sys
import getopt
import os
import traceback
import time
import inspect
import itertools

from collections import namedtuple
from ConfigParser import RawConfigParser
from datetime import datetime
from tempfile import mkstemp
from invenio.legacy.bibsched.bibtask import \
    task_init, \
    task_set_option, \
    task_has_option, \
    task_get_option, write_message, \
    task_update_progress, \
    task_sleep_now_if_required, \
    get_modified_records_since, \
    task_low_level_submission, \
    task_get_task_param
from invenio.config import \
    CFG_VERSION, \
    CFG_ETCDIR, \
    CFG_PYLIBDIR, \
    CFG_SITE_URL, \
    CFG_TMPSHAREDDIR, \
    CFG_CERN_SITE
from invenio.legacy.search_engine import \
    perform_request_search, \
    search_unit_in_bibxxx, \
    search_pattern
from invenio.legacy.bibedit.utils import get_bibrecord
from invenio.legacy.bibrecord import record_xml_output, record_add_field
from intbitset import intbitset
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibcatalog.api import BIBCATALOG_SYSTEM
from invenio.utils.shell import split_cli_ids_arg
from invenio.utils.json import json

CFG_BATCH_SIZE = 1000

class RulesParseError(Exception):
    """ An exception indicating an error in the rules definition """
    def __init__(self, rule_name, error):
        Exception.__init__(self, "Invalid rule '%s': %s." % (rule_name,
            error))


class AmendableRecord(dict):
    """ Class that wraps a record (recstruct) to pass to a plugin """
    def __init__(self, record):
        dict.__init__(self, record)
        self.errors = []
        self.amendments = []
        self.warnings = []
        self.valid = True
        self.amended = False
        self.holdingpen = False
        self.rule = None
        self.record_id = self["001"][0][3]

    def iterfields(self, fields, subfield_filter=(None, None)):
        """
        Iterates over marc tags that match a marc expression.

        This function accepts a list of marc tags (a 6 character string
        containing a 3 character tag, two 1 character indicators and an 1
        character subfield code) and returns and yields tuples of marc tags
        (without wildcards) and the field value. Optionally filters for subfield
        values.

        Examples:
        record.iterfields(["%%%%%%", "%%%%%_"])
            --> Iterator of all the field and subfield values.
                ('_' is for control fields that have no codes)
        record.iterfields(["100__a"])
            --> The author of record
        record.iterfields(["%%%%%u"])
            --> All "u" subfields

        :param fields: marc tags (accepts wildcards)
        :type fields: list of str
        :param subfield_filter: filter for a specific subfield
        :type subfield_filter: (str, str)
        :yields: (position, field_value)
            `position` is (tag, localpos, fieldpos) if filter was disabled, or
                          (tag, localpos, fieldpos, filterpos) if filter was enabled
        """
        for field in fields:
            for res in self.iterfield(field, subfield_filter=subfield_filter):
                yield res

    def iterfield(self, field, subfield_filter=(None, None)):
        """Like iterfields for a single field."""
        assert len(field) == 6
        field = field.replace("_", " ")
        ind1, ind2, code = field[3:]

        assert len(subfield_filter) == 2
        SubfieldFilter = namedtuple('SubfieldFilter', ['code', 'value'])
        subfield_filter = SubfieldFilter(*subfield_filter)
        filter_enabled = subfield_filter.code is not None

        def filter_passes(subfield_code, result):
            return subfield_filter.code in ('%', subfield_code) and \
                subfield_filter.value == result

        for tag in self.itertags(field[:3]):
            for (local_position, field_obj) in enumerate(self[tag]):
                if ind1 in ('%', field_obj[1]) and ind2 in ('%', field_obj[2]):
                    field_name = tag + field_obj[1] + field_obj[2]
                    field_name = field_name.replace(' ', '_')
                    if code == " " and field_obj[3]:
                        position = field_name + "_", local_position, None
                        value = field_obj[3]
                        yield position, value
                    else:
                        # `code` is code from `field`
                        # `subfield_code` is from `field_obj` (storage)
                        if filter_enabled:
                            for subfield_position, subfield_tuple in enumerate(field_obj[0]):
                                subfield_code, value = subfield_tuple
                                filter_position = None # Until challenged
                                if filter_passes(subfield_code, value):
                                    filter_position = subfield_position
                                    break
                        if not filter_enabled or filter_position is not None:
                            for subfield_position, subfield_tuple in enumerate(field_obj[0]):
                                subfield_code, value = subfield_tuple
                                if code in ("%", subfield_code):
                                    position = field_name + subfield_code, local_position, \
                                        subfield_position
                                    if filter_enabled:
                                        position = position + (filter_position,)
                                    yield position, value

    def _query(self, position):
        """ Return a position """
        tag = position[0].replace("_", " ")
        res = self[tag[0:3]]
        if position[1] is not None:
            res = res[position[1]]
            assert res[1] == tag[3] and res[2] == tag[4] # Check indicators
            if position[2] is not None:
                res = res[0][position[2]]
                assert res[0] == tag[5]
        return res

    def _queryval(self, position):
        """ Like _query() but return the value """
        if position[2] is None:
            return self._query(position)[3]
        else:
            return self._query(position)[1]

    def amend_field(self, position, new_value, message=""):
        """
        Changes the value of the field in the specified position to new value
        and marks the record as amended.

        Optional message to explain what was changed.
        """
        tag, localpos, subfieldpos = position
        tag = tag.replace("_", " ")

        old_value = self._queryval(position)
        if new_value != old_value:
            if position[2] is None:
                fields = self[tag[0:3]]
                fields[localpos] = fields[localpos][0:3] + (new_value,)
            else:
                self._query(position[:2] + (None,))[0][subfieldpos] = (tag[5], new_value)
            if message == '':
                message = u"Changed field %s from '%s' to '%s'" % (position[0],
                        old_value.decode('utf-8'), new_value.decode('utf-8'))
            self.set_amended(message)

    def delete_field(self, position, message=""):
        """
        Delete a field or subfield. Returns the deleted field or subfield
        """
        if message == "":
            message = u"Deleted field %s" % (position[0])
        self.set_amended(message)
        if position[2] is None:
            return self._query(position[:1] + (None, None)).pop(position[1])
        else:
            return self._query(position[:2] + (None,))[0].pop(position[2])

    def add_field(self, tag, value, subfields=None):
        """ Add a field """
        tag = tag.replace("_", " ")
        record_add_field(self, tag[:3], tag[3], tag[4], value, subfields)
        self.set_amended("Added field %s" % tag)

    def add_subfield(self, position, code, value):
        """ Add a subfield to the field in the specified field """
        self._query(position[:2] + (None,))[0].append((code, value))
        self.set_amended("Added subfield %s='%s' to field %s" % (code, value,
            position[0][:5]))

    def set_amended(self, message):
        """ Mark the record as amended """
        write_message("Amended record %s by rule %s: %s" %
                (self.record_id, self.rule["name"], message))
        self.amendments.append("Rule %s: %s" % (self.rule["name"], message))
        self.amended = True
        if self.rule["holdingpen"]:
            self.holdingpen = True

    def set_invalid(self, reason):
        """ Mark the record as invalid """
        write_message("Record %s marked as invalid by rule %s: %s" %
                (CFG_SITE_URL + "/record/%s" % self.record_id, self.rule["name"], reason))
        self.errors.append("Rule %s: %s" % (self.rule["name"], reason))
        self.valid = False

    def warn(self, msg):
        """ Add a warning to the record """
        self.warnings.append("Rule %s: %s" % (self.rule["name"], msg))
        write_message("[WARN] record %s by rule %s: %s" %
                (self.record_id, self.rule["name"], msg))

    def set_rule(self, rule):
        """ Set the current rule the record is been checked against """
        self.rule = rule

    def itertags(self, tag):
        """
        Yields the tags of the record that matching

        @param tag: tag with wildcards
        @yields tags without wildcards
        """
        if "%" in tag:
            for key in self.iterkeys():
                if ((tag[0] in ("%", key[0])) and
                    (tag[1] in ("%", key[1])) and
                    (tag[2] in ("%", key[2]))):
                    yield key
        else:
            if tag in self:
                yield tag

    def is_dummy(self):
        return len(list(self.iterfield("001%%_"))) == 1 and \
            len(self.keys()) == 1


def task_parse_options(key, val, *_):
    """ Must be defined for bibtask to create a task """

    if key in ("--all", "-a"):
        for rule_name in val.split(","):
            reset_rule_last_run(rule_name)
    elif key in ("--enable-rules", "-e"):
        task_set_option("enabled_rules", set(val.split(",")))
    elif key in ("--id", "-i"):
        task_set_option("record_ids", intbitset(split_cli_ids_arg(val)))
    elif key in ("--queue", "-q"):
        task_set_option("queue", val)
    elif key in ("--no-tickets", "-t"):
        task_set_option("no_tickets", True)
    elif key in ("--no-upload", "-b"):
        task_set_option("no_upload", True)
    elif key in ("--dry-run", "-n"):
        task_set_option("no_upload", True)
        task_set_option("no_tickets", True)
    elif key in ("--config", "-c"):
        task_set_option("config", val)
    else:
        raise StandardError("Error: Unrecognised argument '%s'." % key)
    return True

def task_run_core():
    """
    Main daemon task.

    Returns True when run successfully. False otherwise.
    """
    plugins = load_plugins()
    rules = load_rules(plugins)
    task_set_option('plugins', plugins)
    recids_for_rules = get_recids_for_rules(rules)

    all_recids = intbitset([])
    single_rules = set()
    batch_rules = set()
    for rule_name, rule_recids in recids_for_rules.iteritems():
        all_recids.union_update(rule_recids)
        if plugins[rules[rule_name]["check"]]["batch"]:
            batch_rules.add(rule_name)
        else:
            single_rules.add(rule_name)

    records_to_upload_holdingpen = []
    records_to_upload_replace = []
    for batch in iter_batches(all_recids, CFG_BATCH_SIZE):

        for rule_name in batch_rules:
            rule = rules[rule_name]
            rule_recids = recids_for_rules[rule_name]
            task_sleep_now_if_required(can_stop_too=True)
            records = []
            for i, record_id, record in batch:
                if record_id in rule_recids:
                    records.append(record)
            if len(records):
                check_records(rule, records)

        # Then run them trught normal rules
        for i, record_id, record in batch:
            progress_percent = int(float(i) / len(all_recids) * 100)
            task_update_progress("Processing record %s/%s (%i%%)." %
                        (i, len(all_recids), progress_percent))
            write_message("Processing record %s" % record_id)

            for rule_name in single_rules:
                rule = rules[rule_name]
                rule_recids = recids_for_rules[rule_name]
                task_sleep_now_if_required(can_stop_too=True)
                if record_id in rule_recids:
                    check_record(rule, record)

            if record.amended:
                if record.holdingpen:
                    records_to_upload_holdingpen.append(record)
                else:
                    records_to_upload_replace.append(record)

            if not record.valid:
                submit_ticket(record, record_id)

        if len(records_to_upload_holdingpen) >= CFG_BATCH_SIZE:
            upload_amendments(records_to_upload_holdingpen, True)
            records_to_upload_holdingpen = []
        if len(records_to_upload_replace) >= CFG_BATCH_SIZE:
            upload_amendments(records_to_upload_replace, False)
            records_to_upload_replace = []

    ## In case there are still some remaining amended records
    if records_to_upload_holdingpen:
        upload_amendments(records_to_upload_holdingpen, True)
    if records_to_upload_replace:
        upload_amendments(records_to_upload_replace, False)

    # Update the database with the last time the rules was ran
    for rule in rules.keys():
        update_rule_last_run(rule)

    return True

def submit_ticket(record, record_id):
    """ Submit the errors to bibcatalog """

    if task_get_option("no_tickets", False):
        return

    msg = """
Bibcheck found some problems with the record with id %s:

Errors:
%s

Amendments:
%s

Warnings:
%s

Edit this record: %s
"""
    msg = msg % (
        record_id,
        "\n".join(record.errors),
        "\n".join(record.amendments),
        "\n".join(record.warnings),
        "%s/record/%s/edit" % (CFG_SITE_URL, record_id),
    )
    if isinstance(msg, unicode):
        msg = msg.encode("utf-8")

    subject = "Bibcheck rule failed in record %s" % record_id

    ticket_id = BIBCATALOG_SYSTEM.ticket_submit(
        subject=subject,
        recordid=record_id,
        text=subject,
        queue=task_get_option("queue", "Bibcheck")
    )
    write_message("Bibcatalog returned %s" % ticket_id)
    if ticket_id:
        BIBCATALOG_SYSTEM.ticket_comment(None, ticket_id, msg)


def upload_amendments(records, holdingpen):
    """ Upload a modified record """

    if task_get_option("no_upload", False) or len(records) == 0:
        return

    xml = '<collection xmlns="http://www.loc.gov/MARC21/slim">'
    for record in records:
        xml += record_xml_output(record)
    xml += "</collection>"

    tmp_file_fd, tmp_file = mkstemp(
        suffix='.xml',
        prefix="bibcheckfile_%s" % time.strftime("%Y-%m-%d_%H:%M:%S"),
        dir=CFG_TMPSHAREDDIR
    )
    os.write(tmp_file_fd, xml)
    os.close(tmp_file_fd)
    os.chmod(tmp_file, 0644)
    if holdingpen:
        flag = "-o"
    else:
        flag = "-r"
    task = task_low_level_submission('bibupload', 'bibcheck', flag, tmp_file)
    write_message("Submitted bibupload task %s" % task)

def check_record(rule, record):
    """
    Check a record against a rule
    """
    plugins = task_get_option("plugins")
    record.set_rule(rule)
    plugin = plugins[rule["check"]]
    if not record.is_dummy():
        return plugin["check_record"](record, **rule["checker_params"])

def check_records(rule, records):
    """
    Check a set of records against a batch rule
    """
    plugins = task_get_option("plugins")
    for record in records:
        record.set_rule(rule)
    plugin = plugins[rule["check"]]
    return plugin["check_records"](records, **rule["checker_params"])

def get_rule_lastrun(rule_name):
    """
    Get the last time a rule was run, or the oldest representable datetime
    if the rule was never ran.
    """
    res = run_sql("SELECT last_run FROM bibcheck_rules WHERE name=%s;",
                  (rule_name,))
    if len(res) == 0 or res[0][0] is None:
        return datetime(1900, 1, 1)
    else:
        return res[0][0]


def update_rule_last_run(rule_name):
    """
    Set the last time a rule was run to now. This function should be called
    after a rule has been ran.
    """

    if task_has_option('record_ids') or task_get_option('no_upload', False) \
            or task_get_option('no_tickets', False):
        return   # We don't want to update the database in this case

    updated = run_sql("UPDATE bibcheck_rules SET last_run=%s WHERE name=%s;",
                      (task_get_task_param('task_starting_time'), rule_name,))
    if not updated: # rule not in the database, insert it
        run_sql("INSERT INTO bibcheck_rules(name, last_run) VALUES (%s, %s)",
                (rule_name, task_get_task_param('task_starting_time')))


def reset_rule_last_run(rule_name):
    """
    Reset the last time a rule was run. This will cause the rule to be
    ran on all matching records (not only modified ones)
    """
    run_sql("DELETE FROM bibcheck_rules WHERE name=%s", (rule_name,))

def load_plugins():
    """
    Will load all the plugins found under the bibcheck_plugins folder.

    Returns a list of plugin objects.
    """
    plugin_dir = os.path.join(CFG_PYLIBDIR, "invenio/bibcheck_plugins/*.py")

    # Load plugins
    from invenio.pluginutils import PluginContainer
    plugins = PluginContainer(plugin_dir,
                              plugin_builder=_bibcheck_plugin_builder)

    # Check for broken plug-ins
    broken = plugins.get_broken_plugins()
    if broken:
        for plugin, info in broken.items():
            print "Failed to load %s:\n" % plugin
            print "".join(traceback.format_exception(*info))
    enabled = plugins.get_enabled_plugins()
    enabled.pop("__init__", None)
    return enabled

def load_rule(config, plugins, rule_name):
    """Read rule 'rule_name' from the config file """
    checker_params = {}
    rule = {
        "checker_params": checker_params,
        "holdingpen": False,
        "name": rule_name
    }

    def encode(obj):
        """ Encode a decoded json object strings """
        if isinstance(obj, dict):
            return dict([(encode(key), encode(value)) for key, value in
                        obj.iteritems()])
        elif isinstance(obj, list):
            return [encode(element) for element in obj]
        elif isinstance(obj, unicode):
            return obj.encode('utf-8')
        else:
            return obj

    def parse_arg(argument_str, arg_name):
        try:
            return encode(json.loads(argument_str))
        except ValueError:
            raise RulesParseError(rule_name, "Invalid value in argument '%s'" %
                                              arg_name)

    for key, val in config.items(rule_name):
        if key in ("filter_pattern",
                   "filter_field",
                   "filter_collection",
                   "filter_limit"):
            rule[key] = val
        elif key in ("holdingpen",
                     "consider_deleted_records"):
            rule[key] = val.lower() in ("true", "1", "yes", "on")
        elif key == "check":
            rule["check"] = val
            if val not in plugins:
                raise RulesParseError(rule_name, "Invalid checker '%s'" % val)
        elif key.startswith("check."):
            checker_params[key[len("check."):]] = parse_arg(val, key)
        else:
            raise RulesParseError(rule_name, "Invalid rule option '%s'" % key)

    if "check" not in rule:
        raise RulesParseError(rule_name, "Doesn't have a checker")

    plugin = plugins[rule["check"]]
    if not plugin["mandatory_args"].issubset(checker_params.keys()):
        raise RulesParseError(rule_name, "Plugin mandatory argument not specified")

    if not plugin["all_args"].issuperset(checker_params.keys()):
        raise RulesParseError(rule_name, "Unknown plugin argument")

    return rule


def load_rules(plugins):
    """
    Load the rules and return a dict with the rules
    """
    config = task_get_option("config", "rules.cfg")
    filename = os.path.join(CFG_ETCDIR, "bibcheck/", config)
    config = RawConfigParser()
    config.readfp(open(filename))
    rules = {}
    rule_names = config.sections()

    enabled = task_get_option("enabled_rules", None)
    if enabled is not None:
        rule_names = enabled.intersection(rule_names)

    for rule_name in rule_names:
        try:
            rules[rule_name] = load_rule(config, plugins, rule_name)
        except RulesParseError, ex:
            print ex
            write_message(ex)
    return rules


def get_recids_for_rules(rules):
    """
    Generates the final list of record IDs to load.

    @param rules dict of rules {rule_name: rule_dict}
    @type rules: dict of rules

    @return dict {rule_name: array of record IDs}
    """
    override_record_ids = task_get_option("record_ids")
    recids = {}
    for rule_name, rule in rules.iteritems():
        if "filter_pattern" in rule:
            query = rule["filter_pattern"]
            if "filter_collection" in rule:
                collections = rule["filter_collection"].split()
            else:
                collections = None
            write_message("Performing given search query: '%s'" % query)
            if collections:
                result = perform_request_search(
                    p=query,
                    of='intbitset',
                    wl=rule.get('filter_limit', 0),
                    f=rule.get('filter_field', None),
                    c=collections
                )
            else:
                result = search_pattern(
                    p=query,
                    wl=rule.get('filter_limit', 0),
                    f=rule.get('filter_field', None),
                )
        else:
            result = intbitset(trailing_bits=True)

        if override_record_ids is not None:
            result.intersection_update(override_record_ids)
        else:
            last_run = get_rule_lastrun(rule_name)
            modified_recids = get_modified_records_since(last_run)
            if not "consider_deleted_records" in rule:
                modified_recids -= search_unit_in_bibxxx(p='DELETED', f='980__%', m='e')
                if CFG_CERN_SITE:
                    modified_recids -= search_unit_in_bibxxx(p='DUMMY', f='980__%', m='e')
            result.intersection_update(modified_recids)
        recids[rule_name] = result

    return recids


def iter_batches(records, batch_size):
    """
    like enumerate_records(), but yield batches of records of size
    batch_size instead of records
    """
    iterator = enumerate_records(records)
    while True:
        batch = list(itertools.islice(iterator, batch_size))
        if len(batch) > 0:
            yield batch
        else:
            return

def enumerate_records(records):
    """
    Given an array of record IDs this function will yield a
    triplet of the count (starting from 0), the record ID and
    the record object.

    @param record: Array of record IDs
    @type record: int

    @yield: tuple (count, recordId, record structure (dict))
    """
    for i, recid in enumerate(records):
        record = get_bibrecord(int(recid))
        if not record:
            write_message("Error: could not load record '%s'." % (recid,))
            continue
        yield i, int(recid), AmendableRecord(record)


def _bibcheck_plugin_builder(plugin_name, plugin_code):
    """
    Custom builder for pluginutils.

    @param plugin_name: the name of the plugin.
    @type plugin_name: string
    @param plugin_code: the code of the module as just read from
        filesystem.
    @type plugin_code: module
    @return: the plugin
    """
    if plugin_name == "__init__":
        return
    plugin = {}
    plugin["check_record"] = getattr(plugin_code, "check_record", None)
    plugin["check_records"] = getattr(plugin_code, "check_records", None)
    plugin["name"] = plugin_name

    if (plugin["check_record"] is None) == (plugin["check_records"] is None):
        raise Exception("Plugin doesn't implement one check_record method")

    plugin["batch"] = plugin["check_records"] is not None

    argspec = inspect.getargspec(plugin["check_record"] or plugin["check_records"])
    args, defaults = argspec[0], argspec[3]
    if len(args) == 0:
        msg = "Plugin %s: check_record must accept at least one argument"
        raise Exception(msg % plugin_name)

    mandatory_args = args[1:len(args)-len(defaults or [])]
    plugin["mandatory_args"] = set(mandatory_args)
    plugin["all_args"] = set(args[1:])

    return plugin


def print_rules():
    """Prints the valid rules to stdout"""
    plugins  = load_plugins()
    for rule_name, rule in load_rules(plugins).items():
        print "Rule %s:" % rule_name
        if "filter_pattern" in rule:
            print " - Filter: %s" % rule["filter_pattern"]
        if "filter_collection" in rule:
            print " - Filter collection: %s" % rule["filter_collection"]
        print " - Checker: %s" % rule["check"]
        if len(rule["checker_params"]) > 0:
            print "      Parameters:"
            for param, val in rule["checker_params"].items():
                print "      %s = %s" % (param, json.dumps(val))

        print


def print_plugins():
    """Prints the enabled plugins to stdout"""
    all_plugins = load_plugins()
    print "Enabled plugins:"
    for plugin in all_plugins.values():
        print " -%s" % plugin["name"]
        optional_args = plugin["all_args"].difference(plugin["mandatory_args"])
        if len(plugin["mandatory_args"]):
            print "    Mandatory args: ", ", ".join(plugin["mandatory_args"])
        if len(optional_args):
            print "    Optional args: ", ", ".join(optional_args)
        print


def main():
    """Constructs the BibCheck bibtask."""
    usage = """

  Scheduled (daemon) options:

  -l, --list-plugins       List all plugins and exit
  -r, --list-rules         List all rules and exit
  -e, --enable-rules=rules Enable only some rules (comma separated)
  -a, --all=rules          Run the specified rules in all matching records (not
                               only modified ones)
  -i, --id=ids             Run only in the specified record ids or ranges (comma
                               separated), ignoring all other filters
  -q, --queue=queue        Create tickets in the specified RT Queue (Default
                               Bibcheck)
  -t, --no-tickets         Don't create any ticket in RT. Useful for debugging
  -b, --no-upload          Don't upload changes to the database
  -n, --dry-run            Like --no-tickets and --no-upload
  -c, --config             By default bibcheck reads the file rules.cfg. This
                           allows to specify a different config file

  If any of the options --id, --no-tickets, --no-upload or --dry-run is enabled,
    bibcheck won't update the last-run-time of a task in the database.

  Examples:
   (run a periodical daemon job that checks the rules from rules.cfg)
      bibcheck -s1d

   (Run bibcheck on records 1, 2, 3, 5, 6, 7, 8, 9 and 10)
      bibcheck -i 1,2,3,5-10

   (Run only the rule foobar in all the records)
      bibcheck -a foobar -e foobar

   (Run only the rules foo and bar on modified records)
      bibcheck -e foo,bar
    """
    try:
        opts = getopt.getopt(sys.argv[1:], "lr",
                                   ["list-plugins", "list-rules"])[0]
    except getopt.GetoptError:
        opts = []

    for opt, dummy in opts:
        if opt in ["-l", "--list-plugins"]:
            print_plugins()
            return
        elif opt in ["-r", "--list-rules"]:
            print_rules()
            return

    # Build and submit the task
    task_init(authorization_action='runbibcheck',
              authorization_msg="BibCheck Task Submission",
              description="",
              help_specific_usage=usage,
              version="Invenio v%s" % CFG_VERSION,
              specific_params=("hvtbnV:e:a:i:q:c:", ["help", "version",
                  "verbose=", "enable-rules=", "all=", "id=", "queue=",
                  "no-tickets", "no-upload", "dry-run", "config"]),
              task_submit_elaborate_specific_parameter_fnc=task_parse_options,
              task_run_fnc=task_run_core)

