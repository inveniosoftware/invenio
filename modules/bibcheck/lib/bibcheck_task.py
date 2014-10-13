# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014, 2015 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

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
import collections
import functools

from ConfigParser import RawConfigParser
from datetime import datetime
from tempfile import mkstemp
from invenio.bibtask import \
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
    CFG_CERN_SITE, \
    CFG_SITE_RECORD
from invenio.search_engine import \
    perform_request_search, \
    search_unit_in_bibxxx, \
    search_pattern
from invenio.bibedit_utils import get_bibrecord
from invenio.bibrecord import record_xml_output, record_add_field
from invenio.pluginutils import PluginContainer
from invenio.intbitset import intbitset
from invenio.dbquery import run_sql
from invenio.bibcatalog import BIBCATALOG_SYSTEM
from invenio.shellutils import split_cli_ids_arg
from invenio.jsonutils import json
from invenio.websearch_webcoll import get_cache_last_updated_timestamp

CFG_BATCH_SIZE = 1000

class RulesParseError(Exception):
    """ An exception indicating an error in the rules definition """
    def __init__(self, rule_name, error):
        Exception.__init__(self, "Invalid rule '%s': %s." % (rule_name,
            error))


class Tickets(object):

    """Handle ticket accumulation and dispatching."""

    def __init__(self, records):
        self.records = records
        self.policy_method = None

    def resolve_ticket_creation_policy(self):
        """Resolve the policy for creating tickets."""
        ticket_creation_policy = \
            task_get_option('ticket_creation_policy', 'per-record')

        known_policies = ('per-rule',
                          'per-record',
                          'per-rule-per-record',
                          'no-tickets')
        if ticket_creation_policy not in known_policies:
            raise Exception("Invalid ticket_creation_policy in config '{0}'".
                            format(ticket_creation_policy))

        if task_get_option('no_tickets', False):
            ticket_creation_policy = 'no-tickets'

        policy_translator = {
            'per-rule': self.tickets_per_rule,
            'per-record': self.tickets_per_record,
            'per-rule-per-record': self.tickets_per_rule_per_record
        }
        self.policy_method = policy_translator[ticket_creation_policy]

    @staticmethod
    def submit_ticket(msg_subject, msg, record_id):
        """Submit a single ticket."""
        if isinstance(msg, unicode):
            msg = msg.encode("utf-8")

        submit = functools.partial(BIBCATALOG_SYSTEM.ticket_submit,
                                   subject=msg_subject, text=msg,
                                   queue=task_get_option("queue", "Bibcheck"))
        if record_id is not None:
            submit = functools.partial(submit, recordid=record_id)
        res = submit()
        write_message("Bibcatalog returned %s" % res)
        if res > 0:
            BIBCATALOG_SYSTEM.ticket_comment(None, res, msg)

    def submit(self):
        """Generate and submit tickets for the bibcatalog system."""
        self.resolve_ticket_creation_policy()
        for ticket_information in self.policy_method():
            self.submit_ticket(*ticket_information)

    def _generate_subject(self, issue_type, record_id, rule_name):
        """Generate a fitting subject based on what information is given."""
        assert any((i is not None for i in (issue_type, record_id, rule_name)))
        return "[BibCheck{issue_type}]{record_id}{rule_name}".format(
            issue_type=":" + issue_type if issue_type else "",
            record_id=" [ID:" + record_id + "]" if self.ticket_creation_policy
            in ("per-record", "per-rule-per-record") else "",
            rule_name=" [Rule:" + rule_name + "]" if self.ticket_creation_policy
            in ("per-rule", "per-rule-per-record") else "")

    @staticmethod
    def _get_url(record):
        """Resolve the URL required to edit a record."""
        return "%s/%s/%s/edit" % (CFG_SITE_URL, CFG_SITE_RECORD,
                                  record.record_id)

    def tickets_per_rule(self):
        """Generate with the `per-rule` policy."""
        output = collections.defaultdict(list)
        for record in self.records:
            for issue in record.issues:
                output[issue.rule].append((record, issue.nature, issue.msg))
        for rule_name in output.iterkeys():
            msg = []
            for record, issue_nature, issue_msg in output[rule_name]:
                msg.append("{issue_nature}: {issue_msg}".format(
                    issue_nature=issue_nature, issue_msg=issue_msg))
                msg.append("Edit record ({record_id}) {url}\n".format(
                    record_id=record.record_id, url=self._get_url(record)))
            msg_subject = self._generate_subject(None, None, rule_name)
            yield (msg_subject, "\n".join(msg), None)

    def tickets_per_record(self):
        """Generate with the `per-record` policy."""
        output = collections.defaultdict(list)
        for record in self.records:
            for issue in record.issues:
                output[record].append((issue.nature, issue.msg))
        for record in output.iterkeys():
            msg = []
            for issue in output[record]:
                issue_nature, issue_msg = issue
                msg.append("{issue_type}: {rule_messages}".
                           format(record_id=record.record_id,
                                  issue_type=issue_nature,
                                  rule_messages=issue_msg))
            msg.append("Edit record: {url}".format(url=self._get_url(record)))
            msg_subject = self._generate_subject(None, record.record_id, None)
            yield (msg_subject, "\n".join(msg), record.record_id)

    def tickets_per_rule_per_record(self):
        """Generate with the `per-rule-per-record` policy."""
        output = collections.defaultdict(list)
        for record in self.records:
            for issue in record.issues:
                output[(issue.rule, record)].append((issue.nature, issue.msg))
        for issue_rule, record in output.iterkeys():
            msg = []
            for issue_nature, issue_msg in output[(issue_rule, record)]:
                msg.append("{issue_message}".format(issue_message=issue_msg))
            msg.append("Edit record ({record_id}): {url}".format(url=self._get_url(record),
                                                                 record_id=record.record_id))
            msg_subject = self._generate_subject(issue_nature, record.record_id,
                                                 issue_rule)
            yield (msg_subject, "\n".join(msg), record.record_id)


