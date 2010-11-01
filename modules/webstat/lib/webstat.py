## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import os
import time
import re
import datetime
import cPickle
import calendar
from urllib import quote

from invenio import template
from invenio.config import \
     CFG_SITE_NAME, \
     CFG_WEBDIR, \
     CFG_TMPDIR, \
     CFG_SITE_URL, \
     CFG_SITE_LANG
from invenio.webstat_config import CFG_WEBSTAT_CONFIG_PATH
from invenio.search_engine import get_alphabetically_ordered_collection_list
from invenio.dbquery import run_sql, wash_table_column_name
from invenio.bibsched import is_task_scheduled, get_task_ids_by_descending_date, get_task_options

# Imports handling key events
from invenio.webstat_engine import get_keyevent_trend_collection_population
from invenio.webstat_engine import get_keyevent_trend_search_frequency
from invenio.webstat_engine import get_keyevent_trend_search_type_distribution
from invenio.webstat_engine import get_keyevent_trend_download_frequency
from invenio.webstat_engine import get_keyevent_snapshot_apache_processes
from invenio.webstat_engine import get_keyevent_snapshot_bibsched_status
from invenio.webstat_engine import get_keyevent_snapshot_uptime_cmd
from invenio.webstat_engine import get_keyevent_snapshot_sessions

# Imports handling custom events
from invenio.webstat_engine import get_customevent_table
from invenio.webstat_engine import get_customevent_trend
from invenio.webstat_engine import get_customevent_dump

# Imports for handling outputting
from invenio.webstat_engine import create_graph_trend
from invenio.webstat_engine import create_graph_dump

# Imports for handling exports
from invenio.webstat_engine import export_to_python
from invenio.webstat_engine import export_to_csv

TEMPLATES = template.load('webstat')

# Constants
WEBSTAT_CACHE_INTERVAL = 600 # Seconds, cache_* functions not affected by this.
                             # Also not taking into account if BibSched has webstatadmin process.
WEBSTAT_RAWDATA_DIRECTORY = CFG_TMPDIR + "/"
WEBSTAT_GRAPH_DIRECTORY = CFG_WEBDIR + "/img/"

TYPE_REPOSITORY = [ ('gnuplot', 'Image - Gnuplot'),
                    ('asciiart', 'Image - ASCII art'),
                    ('asciidump', 'Image - ASCII dump'),
                    ('python', 'Data - Python code', export_to_python),
                    ('csv', 'Data - CSV', export_to_csv) ]

# Key event repository, add an entry here to support new key measures.
KEYEVENT_REPOSITORY = { 'collection population':
                          { 'fullname': 'Collection population',
                            'specificname': 'Population in collection "%(collection)s"',
                            'gatherer': get_keyevent_trend_collection_population,
                            'extraparams': {'collection': ('Collection', get_alphabetically_ordered_collection_list)},
                            'cachefilename': 'webstat_%(id)s_%(collection)s_%(timespan)s',
                            'ylabel': 'Number of records',
                            'multiple': None,
                           },
                        'search frequency':
                          { 'fullname': 'Search frequency',
                            'specificname': 'Search frequency',
                            'gatherer': get_keyevent_trend_search_frequency,
                            'extraparams': {},
                            'cachefilename': 'webstat_%(id)s_%(timespan)s',
                            'ylabel': 'Number of searches',
                            'multiple': None,
                           },
                        'search type distribution':
                          { 'fullname': 'Search type distribution',
                            'specificname': 'Search type distribution',
                            'gatherer': get_keyevent_trend_search_type_distribution,
                            'extraparams': {},
                            'cachefilename': 'webstat_%(id)s_%(timespan)s',
                            'ylabel': 'Number of searches',
                            'multiple': ['Simple searches', 'Advanced searches'],
                           },
                        'download frequency':
                          { 'fullname': 'Download frequency',
                            'specificname': 'Download frequency',
                            'gatherer': get_keyevent_trend_download_frequency,
                            'extraparams': {},
                            'cachefilename': 'webstat_%(id)s_%(timespan)s',
                            'ylabel': 'Number of downloads',
                            'multiple': None,
                           }
                       }

# CLI

