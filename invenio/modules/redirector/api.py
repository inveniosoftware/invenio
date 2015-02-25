# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
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

"""Redirecting engine."""

from invenio.ext.sqlalchemy import db
from .models import Goto


def register_redirection(label, plugin, parameters=None,
                         update_on_duplicate=False):
    """
    Register a redirection from /goto/<LABEL> to the URL.

    Register a redirection from /goto/<LABEL> to the URL returned by
    running the given plugin (as available in REDIRECT_METHODS), with the
    given parameters.

    :param label: the uniquely identifying label for this redirection
    :type label: string

    :param plugin: the algorithm that should resolve the redirection, usually:
        "goto_plugin_FOO"
    :type plugin: string

    :param parameters: further parameters that should be passed to the plugin.
        This should be a dictionary or None. Note that these parameters could
        be overridden by the query parameters.
    :type parameters: dict

    :param update_on_duplicate: if False (default), if the label already
        exist it L{register_redirection} will raise a ValueError exception.
        If True, it will implicitly call L{update_redirection}.
    :type update_on_duplicate: bool

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case not exist
        and L{update_on_duplicate} is set to False.

    :note: parameters are going to be serialized to JSON before being stored
        in the DB. Hence only JSON-serializable values should be put there.
    """
    if not update_on_duplicate \
       or Goto.query.filter_by(label=label).first():
        goto = Goto(label=label, plugin=plugin,
                    parameters=parameters)
        db.session.add(goto)
        db.session.commit()
    else:
        update_redirection(label=label, plugin=plugin, parameters=parameters)


def update_redirection(label, plugin, parameters=None):
    """
    Update an existing redirection from /goto/<LABEL> to the URL.

    Update an existing redirection from /goto/<LABEL> to the URL returned by
    running the given plugin (as available in REDIRECT_METHODS), with the given
    parameters.

    :param label: the uniquely identifying label for this redirection
    :type label: string

    :param plugin: the algorithm that should resolve the redirection, usually:
        "goto_plugin_FOO"
    :type plugin: string

    :param parameters: further parameters that should be passed to the plugin.
        This should be a dictionary or None. Note that these parameters could
        be overridden by the query parameters.
    :type parameters: dict

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case the label does
        not already exist.

    :note: parameters are going to be serialized to JSON before being stored
        in the DB. Hence only JSON-serializable values should be put there.
    """
    goto = Goto.query.filter_by(label=label).one()
    goto.plugin = plugin
    goto.parameters = parameters
    try:
        db.session.merge(goto)
    except:
        db.session.rollback()
        # FIXME add re-raise exception
    finally:
        db.session.commit()


def drop_redirection(label):
    """
    Delete an existing redirection identified by label.

    :param label: the uniquely identifying label for this redirection
    :type label: string
    """
    Goto.query.filter_by(label=label).delete()
    db.session.commit()


def get_redirection_data(label):
    """
    Return all information about a given redirection identified by label.

    :param label: the label identifying the redirection
    :type label: string

    :returns: a dictionary with the following keys:
        * label: the label
        * plugin: the name of the plugin
        * parameters: the parameters that are passed to the plugin
        (deserialized from JSON)
        * creation_date: datetime object on when the redirection was first
        created.
        * modification_date: datetime object on when the redirection was
        last modified.
    :rtype: dict

    :raises: :exc:`~sqlalchemy.orm.exc.NoResultFound` in case the label
        does not exist.
    """
    res = Goto.query.filter_by(label=label).one()
    return res.to_dict()