class Issue(object):

    """Holds information about a single record issue."""

    def __init__(self, nature, rule, msg):
        self._nature = None
        self.nature = nature
        self.rule = rule
        self.msg = msg

    @property
    def nature(self):
        return self._nature

    @nature.setter
    def nature(self, value):
        assert value in ('error', 'amendment', 'warning')
        self._nature = value

class AmendableRecord(dict):
    """ Class that wraps a record (recstruct) to pass to a plugin """
    def __init__(self, record):
        dict.__init__(self, record)
        self.issues = []
        self.valid = True
        self.amended = False
        self.holdingpen = False
        self.rule = None
        self.record_id = self["001"][0][3]

    @property
    def _errors(self):
        return [i for i in self.issues if i.nature == 'error']

    @property
    def _amendments(self):
        return [i for i in self.issues if i.nature == 'amendment']

    @property
    def _warnings(self):
        return [i for i in self.issues if i.nature == 'warning']

    def iterfields(self, fields):
        """
        This function accepts a list of marc tags (a 6 character string
        containing a 3 character tag, two 1 character indicators and an 1
        character subfield code) and returns and yields tuples of marc tags
        (without wildcards) and the field value.

        Examples:
        record.iterfields(["%%%%%%", "%%%%%_"])
            --> Iterator of all the field and subfield values.
        record.iterfields(["100__a"])
            --> The author of record
        record.iterfields(["%%%%%u"])
            --> All "u" subfields

        @param list of marc tags (accepts wildcards)
        @yields tuple (position, field_value)
        """
        for field in fields:
            for res in self.iterfield(field):
                yield res

    def iterfield(self, field):
        """ Like iterfields with only a field """
        assert len(field) == 6
        field = field.replace("_", " ")
        ind1, ind2, code = field[3:]

        for tag in self.itertags(field[:3]):
            for (local_position, field_obj) in enumerate(self[tag]):
                if ind1 in ('%', field_obj[1]) and ind2 in ('%', field_obj[2]):
                    field_name = tag + field_obj[1] + field_obj[2]
                    field_name = field_name.replace(' ', '_')
                    if code == " " and field_obj[3]:
                        position = field_name + "_", local_position, None
                        yield position, field_obj[3]
                    else:
                        for subfield_position, subfield_tuple in enumerate(field_obj[0]):
                            subfield_code, value = subfield_tuple
                            if code in ("%", subfield_code):
                                position = field_name + subfield_code, local_position, subfield_position
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
        self.issues.append(Issue('amendment', self.rule['name'], message))
        self.amended = True
        if self.rule["holdingpen"]:
            self.holdingpen = True

    def set_invalid(self, reason):
        """ Mark the record as invalid """
        url = "{site}/{record}/{record_id}".format(site=CFG_SITE_URL,
                                                   record=CFG_SITE_RECORD,
                                                   record_id=self.record_id)
        write_message("Record {url} marked as invalid by rule {name}: {reason}".
                      format(url=url, name=self.rule["name"], reason=reason))
        self.issues.append(Issue('error', self.rule['name'], reason))
        self.valid = False

    def warn(self, msg):
        """ Add a warning to the record """
        self.issues.append(Issue('warning', self.rule['name'], msg))
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
        task_set_option("reset_rules", set(val.split(",")))
    elif key in ("--enable-rules", "-e"):
        task_set_option("enabled_rules", set(val.split(",")))
    elif key in ("--id", "-i"):
        task_set_option("record_ids", intbitset(split_cli_ids_arg(val)))
    elif key in ("--queue", "-q"):
        task_set_option("queue", val)
    elif key in ("--no-tickets", "-t"):
        task_set_option("no_tickets", True)
    elif key in ("--ticket-creation-policy", "-p"):
        task_set_option("ticket_creation_policy", val)
    elif key in ("--no-upload", "-b"):
        task_set_option("no_upload", True)
    elif key in ("--dry-run", "-n"):
        task_set_option("no_upload", True)
        task_set_option("no_tickets", True)
    elif key in ("--config", "-c"):
        task_set_option("config", val)
    elif key in ("--notimechange", ):
        task_set_option("notimechange", True)
    else:
        raise StandardError("Error: Unrecognised argument '%s'." % key)
    return True