def create_customevent(id=None, name=None, cols=[]):
    """
    Creates a new custom event by setting up the necessary MySQL tables.

    @param id: Proposed human-readable id of the new event.
    @type id: str

    @param name: Optionally, a descriptive name.
    @type name: str

    @param cols: Optionally, the name of the additional columns.
    @type cols: [str]

    @return: A status message
    @type: str
    """
    if id is None:
        return "Please specify a human-readable ID for the event."

    # Only accept id and name with standard characters
    if not re.search("[^\w]", str(id) + str(name)) is None:
        return "Please note that both event id and event name needs to be written without any non-standard characters."

    # Make sure the chosen id is not already taken
    if len(run_sql("SELECT NULL FROM staEVENT WHERE id = %s", (id,))) != 0:
        return "Event id [%s] already exists! Aborted." % id

    # Check if the cols are valid titles
    for argument in cols:
        if (argument == "creation_time") or (argument == "id"):
            return "Invalid column title: %s! Aborted." % argument

    # Insert a new row into the events table describing the new event
    sql_param = [id]
    if name is not None:
        sql_name = "%s"
        sql_param.append(name)
    else:
        sql_name = "NULL"
    if len(cols) != 0:
        sql_cols = "%s"
        sql_param.append(cPickle.dumps(cols))
    else:
        sql_cols = "NULL"
    run_sql("INSERT INTO staEVENT (id, name, cols) VALUES (%s, " + sql_name + ", " + sql_cols + ")",
            tuple(sql_param))

    tbl_name = get_customevent_table(id)

    # Create a table for the new event
    sql_query = ["CREATE TABLE %s (" % tbl_name]
    sql_query.append("id MEDIUMINT unsigned NOT NULL auto_increment,")
    sql_query.append("creation_time TIMESTAMP DEFAULT NOW(),")
    for argument in cols:
        arg = wash_table_column_name(argument)
        sql_query.append("%s MEDIUMTEXT NULL," % arg)
        sql_query.append("INDEX %s (%s(50))," % (arg, arg))
    sql_query.append("PRIMARY KEY (id))")
    sql_str = ' '.join(sql_query)
    run_sql(sql_str)

    # We're done! Print notice containing the name of the event.
    return ("Event table [%s] successfully created.\n" +
            "Please use event id [%s] when registering an event.") % (tbl_name, id)

def modify_customevent(id=None, name=None, cols=[]):
    """
    Modify a custom event. It can modify the columns definition
    or/and the descriptive name

    @param id: Human-readable id of the event.
    @type id: str

    @param name: Optionally, a descriptive name.
    @type name: str

    @param cols: Optionally, the name of the additional columns.
    @type cols: [str]

    @return: A status message
    @type: str
    """
    if id is None:
        return "Please specify a human-readable ID for the event."

    # Only accept name with standard characters
    if not re.search("[^\w]", str(name)) is None:
        return "Please note that event name needs to be written without any non-standard characters."

    # Check if the cols are valid titles
    for argument in cols:
        if (argument == "creation_time") or (argument == "id"):
            return "Invalid column title: %s! Aborted." % argument

    res = run_sql("SELECT CONCAT('staEVENT', number), cols FROM staEVENT WHERE id = %s", (id,))
    cols_orig = cPickle.loads(res[0][1])

    # add new cols
    cols_add = []
    for col in cols:
        if not col in cols_orig:
            cols_add.append(col)

    # del old cols
    cols_del = []
    for col in cols_orig:
        if not col in cols:
            cols_del.append(col)

    #modify event table
    if cols_del or cols_add:
        sql_query = ["ALTER TABLE %s " % res[0][0]]
        for col in cols_del:
            sql_query.append("DROP COLUMN `%s`" % col)
            sql_query.append(", ")
        for col in cols_add:
            sql_query.append("ADD COLUMN `%s` MEDIUMTEXT NULL, " % col)
            sql_query.append("ADD INDEX `%s` (`%s`(50))" % (col, col))
            sql_query.append(", ")
        sql_query[-1] = ";"
        run_sql("".join(sql_query))

    #modify event definition
    sql_query = ["UPDATE staEVENT SET"]
    sql_param = []
    if cols_del or cols_add:
        sql_query.append("cols = %s")
        sql_query.append(",")
        sql_param.append(cPickle.dumps(cols))
    if name:
        sql_query.append("name = %s")
        sql_query.append(",")
        sql_param.append(name)
    if sql_param:
        sql_query[-1] = "WHERE id = %s"
        sql_param.append(id)
        sql_str = ' '.join(sql_query)
        run_sql(sql_str, sql_param)

    # We're done! Print notice containing the name of the event.
    return ("Event table [%s] successfully modified." % (id,))

def destroy_customevent(id=None):
    """
    Removes an existing custom event by destroying the MySQL tables and
    the event data that might be around. Use with caution!

    @param id: Human-readable id of the event to be removed.
    @type id: str

    @return: A status message
    @type: str
    """
    if id is None:
        return "Please specify an existing event id."

    # Check if the specified id exists
    if len(run_sql("SELECT NULL FROM staEVENT WHERE id = %s", (id,))) == 0:
        return "Event id [%s] doesn't exist! Aborted." % id
    else:
        tbl_name = get_customevent_table(id)
        run_sql("DROP TABLE %s" % tbl_name)
        run_sql("DELETE FROM staEVENT WHERE id = %s", (id,))
        return ("Event with id [%s] was successfully destroyed.\n" +
                "Table [%s], with content, was destroyed.") % (id, tbl_name)

