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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Redirecting engine.
"""

import datetime
from sqlalchemy.exc import IntegrityError

from invenio.base.utils import autodiscover_redirect_methods
from invenio.ext.sqlalchemy import db
from invenio.modules.redirector.models import Goto
from invenio.utils.datastructures import LazyDict
from invenio.utils.json import json, json_unicode_to_utf8


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
    if Goto.query.filter_by(label=label).first() is not None:
        raise ValueError("%s label already exists" % label)
    if plugin not in REDIRECT_METHODS:
        raise ValueError("%s plugin does not exist" % plugin)
    if parameters is None:
        parameters = {}
    try:
        parameters.items() ## dummy test to see if it exposes the dict interface
        json_parameters = json.dumps(parameters)
    except Exception as err:
        raise ValueError("The parameters %s do not specify a valid JSON map: %s" % (parameters, err))
    try:
        now = datetime.datetime.now()
        goto = Goto(label=label, plugin=plugin, parameters=json_parameters, creation_date=now, modification_date=now)
        db.session.add(goto)
        db.session.commit()

    except IntegrityError:
        if Goto.query.filter_by(label=label).first() is not None:
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
    goto = Goto.query.filter_by(label=label).first()
    if goto is None:
        raise ValueError("%s label does not already exist" % label)
    if plugin not in REDIRECT_METHODS:
        raise ValueError("%s plugin does not exist" % plugin)
    if parameters is None:
        parameters = {}
    try:
        parameters.items() ## dummy test to see if it exposes the dict interface
        json_parameters = json.dumps(parameters)
    except Exception as err:
        raise ValueError("The parameters %s do not specify a valid JSON map: %s" % (parameters, err))
    goto.plugin = plugin
    goto.parameters = json_parameters
    goto.modification_date = datetime.datetime.now()
    db.session.commit()

def drop_redirection(label):
    """
    Delete an existing redirection identified by label.

    @param label: the uniquely identifying label for this redirection
    @type label: string
    """
    goto = Goto.query.filter_by(label=label).first()
    db.session.delete(goto)
    db.session.commit()


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
    res = Goto.query.filter_by(label=label).first()
    if res is not None:
        return {'label': res.label,
                 'plugin': REDIRECT_METHODS[res.plugin],
                 'parameters': json_unicode_to_utf8(json.loads(res.parameters)),
                 'creation_date': res.creation_date,
                 'modification_date': res.modification_date}
    else:
        raise ValueError("%s label does not exist" % label)


def is_redirection_label_already_taken(label):
    """
    Returns True in case the given label is already taken.
    """
    return Goto.query.filter_by(label=label).first() is not None