def task_run_core():
    """
    Main daemon task.

    Returns True when run successfully. False otherwise.
    """
    rules_to_reset = task_get_option("reset_rules")
    if rules_to_reset:
        write_message("Resetting the following rules: %s" % rules_to_reset)
        for rule in rules_to_reset:
            reset_rule_last_run(rule)
    plugins = load_plugins()
    rules = load_rules(plugins)
    write_message("Loaded rules: %s" % rules, verbose=9)
    task_set_option('plugins', plugins)
    recids_for_rules = get_recids_for_rules(rules)
    write_message("recids for rules: %s" % recids_for_rules, verbose=9)

    update_database = not (task_has_option('record_ids') or
                           task_get_option('no_upload', False) or
                           task_get_option('no_tickets', False))

    if update_database:
        next_starting_dates = {}
        for rule_name, rule in rules.iteritems():
            next_starting_dates[rule_name] = get_next_starting_date(rule)

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
    records_to_submit_tickets = []
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

        # Then run them through normal rules
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
                records_to_submit_tickets.append(record)

        Tickets(records).submit()

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

    # Update the database with the last time each rule was ran
    if update_database:
        for rule_name, rule in rules.iteritems():
            update_rule_last_run(rule_name, next_starting_dates[rule_name])

    return True



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
    if task_get_option("notimechange"):
        task = task_low_level_submission('bibupload', 'bibcheck', flag,
                                         tmp_file, "--notimechange")
    else:
        task = task_low_level_submission('bibupload', 'bibcheck', flag,
                                         tmp_file)
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


def get_next_starting_date(rule):
    """Calculate the date the next bibcheck run should consider as initial.

    If no filter has been specified then the time that is set is the time the
    task was started. Otherwise, it is set to the earliest date among last time
    webcoll was run and the last bibindex last_update as the last_run to prevent
    records that have yet to be categorized from being perpetually ignored.
    """
    def dt(t):
        return datetime.strptime(t, "%Y-%m-%d %H:%M:%S")

    # Upper limit
    task_starting_time = dt(task_get_task_param('task_starting_time'))

    for key, val in rule.iteritems():
        if key.startswith("filter_") and val:
            break
    else:
        return task_starting_time

    # Lower limit
    min_last_updated = run_sql("select min(last_updated) from idxINDEX")[0][0]
    cache_last_updated = dt(get_cache_last_updated_timestamp())

    return min(min_last_updated, task_starting_time, cache_last_updated)


def update_rule_last_run(rule_name, next_starting_date):
    """
    Set the last time a rule was run.

    This function should be called after a rule has been ran.
    """
    next_starting_date_str = datetime.strftime(next_starting_date,
                                               "%Y-%m-%d %H:%M:%S")

    updated = run_sql("UPDATE bibcheck_rules SET last_run=%s WHERE name=%s;",
                      (next_starting_date_str, rule_name,))
    if not updated: # rule not in the database, insert it
        run_sql("INSERT INTO bibcheck_rules(name, last_run) VALUES (%s, %s)",
                (rule_name, next_starting_date_str))

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
                modified_recids -= search_unit_in_bibxxx(p='DELETED', f='980__%', type='e')
                if CFG_CERN_SITE:
                    modified_recids -= search_unit_in_bibxxx(p='DUMMY', f='980__%', type='e')
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
      --notimechange       schedules bibuploads with the option --notimechange
                           (useful not to trigger reindexing)

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
                  "no-tickets", "no-upload", "dry-run", "config",
                  "notimechange"]),
              task_submit_elaborate_specific_parameter_fnc=task_parse_options,
              task_run_fnc=task_run_core)