def register_customevent(id, *arguments):
    """
    Registers a custom event. Will add to the database's event tables
    as created by create_customevent().

    This function constitutes the "function hook" that should be
    called throughout Invenio where one wants to register a
    custom event! Refer to the help section on the admin web page.

    @param id: Human-readable id of the event to be registered
    @type id: str

    @param *arguments: The rest of the parameters of the function call
    @type *arguments: [params]
    """
    res = run_sql("SELECT CONCAT('staEVENT', number),cols FROM staEVENT WHERE id = %s",  (id,))
    if not res:
        return # the id does not exist
    tbl_name = res[0][0]
    if res[0][1]:
        col_titles = cPickle.loads(res[0][1])
    else:
        col_titles = []
    if len(col_titles) != len(arguments[0]):
        return # there is different number of arguments than cols

    # Make sql query
    if len(arguments[0]) != 0:
        sql_param = []
        sql_query = ["INSERT INTO %s (" % tbl_name]
        for title in col_titles:
            sql_query.append("`%s`" % title)
            sql_query.append(",")
        sql_query.pop() # del the last ','
        sql_query.append(") VALUES (")
        for argument in arguments[0]:
            sql_query.append("%s")
            sql_query.append(",")
            sql_param.append(argument)
        sql_query.pop() # del the last ','
        sql_query.append(")")
        sql_str = ''.join(sql_query)
        run_sql(sql_str, tuple(sql_param))
    else:
        run_sql("INSERT INTO %s () VALUES ()" % tbl_name)

def cache_keyevent_trend(ids=[]):
    """
    Runs the rawdata gatherer for the specific key events.
    Intended to be run mainly but the BibSched daemon interface.

    For a specific id, all possible timespans' rawdata is gathered.

    @param ids: The key event ids that are subject to caching.
    @type ids: []
    """
    args = {}
    timespans = _get_timespans()

    for id in ids:
        args['id'] = id
        extraparams = KEYEVENT_REPOSITORY[id]['extraparams']

        # Construct all combinations of extraparams and store as [{param name: arg value}]
        # so as we can loop over them and just pattern-replace the each dictionary against
        # the KEYEVENT_REPOSITORY['id']['cachefilename'].
        combos = [[]]
        for x in [[(param, x[0]) for x in extraparams[param][1]()] for param in extraparams]:
            combos = [i + [y] for y in x for i in combos]
        combos = [dict(x) for x in combos]

        for i in range(len(timespans)):
            # Get timespans parameters
            args['timespan'] = timespans[i][0]
            args.update({ 't_start': timespans[i][2], 't_end': timespans[i][3], 'granularity': timespans[i][4],
                          't_format': timespans[i][5], 'xtic_format': timespans[i][6] })

            for combo in combos:
                args.update(combo)

                # Create unique filename for this combination of parameters
                filename = KEYEVENT_REPOSITORY[id]['cachefilename'] \
                            % dict([(param, re.subn("[^\w]", "_", args[param])[0]) for param in args])

                # Create closure of gatherer function in case cache needs to be refreshed
                gatherer = lambda: KEYEVENT_REPOSITORY[id]['gatherer'](args)

                # Get data file from cache, ALWAYS REFRESH DATA!
                _get_file_using_cache(filename, gatherer, True).read()

    return True

def cache_customevent_trend(ids=[]):
    """
    Runs the rawdata gatherer for the specific custom events.
    Intended to be run mainly but the BibSched daemon interface.

    For a specific id, all possible timespans' rawdata is gathered.

    @param ids: The custom event ids that are subject to caching.
    @type ids: []
    """
    args = {}
    timespans = _get_timespans()

    for id in ids:
        args['id'] = id
        args['cols'] = []

        for i in range(len(timespans)):
            # Get timespans parameters
            args['timespan'] = timespans[i][0]
            args.update({ 't_start': timespans[i][2], 't_end': timespans[i][3], 'granularity': timespans[i][4],
                          't_format': timespans[i][5], 'xtic_format': timespans[i][6] })

            # Create unique filename for this combination of parameters
            filename = "webstat_customevent_%(id)s_%(timespan)s" \
                        % { 'id': re.subn("[^\w]", "_", id)[0], 'timespan': re.subn("[^\w]", "_", args['timespan'])[0] }

            # Create closure of gatherer function in case cache needs to be refreshed
            gatherer = lambda: get_customevent_trend(args)

            # Get data file from cache, ALWAYS REFRESH DATA!
            _get_file_using_cache(filename, gatherer, True).read()

    return True

