# $id: webstatadmin.py,v 1.28 2007/04/01 23:46:46 tibor exp $
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

from __future__ import print_function

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import sys

from invenio import webstat
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsched.bibtask import task_init, task_get_option, task_set_option, \
                            task_has_option, task_update_progress, write_message
from invenio.legacy.webstat.config import CFG_WEBSTAT_CONFIG_PATH
from invenio.config import CFG_SITE_RECORD


def main():
    """Main dealing with all the BibTask magic."""
    task_init(authorization_action="runwebstatadmin",
              authorization_msg="Webstat Administrator",
              description="Description: %s Creates/deletes custom events. Can be set\n"
                          "             to cache key events and previously defined custom events.\n" % sys.argv[0],
              help_specific_usage="  -n, --new-event=ID            create a new custom event with the human-readable ID\n"
                                  "  -r, --remove-event=ID         remote the custom event with id ID and all its data\n"
                                  "  -S, --show-events             show all currently available custom events\n"
                                  "  -c, --cache-events=CLASS|[ID] caches the events defined by the class or IDs, e.g.:\n"
                                  "                                  -c ALL\n"
                                  "                                  -c KEYEVENTS\n"
                                  "                                  -c CUSTOMEVENTS\n"
                                  "                                  -c 'event id1',id2,'testevent'\n"
                                  "  -d,--dump-config              dump default config file\n"
                                  "  -e,--load-config              create the custom events described in config_file\n"
                                  "\nWhen creating events (-n) the following parameters are also applicable:\n"
                                  "  -l, --event-label=NAME  set a descriptive label to the custom event\n"
                                  "  -a, --args=[NAME]       set column headers for additional custom event arguments\n"
                                  "                          (e.g. -a country,person,car)\n",
              version=__revision__,
              specific_params=("n:r:Sl:a:c:de", ["new-event=", "remove-event=", "show-events",
                                                  "event-label=", "args=", "cache-events=", "dump-config",
                                                  "load-config"]),
              task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
              task_submit_check_options_fnc=task_submit_check_options,
              task_run_fnc=task_run_core)


def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """
    Given the string key it checks it's meaning, eventually using the value.
    Usually it fills some key in the options dict. It must return True if
    it has elaborated the key, False, if it doesn't know that key.  eg:
    """
    if key in ("-n", "--new-event"):
        task_set_option("create_event_with_id", value)

    elif key in ("-r", "--remove-event"):
        task_set_option("destroy_event_with_id", value)

    elif key in ("-S", "--show-events"):
        task_set_option("list_events", True)

    elif key in ("-l", "--event-label"):
        task_set_option("event_name", value)

    elif key in ("-a", "--args"):
        task_set_option("column_headers", value.split(','))

    elif key in ("-c", "--cache-events"):
        task_set_option("cache_events", value.split(','))

    elif key in ("-d", "--dump-config"):
        task_set_option("dump_config", True)

    elif key in ("-e", "--load-config"):
        task_set_option("load_config", True)

    else:
        return False

    return True


