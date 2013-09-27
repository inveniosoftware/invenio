# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""
Redirecting engine.
"""

from invenio.dbquery import run_sql, IntegrityError
from invenio.utils.json import json, json_unicode_to_utf8
from invenio.utils.datastructures import LazyDict
from invenio.base.utils import autodiscover_redirect_methods


def register_redirect_methods():
    out = {}
    for module in autodiscover_redirect_methods():
        if hasattr(module, 'goto'):
            out[module.__name__.split('.')[-1]] = module.goto
    return out

REDIRECT_METHODS = LazyDict(register_redirect_methods)


def register_redirection(label, plugin, parameters=None, update_on_duplicate=False):
    """
    Register a redirection from /goto/<LABEL> to the URL returned by running the
    given plugin (as available in REDIRECT_METHODS), with the given parameters.

    @param label: the uniquely identifying label for this redirection
    @type label: string

    @param plugin: the algorithm that should resolve the redirection, usually:
        "goto_plugin_FOO"
    @type plugin: string

    @param parameters: further parameters that should be passed to the plugin.
        This should be a dictionary or None. Note that these parameters could
        be overridden by the query parameters.
    @type parameters: dict or None

    @param update_on_duplicate: if False (default), if the label already exist it
        L{register_redirection} will raise a ValueError exception. If True, it
        will implicitly call L{update_redirection}.
    @type update_on_duplicate: bool

    @raises: ValueError in case of duplicate label and L{update_on_duplicate} is
        set to False.

    @note: parameters are going to be serialized to JSON before being stored
        in the DB. Hence only JSON-serializable values should be put there.
    """
    if run_sql("SELECT label FROM goto WHERE label=%s", (label, )):
        raise ValueError("%s label already exists" % label)
    if plugin not in REDIRECT_METHODS:
        raise ValueError("%s plugin does not exist" % plugin)
    if parameters is None:
        parameters = {}
    try:
        parameters.items() ## dummy test to see if it exposes the dict interface
        json_parameters = json.dumps(parameters)
    except Exception, err:
        raise ValueError("The parameters %s do not specify a valid JSON map: %s" % (parameters, err))
    try:
        run_sql("INSERT INTO goto(label, plugin, parameters, creation_date, modification_date) VALUES(%s, %s, %s, NOW(), NOW())", (label, plugin, json_parameters))
    except IntegrityError:
        if run_sql("SELECT label FROM goto WHERE label=%s", (label,)):
            if update_on_duplicate:
                update_redirection(label=label, plugin=plugin, parameters=parameters)
            else:
                raise ValueError("%s label already exists" % label)
        else:
            ## This is due to some other issue
            raise

def update_redirection(label, plugin, parameters=None):
    """
    Update an existing redirection from /goto/<LABEL> to the URL returned by
    running the given plugin (as available in REDIRECT_METHODS), with the given
    parameters.

    @param label: the uniquely identifying label for this redirection
    @type label: string

    @param plugin: the algorithm that should resolve the redirection, usually:
        "goto_plugin_FOO"
    @type plugin: string

    @param parameters: further parameters that should be passed to the plugin.
        This should be a dictionary or None. Note that these parameters could
        be overridden by the query parameters.
    @type parameters: dict or None

    @raises: ValueError in case the label does not already exist.

    @note: parameters are going to be serialized to JSON before being stored
        in the DB. Hence only JSON-serializable values should be put there.
    """
    if not run_sql("SELECT label FROM goto WHERE label=%s", (label, )):
        raise ValueError("%s label does not already exist" % label)
    if plugin not in REDIRECT_METHODS:
        raise ValueError("%s plugin does not exist" % plugin)
    if parameters is None:
        parameters = {}
    try:
        parameters.items() ## dummy test to see if it exposes the dict interface
        json_parameters = json.dumps(parameters)
    except Exception, err:
        raise ValueError("The parameters %s do not specify a valid JSON map: %s" % (parameters, err))
    run_sql("UPDATE goto SET plugin=%s, parameters=%s, modification_date=NOW() WHERE label=%s", (plugin, json_parameters, label))

def drop_redirection(label):
    """
    Delete an existing redirection identified by label.

    @param label: the uniquely identifying label for this redirection
    @type label: string
    """
    run_sql("DELETE FROM goto WHERE label=%s", (label, ))


def get_redirection_data(label):
    """
    Returns all information about a given redirection identified by label.

    @param label: the label identifying the redirection
    @type label: string

    @returns: a dictionary with the following keys:
        * label: the label
        * plugin: the name of the plugin
        * parameters: the parameters that are passed to the plugin
            (deserialized from JSON)
        * creation_date: datetime object on when the redirection was first
            created.
        * modification_date: datetime object on when the redirection was
            last modified.
    @rtype: dict

    @raises ValueError: in case the label does not exist.
    """
    res = run_sql("SELECT label, plugin, parameters, creation_date, modification_date FROM goto WHERE label=%s", (label, ))
    if res:
        return {'label': res[0][0],
                 'plugin': REDIRECT_METHODS[res[0][1]],
                 'parameters': json_unicode_to_utf8(json.loads(res[0][2])),
                 'creation_date': res[0][3],
                 'modification_date': res[0][4]}
    else:
        raise ValueError("%s label does not exist" % label)


def is_redirection_label_already_taken(label):
    """
    Returns True in case the given label is already taken.
    """
    return bool(run_sql("SELECT label FROM goto WHERE label=%s", (label,)))