def basket_display():
    """
    Display basket statistics.
    """
    tbl_name = get_customevent_table("baskets")
    if not tbl_name:
        # custom event baskets not defined, so return empty output:
        return []
    try:
        res = run_sql("SELECT creation_time FROM %s ORDER BY creation_time" % tbl_name)
        days = (res[-1][0] - res[0][0]).days + 1
        public = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'display_public'" % tbl_name)[0][0]
        users = run_sql("SELECT COUNT(DISTINCT user) FROM %s" % tbl_name)[0][0]
        adds = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'add'" % tbl_name)[0][0]
        displays = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'display' OR action = 'display_public'" % tbl_name)[0][0]
        hits = adds + displays
        average = hits / days

        res = [("Basket page hits", hits)]
        res.append(("   Average per day", average))
        res.append(("   Unique users", users))
        res.append(("   Additions", adds))
        res.append(("   Public", public))
    except IndexError:
        res = []

    return res

def alert_display():
    """
    Display alert statistics.
    """
    tbl_name = get_customevent_table("alerts")
    if not tbl_name:
        # custom event alerts not defined, so return empty output:
        return []
    try:
        res = run_sql("SELECT creation_time FROM %s ORDER BY creation_time" % tbl_name)
        days = (res[-1][0] - res[0][0]).days + 1
        res = run_sql("SELECT COUNT(DISTINCT user),COUNT(*) FROM %s" % tbl_name)
        users = res[0][0]
        hits = res[0][1]
        displays = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'list'" % tbl_name)[0][0]
        search = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'display'" % tbl_name)[0][0]
        average = hits / days

        res = [("Alerts page hits", hits)]
        res.append(("   Average per day", average))
        res.append(("   Unique users", users))
        res.append(("   Displays", displays))
        res.append(("   Searches history display", search))
    except IndexError:
        res = []

    return res

def get_url_customevent(url_dest, id, *arguments):
    """
    Get an url for registers a custom event. Every time is load the
    url will register a customevent as register_customevent().

    @param id: Human-readable id of the event to be registered
    @type id: str

    @param *arguments: The rest of the parameters of the function call
                       the param "WEBSTAT_IP" will tell webstat that here
                       should be the IP who request the url
    @type *arguments: [params]

    @param id: url to redirect after register the event
    @type id: str

    @return: url for register event
    @type: str
    """
    return "%s/stats/customevent_register?id=%s&arg=%s&url=%s" % \
            (CFG_SITE_URL, id, ','.join(arguments[0]), quote(url_dest))

# WEB