def task_submit_check_options():
    """
    NOTE: Depending on the parameters, either "BibSched mode" or plain
          straigh-forward execution mode is entered.
    """
    if task_has_option("create_event_with_id"):
        print(webstat.create_customevent(task_get_option("create_event_with_id"),
                                         task_get_option("event_name", None),
                                         task_get_option("column_headers", [])))
        sys.exit(0)

    elif task_has_option("destroy_event_with_id"):
        print(webstat.destroy_customevent(task_get_option("destroy_event_with_id")))
        sys.exit(0)

    elif task_has_option("list_events"):
        events = webstat._get_customevents()
        if len(events) == 0:
            print("There are no custom events available.")
        else:
            print("Available custom events are:\n")
            print('\n'.join([x[0] + ": " + ((x[1] == None) and "No descriptive name" or str(x[1])) for x in events]))
        sys.exit(0)

    elif task_has_option("cache_events"):
        events = task_get_option("cache_events")

        write_message(str(events), verbose=9)

        if events[0] == 'ALL':
            keyevents_to_cache = webstat.KEYEVENT_REPOSITORY.keys()
            customevents_to_cache = [x[0] for x in webstat._get_customevents()]

        elif events[0] == 'KEYEVENTS':
            keyevents_to_cache = webstat.KEYEVENT_REPOSITORY.keys()
            customevents_to_cache = []

        elif events[0] == 'CUSTOMEVENTS':
            keyevents_to_cache = []
            customevents_to_cache = [x[0] for x in webstat._get_customevents()]

        elif events[0] != '':
            keyevents_to_cache = [x for x in webstat.KEYEVENT_REPOSITORY.keys() if x in events]
            customevents_to_cache = [x[0] for x in webstat._get_customevents() if x in events]

        # Control so that we have valid event names
        if len(keyevents_to_cache + customevents_to_cache) == 0:
            # Oops, no events. Abort and display help.
            return False
        else:
            task_set_option("keyevents", keyevents_to_cache)
            task_set_option("customevents", customevents_to_cache)

        return True

    elif task_has_option("dump_config"):
        print("""\
[general]
visitors_box = True
search_box = True
record_box = True
bibsched_box = True
basket_box = True
apache_box = True
uptime_box = True

[webstat_custom_event_1]
name = baskets
param1 = action
param2 = basket
param3 = user

[apache_log_analyzer]
profile = nil
nb-histogram-items-to-print = 20
exclude-ip-list = ("137.138.249.162")
home-collection = "Atlantis Institute of Fictive Science"
search-interface-url = "/?"
detailed-record-url = "/%s/"
search-engine-url = "/search?"
search-engine-url-old-style = "/search.py?"
basket-url = "/yourbaskets/"
add-to-basket-url = "/yourbaskets/add"
display-basket-url = "/yourbaskets/display"
display-public-basket-url = "/yourbaskets/display_public"
alert-url = "/youralerts/"
display-your-alerts-url = "/youralerts/list"
display-your-searches-url = "/youralerts/display"
""" % CFG_SITE_RECORD)
        sys.exit(0)

    elif task_has_option("load_config"):
        from ConfigParser import ConfigParser
        conf = ConfigParser()
        conf.read(CFG_WEBSTAT_CONFIG_PATH)
        for section in conf.sections():
            if section[:21] == "webstat_custom_event_":
                cols = []
                name = ""
                for option, value in conf.items(section):
                    if option == "name":
                        name = value
                    if option[:5] == "param":
                        # add the column name in it's position
                        index = int(option[-1]) - 1
                        while len(cols) <= index:
                            cols.append("")
                        cols[index] = value
                if name:
                    res = run_sql("SELECT COUNT(id) FROM staEVENT WHERE id = %s", (name, ))
                    if res[0][0] == 0:
                        # name does not exist, create customevent
                        webstat.create_customevent(name, name, cols)
                    else:
                        # name already exists, update customevent
                        webstat.modify_customevent(name, cols=cols)

        sys.exit(0)

    else:
        # False means that the --help should be displayed
        return False


def task_run_core():
    """
    When this function is called, the tool has entered BibSched mode, which means
    that we're going to cache events according to the parameters.
    """
    write_message("Initiating rawdata caching")
    task_update_progress("Initating rawdata caching")

    # Cache key events
    keyevents = task_get_option("keyevents")
    if keyevents and len(keyevents) > 0:
        for i in range(len(keyevents)):
            write_message("Caching key event 1: %s" % keyevents[i])
            webstat.cache_keyevent_trend(keyevents)
            task_update_progress("Part 1/2: done %d/%d" % (i + 1, len(keyevents)))

    # Cache custom events
    customevents = task_get_option("customevents")
    if len(customevents) > 0:
        for i in range(len(customevents)):
            write_message("Caching custom event 1: %s" % customevents[i])
            webstat.cache_customevent_trend(customevents)
            task_update_progress("Part 2/2: done %d/%d" % (i + 1, len(customevents)))

    write_message("Finished rawdata caching succesfully")
    task_update_progress("Finished rawdata caching succesfully")

    return True
