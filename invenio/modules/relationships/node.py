# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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

"""Node interface and StorageEngine metaclass."""

from flask import current_app

from invenio.utils.memoise import memoize

from six import add_metaclass, string_types

from werkzeug.utils import import_string


class StorageEngine(type):

    """Storage metaclass for parsing application config."""

    __storage_engine_registry__ = []
    __entity_types_registry__ = {}

    def __init__(cls, name, bases, dct):
        """Register cls to type registry."""
        if hasattr(cls, '__storagename__'):
            cls.__storage_engine_registry__.append(cls)
            if cls.__storagename__ not in cls.__entity_types_registry__:
                cls.__entity_types_registry__.update({cls.__storagename__:
                                                     cls})

        super(StorageEngine, cls).__init__(name, bases, dct)

    @property
    def storage_engine(cls):
        """Return an instance of storage engine defined in application config.

        It looks for key "ENGINE' prefixed by ``__storagename__.upper()`` for
        example::

            class Dummy(SmartJson):
                __storagename__ = 'dummy'

        will look for key "DUMMY_ENGINE" and
        "DUMMY_`DUMMY_ENGINE.__name__.upper()`" should contain dictionary with
        keyword arguments of the engine defined in "DUMMY_ENGINE".
        """
        storagename = cls.__storagename__.lower()
        return cls._engine(storagename)

    @staticmethod
    @memoize
    def _engine(storagename):
        prefix = storagename.upper()
        engine = current_app.config['{0}_ENGINE'.format(prefix)]
        if isinstance(engine, string_types):
            engine = import_string(engine)

        key = engine.__name__.upper()
        kwargs = current_app.config.get('{0}_{1}'.format(prefix, key), {})
        return engine(**kwargs)


@add_metaclass(StorageEngine)
class Node(object):

    """Superclass representing abstract node."""

    def __init__(self, id=None, storagename=None):
        """Initialize node.

        :param id: integer
            The id of the entity.
        :param storagename: string
            The namespace the entity belongs to.

        :raise ValueError:
            Unless sufficient arguments are provided.
        """
        self.node_storagename = storagename
        self.node_id = id

    def __eq__(self, other):
        """Overwritten equality function for Node.

        Node is equal only to another node which shares the same ``_id`` and
        ``namespace``. Such node is unique.
        """
        if isinstance(other, Node):
            return (self.node_id == other.node_id and
                    self.node_storagename == other.node_storagename)
        return False

    def degree(self, inwards=True, outwards=True, link_type=None, **kwargs):
        """Get number of edges belonging to this node.

        :param inwards: boolean
            Count the edges that are coming in to this node.
        :param outwards: boolean
            Count the edges that are coming out from this node.
        :param link_type: string
            Count only this type of edges. Optional.

        :returns: int
            Number of edges.
        """
        raise NotImplementedError

    def edges(self, inwards=True, outwards=True, link_type=None,
              loops_doubled=True, **kwargs):
        """Get all the edges of this node.

        There are no guarantees on the order of the result.

        :param inwards: boolean
            Get the edges that are coming in to this node.
        :param outwards: boolean
            Get the edges that are coming out from this node.
        :param link_type: string
            Type of the edges. Optional.
        :param loops_doubled: boolean
            If true, return every loop twice.

        :returns: list
            Edges belonging to this node.
        """
        raise NotImplementedError

    def neighbours(self, inwards=True, outwards=True, link_type=None,
                   **kwargs):
        """Get all the nodes which are neighbours of this node.

        :param inwards: boolean
            Get the vertices that are sources for this node.
        :param outwards: boolean
            Get the vertices that are destinations from this node.
        :param link_type: string
            Type of the edges. Optional.

        :returns: set
            Nodes that are neighbours of this node.
        """
        raise NotImplementedError

    def get_entity(self):
        """Get the entity that is represented by this node.

        :returns: SmartJSON object
            The entity with the metadata included.
        """
        implemented_by = self.__class__.\
            __entity_types_registry__[self.node_storagename]

        return implemented_by.get_entity(self.node_id)