def perform_request_index(ln=CFG_SITE_LANG):
    """
    Displays some informative text, the health box, and a the list of
    key/custom events.
    """
    from ConfigParser import ConfigParser
    conf = ConfigParser()
    conf.read(CFG_WEBSTAT_CONFIG_PATH)
    out = TEMPLATES.tmpl_welcome(ln=ln)

    # Prepare the health base data
    health_indicators = []
    now = datetime.datetime.now()
    yesterday = (now-datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now+datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # Append session information to the health box
    if conf.get("general", "visitors_box") == "True":
        sess = get_keyevent_snapshot_sessions()
        health_indicators.append(("Total active visitors", sum(sess)))
        health_indicators.append(("    Logged in", sess[1]))
        health_indicators.append(None)

    # Append searches information to the health box
    if conf.get("general", "search_box") == "True":
        args = { 't_start': today, 't_end': tomorrow, 'granularity': "day", 't_format': "%Y-%m-%d" }
        searches = get_keyevent_trend_search_type_distribution(args)
        health_indicators.append(("Searches since midnight", sum(searches[0][1])))
        health_indicators.append(("    Simple", searches[0][1][0]))
        health_indicators.append(("    Advanced", searches[0][1][1]))
        health_indicators.append(None)

    # Append new records information to the health box
    if conf.get("general", "record_box") == "True":
        args = { 'collection': CFG_SITE_NAME, 't_start': today, 't_end': tomorrow, 'granularity': "day", 't_format': "%Y-%m-%d" }
        try: tot_records = get_keyevent_trend_collection_population(args)[0][1]
        except IndexError: tot_records = 0
        args = { 'collection': CFG_SITE_NAME, 't_start': yesterday, 't_end': today, 'granularity': "day", 't_format': "%Y-%m-%d" }
        try: new_records = tot_records - get_keyevent_trend_collection_population(args)[0][1]
        except IndexError: new_records = 0
        health_indicators.append(("Total records", tot_records))
        health_indicators.append(("    New records since midnight", new_records))
        health_indicators.append(None)

    # Append status of BibSched queue to the health box
    if conf.get("general", "bibsched_box") == "True":
        bibsched = get_keyevent_snapshot_bibsched_status()
        health_indicators.append(("BibSched queue", sum([x[1] for x in bibsched])))
        for item in bibsched:
            health_indicators.append(("    " + item[0], str(item[1])))
        health_indicators.append(None)

    # Append basket stats to the health box
    if conf.get("general", "basket_box") == "True":
        health_indicators += basket_display()
        health_indicators.append(None)

    # Append alerts stats to the health box
    if conf.get("general", "alert_box") == "True":
        health_indicators += alert_display()
        health_indicators.append(None)

    # Append number of Apache processes to the health box
    if conf.get("general", "apache_box") == "True":
        health_indicators.append(("Apache processes", get_keyevent_snapshot_apache_processes()))

    # Append uptime and load average to the health box
    if conf.get("general", "uptime_box") == "True":
        health_indicators.append(("Uptime cmd", get_keyevent_snapshot_uptime_cmd()))

    # Display the health box
    out += TEMPLATES.tmpl_system_health(health_indicators, ln=ln)

    # Produce a list of the key statistics
    out += TEMPLATES.tmpl_keyevent_list(ln=ln)

    # Display the custom statistics
    out += TEMPLATES.tmpl_customevent_list(_get_customevents(), ln=ln)

    return out

def perform_display_keyevent(id=None, args={}, req=None, ln=CFG_SITE_LANG):
    """
    Display key events using a certain output type over the given time span.

    @param ids: The ids for the custom events that are to be displayed.
    @type ids: [str]

    @param args: { param name: argument value }
    @type args: { str: str }

    @param req: The Apache request object, necessary for export redirect.
    @type req:
    """
    # Get all the option lists: { parameter name: [(argument internal name, argument full name)]}
    options = dict([(param,
                     (KEYEVENT_REPOSITORY[id]['extraparams'][param][0],
                      KEYEVENT_REPOSITORY[id]['extraparams'][param][1]())) for param in
                    KEYEVENT_REPOSITORY[id]['extraparams']] +
                   [('timespan', ('Time span', _get_timespans())), ('format', ('Output format', _get_formats()))])
    # Order of options
    order = [param for param in KEYEVENT_REPOSITORY[id]['extraparams']] + ['timespan', 'format']
    # Build a dictionary for the selected parameters: { parameter name: argument internal name }
    choosed = dict([(param, args[param]) for param in KEYEVENT_REPOSITORY[id]['extraparams']] +
                   [('timespan', args['timespan']), ('format', args['format'])])
    # Send to template to prepare event customization FORM box
    out = TEMPLATES.tmpl_keyevent_box(options, order, choosed, ln=ln)

    # Arguments OK?

    # Check for existance. If nothing, only show FORM box from above.
    if len(choosed) == 0:
        return out

    # Make sure extraparams are valid, if any
    for param in choosed:
        if not choosed[param] in [x[0] for x in options[param][1]]:
            return out + TEMPLATES.tmpl_error('Please specify a valid value for parameter "%s".'
                                               % options[param][0], ln=ln)

    # Arguments OK beyond this point!

    # Get unique name for caching purposes (make sure that the params used in the filename are safe!)
    filename = KEYEVENT_REPOSITORY[id]['cachefilename'] \
               % dict([(param, re.subn("[^\w]", "_", choosed[param])[0]) for param in choosed] +
                      [('id', re.subn("[^\w]", "_", id)[0])])

    # Get time parameters from repository
    # TODO: This should quite possibly be lifted out (webstat_engine?), in any case a cleaner repository
    _, t_fullname, t_start, t_end, granularity, t_format, xtic_format = \
        options['timespan'][1][[x[0] for x in options['timespan'][1]].index(choosed['timespan'])]
    args = { 't_start': t_start, 't_end': t_end, 'granularity': granularity,
             't_format': t_format, 'xtic_format': xtic_format }
    for param in KEYEVENT_REPOSITORY[id]['extraparams']:
        args[param] = choosed[param]

    # Create closure of frequency function in case cache needs to be refreshed
    gatherer = lambda: KEYEVENT_REPOSITORY[id]['gatherer'](args)

    # Determine if this particular file is due for scheduling cacheing, in that case we must not
    # allow refreshing of the rawdata.
    allow_refresh = not _is_scheduled_for_cacheing(id)

    # Get data file from cache (refresh if necessary)
    data = eval(_get_file_using_cache(filename, gatherer, allow_refresh=allow_refresh).read())

    # If type indicates an export, run the export function and we're done
    if _is_type_export(choosed['format']):
        _get_export_closure(choosed['format'])(data, req)
        return out

    # Prepare the graph settings that are being passed on to grapher
    settings = { "title": KEYEVENT_REPOSITORY[id]['specificname'] % choosed,
                  "xlabel": t_fullname + ' (' + granularity + ')',
                  "ylabel": KEYEVENT_REPOSITORY[id]['ylabel'],
                  "xtic_format": xtic_format,
                  "format": choosed['format'],
                  "multiple": KEYEVENT_REPOSITORY[id]['multiple'] }

    return out + _perform_display_event(data, os.path.basename(filename), settings, ln=ln)

def perform_display_customevent(ids=[], args={}, req=None, ln=CFG_SITE_LANG):
    """
    Display custom events using a certain output type over the given time span.

    @param ids: The ids for the custom events that are to be displayed.
    @type ids: [str]

    @param args: { param name: argument value }
    @type args: { str: str }

    @param req: The Apache request object, necessary for export redirect.
    @type req:
    """
    # Get all the option lists: { parameter name: [(argument internal name, argument full name)]}
    cols_dict = _get_customevent_cols()
    cols_dict['__header'] = 'Argument'
    cols_dict['__none'] = []
    options = { 'ids': ('Custom event', _get_customevents()),
                'timespan': ('Time span', _get_timespans()),
                'format': ('Output format', _get_formats(True)),
                'cols': cols_dict }

    # Build a dictionary for the selected parameters: { parameter name: argument internal name }
    choosed = { 'ids': args['ids'], 'timespan': args['timespan'], 'format': args['format']}
    # Calculate cols
    index = []
    for key in args.keys():
        if key[:4] == 'cols':
            index.append(key[4:])
    index.sort()
    choosed['cols'] = [ zip([""]+args['bool'+i], args['cols'+i], args['col_value'+i])
                        for i in index ]
    # Send to template to prepare event customization FORM box
    out = TEMPLATES.tmpl_customevent_box(options, choosed, ln=ln)

    # Arguments OK?

    # Make sure extraparams are valid, if any
    for param in ['ids', 'timespan', 'format']:
        legalvalues = [x[0] for x in options[param][1]]

        if type(args[param]) is list:
            # If the argument is a list, like the content of 'ids' every value has to be checked
            if len(args[param]) == 0:
                return out + TEMPLATES.tmpl_error('Please specify a valid value for parameter "%s".' % options[param][0], ln=ln)
            for arg in args[param]:
                if not arg in legalvalues:
                    return out + TEMPLATES.tmpl_error('Please specify a valid value for parameter "%s".' % options[param][0], ln=ln)
        else:
            if not args[param] in legalvalues:
                return out + TEMPLATES.tmpl_error('Please specify a valid value for parameter "%s".' % options[param][0], ln=ln)

    # Fetch time parameters from repository
    _, t_fullname, t_start, t_end, granularity, t_format, xtic_format = \
        options['timespan'][1][[x[0] for x in options['timespan'][1]].index(choosed['timespan'])]
    args_req = { 't_start': t_start, 't_end': t_end, 'granularity': granularity,
                't_format': t_format, 'xtic_format': xtic_format }

    data_unmerged = []

    # ASCII dump data is different from the standard formats
    if choosed['format'] == 'asciidump':
        for i in [ str(j) for j in range(len(ids))]:
            args['bool'+i].insert(0, "")
            args_req['cols'+i] = zip(args['bool'+i], args['cols'+i], args['col_value'+i])
        filename = "webstat_customevent_" + re.subn("[^\w]", "", ''.join(ids) + "_" + choosed['timespan'] + "_" + '-'.join([ ':'.join(col) for col in [ args['cols'+str(i)] for i in range(len(ids))]]) + "_asciidump")[0]
        args_req['ids'] = ids
        gatherer = lambda: get_customevent_dump(args_req)
        data = eval(_get_file_using_cache(filename, gatherer).read())
    else:
        for id, i in [ (ids[i], str(i)) for i in range(len(ids))]:
            # Calculate cols
            args_req['cols'] = choosed['cols'][int(i)]

            # Get unique name for the rawdata file (wash arguments!)
            filename = "webstat_customevent_" + re.subn("[^\w]", "", id + "_" + choosed['timespan'] + "_" + '-'.join([ ':'.join(col) for col in args_req['cols']]))[0]

            # Add the current id to the gatherer's arguments
            args_req['id'] = id

            # Prepare raw data gatherer, if cache needs refreshing.
            gatherer = lambda: get_customevent_trend(args_req)

            # Determine if this particular file is due for scheduling cacheing, in that case we must not
            # allow refreshing of the rawdata.
            allow_refresh = not _is_scheduled_for_cacheing(id)

            # Get file from cache, and evaluate it to trend data
            data_unmerged.append(eval(_get_file_using_cache(filename, gatherer, allow_refresh=allow_refresh).read()))

        # Merge data from the unmerged trends into the final destination
        data = [(x[0][0], tuple([y[1] for y in x])) for x in zip(*data_unmerged)]

    # If type indicates an export, run the export function and we're done
    if _is_type_export(args['format']):
        _get_export_closure(args['format'])(data, req)
        return out

    # Get full names, for those that have them
    names = []
    events = _get_customevents()
    for id in ids:
        temp = events[[x[0] for x in events].index(id)]
        if temp[1] != None:
            names.append(temp[1])
        else:
            names.append(temp[0])

    # Generate a filename for the graph
    filename = "tmp_webstat_customevent_" + ''.join([re.subn("[^\w]", "", id)[0] for id in ids]) + "_" + choosed['timespan']

    settings = { "title": 'Custom event',
                 "xlabel": t_fullname + ' (' + granularity + ')',
                 "ylabel": "Action quantity",
                 "xtic_format": xtic_format,
                 "format": choosed['format'],
                 "multiple": (type(ids) is list) and names or [] }

    return out + _perform_display_event(data, os.path.basename(filename), settings, ln=ln)

def perform_display_customevent_help(ln=CFG_SITE_LANG):
    """Display the custom event help"""
    return TEMPLATES.tmpl_customevent_help(ln=ln)

# INTERNALS

def _perform_display_event(data, name, settings, ln=CFG_SITE_LANG):
    """
    Retrieves a graph.

    @param data: The trend/dump data
    @type data: [(str, str|int|(str|int,...))] | [(str|int,...)]

    @param name: The name of the trend (to be used as basename of graph file)
    @type name: str

    @param settings: Dictionary of graph parameters
    @type settings: dict

    @return: The URL of the graph (ASCII or image)
    @type: str
    """
    path = WEBSTAT_GRAPH_DIRECTORY + "tmp_" + name

    # Generate, and insert using the appropriate template
    if settings["format"] != "asciidump":
        create_graph_trend(data, path, settings)
        if settings["format"] == "asciiart":
            return TEMPLATES.tmpl_display_event_trend_ascii(settings["title"], path, ln=ln)
        else:
            if settings["format"] == "gnuplot":
                try:
                    import Gnuplot
                except ImportError:
                    return 'Gnuplot is not installed. Returning ASCII art.' +\
                           TEMPLATES.tmpl_display_event_trend_ascii(settings["title"], path, ln=ln)

            return TEMPLATES.tmpl_display_event_trend_image(settings["title"], path, ln=ln)
    else:
        path += "_asciidump"
        create_graph_dump(data, path, settings)
        return TEMPLATES.tmpl_display_event_trend_ascii(settings["title"], path, ln=ln)

def _get_customevents():
    """
    Retrieves registered custom events from the database.

    @return: [(internal name, readable name)]
    @type: [(str, str)]
    """
    return [(x[0], x[1]) for x in run_sql("SELECT id, name FROM staEVENT")]

def _get_timespans(dt=None):
    """
    Helper function that generates possible time spans to be put in the
    drop-down in the generation box. Computes possible years, and also some
    pre-defined simpler values. Some items in the list returned also tweaks the
    output graph, if any, since such values are closely related to the nature
    of the time span.

    @param dt: A datetime object indicating the current date and time
    @type dt: datetime.datetime

    @return: [(Internal name, Readable name, t_start, t_end, granularity, format, xtic_format)]
    @type [(str, str, str, str, str, str, str)]
    """
    if dt is None:
        dt = datetime.datetime.now()

    format = "%Y-%m-%d"
    # Helper function to return a timediff object reflecting a diff of x days
    d_diff = lambda x: datetime.timedelta(days=x)
    # Helper function to return the number of days in the month x months ago
    d_in_m = lambda x: calendar.monthrange(((dt.month-x<1) and dt.year-1 or dt.year),
                                           (((dt.month-1)-x)%12+1))[1]
    to_str = lambda x: x.strftime(format)
    dt_str = to_str(dt)

    spans = [("today", "Today",
              dt_str,
              to_str(dt+d_diff(1)),
              "hour", format, "%H"),
             ("this week", "This week",
              to_str(dt-d_diff(dt.weekday())),
              to_str(dt+d_diff(1)),
              "day", format, "%a"),
             ("last week", "Last week",
              to_str(dt-d_diff(dt.weekday()+7)),
              to_str(dt-d_diff(dt.weekday())),
              "day", format, "%a"),
             ("this month", "This month",
              to_str(dt-d_diff(dt.day)+d_diff(1)),
              to_str(dt+d_diff(1)),
              "day", format, "%d"),
             ("last month", "Last month",
              to_str(dt-d_diff(d_in_m(1))-d_diff(dt.day)+d_diff(1)),
              to_str(dt-d_diff(dt.day)+d_diff(1)),
              "day", format, "%d"),
             ("last three months", "Last three months",
              to_str(dt-d_diff(d_in_m(1))-d_diff(d_in_m(2))-d_diff(dt.day)+d_diff(1)),
              dt_str,
              "month", format, "%b"),
             ("last year", "Last year",
              to_str((dt - datetime.timedelta(days=365)).replace(day=1)),
              to_str((dt + datetime.timedelta(days=31)).replace(day=1)),
              "month", format, "%b")]

    # Get first year as indicated by the content's in bibrec
    try:
        y1 = run_sql("SELECT creation_date FROM bibrec ORDER BY creation_date LIMIT 1")[0][0].year
    except IndexError:
        y1 = dt.year

    y2 = time.localtime()[0]
    diff_year = y2 - y1
    if diff_year >= 2:
        spans.append(("last 2 years", "Last 2 years",
                      to_str((dt - datetime.timedelta(days=365*2)).replace(day=1)),
                      to_str((dt + datetime.timedelta(days=31)).replace(day=1)),
                      "month", format, "%b"))
    if diff_year >= 5:
        spans.append(("last 5 years", "Last 5 years",
                      to_str((dt - datetime.timedelta(days=365*5)).replace(day=1)),
                      to_str((dt + datetime.timedelta(days=31)).replace(day=1)),
                      "year", format, "%Y"))
    if diff_year >= 10:
        spans.append(("last 10 years", "Last 10 years",
                      to_str((dt - datetime.timedelta(days=365*10)).replace(day=1)),
                      to_str((dt + datetime.timedelta(days=31)).replace(day=1)),
                      "year", format, "%Y"))
    spans.append(("full history", "Full history", str(y1), str(y2+1), "year", "%Y", "%Y"))
    spans.extend([(str(x), str(x), str(x), str(x+1), "month", "%Y", "%b") for x in range(y2, y1-1, -1)])

    return spans

def _get_formats(with_dump=False):
    """
    Helper function to retrieve a Invenio friendly list of all possible
    output types (displaying and exporting) from the central repository as
    stored in the variable self.types at the top of this module.

    @param with_dump: Optionally displays the custom-event only type 'asciidump'
    @type with_dump: bool

    @return: [(Internal name, Readable name)]
    @type [(str, str)]
    """
    # The third tuple value is internal
    if with_dump:
        return [(x[0], x[1]) for x in TYPE_REPOSITORY]
    else:
        return [(x[0], x[1]) for x in TYPE_REPOSITORY if x[0] != 'asciidump']

def _get_customevent_cols(id=""):
    """
    List of all the diferent name of columns in customevents.

    @return: {id: [(internal name, readable name)]}
    @type: {str: [(str, str)]}
    """
    sql_str = "SELECT id,cols FROM staEVENT"
    sql_param = []
    if id:
        sql_str += "WHERE id = %s"
        sql_param.append(id)
    cols = {}
    for x in run_sql(sql_str, sql_param):
        if x[0]:
            if x[1]:
                cols[x[0]] = [ (name, name) for name in cPickle.loads(x[1]) ]
            else:
                cols[x[0]] = []
    return cols

def _is_type_export(typename):
    """
    Helper function that consults the central repository of types to determine
    whether the input parameter represents an export type.

    @param typename: Internal type name
    @type typename: str

    @return: Information whether a certain type exports data
    @type: bool
    """
    return len(TYPE_REPOSITORY[[x[0] for x in TYPE_REPOSITORY].index(typename)]) == 3

def _get_export_closure(typename):
    """
    Helper function that for a certain type, gives back the corresponding export
    closure.

    @param typename: Internal type name
    @type type: str

    @return: Closure that exports data to the type's format
    @type: function
    """
    return TYPE_REPOSITORY[[x[0] for x in TYPE_REPOSITORY].index(typename)][2]

def _get_file_using_cache(filename, closure, force=False, allow_refresh=True):
    """
    Uses the Invenio cache, i.e. the tempdir, to see if there's a recent
    cached version of the sought-after file in there. If not, use the closure to
    compute a new, and return that instead. Relies on Invenio configuration
    parameter WEBSTAT_CACHE_INTERVAL.

    @param filename: The name of the file that might be cached
    @type filename: str

    @param closure: A function, that executed will return data to be cached. The
                    function should return either a string, or something that
                    makes sense after being interpreted with str().
    @type closure: function

    @param force: Override cache default value.
    @type force: bool


    """
    # Absolute path to cached files, might not exist.
    filename = os.path.normpath(WEBSTAT_RAWDATA_DIRECTORY + filename)

    # Get the modification time of the cached file (if any).
    try:
        mtime = os.path.getmtime(filename)
    except OSError:
        # No cached version of this particular file exists, thus the modification
        # time is set to 0 for easy logic below.
        mtime = 0

    # Consider refreshing cache if FORCE or NO CACHE AT ALL, or CACHE EXIST AND REFRESH IS ALLOWED.
    if force or mtime == 0 or (mtime > 0 and allow_refresh):

        # Is the file modification time recent enough?
        if force or (time.time() - mtime > WEBSTAT_CACHE_INTERVAL):

            # No! Use closure to compute new content
            content = closure()

            # Cache the data
            open(filename, 'w').write(str(content))

    # Return the (perhaps just) cached file
    return open(filename, 'r')

def _is_scheduled_for_cacheing(id):
    """
    @param id: The event id
    @type id: str

    @return: Indication of if the event id is scheduling for BibSched execution.
    @type: bool
    """
    if not is_task_scheduled('webstatadmin'):
        return False

    # Get the task id
    try:
        task_id = get_task_ids_by_descending_date('webstatadmin', ['RUNNING', 'WAITING'])[0]
    except IndexError:
        return False
    else:
        args = get_task_options(task_id)
        return id in (args['keyevents'] + args['customevents'])
