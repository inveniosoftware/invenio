# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Implementation of ``Node`` using ``SQLAlchemy``."""

from invenio.ext.sqlalchemy import db

from ..models import Relationship as SQLAlchemyRelationship
from ..node import Node


class SQLAlchemyNode(Node):

    """Node implementation for ``SQLAlchemy``."""

    def __init__(self, id=None, storagename=None):
        """Initialize node.

        :param json: SmartJSON
            The entity. If not provided, both ``id`` and ``namespace`` need
            to be provided.
        :param id: integer
            The id of the entity.
        :param namespace: string
            The namespace the entity belongs to.

        :raise ValueError:
            Unless sufficient arguments are provided.
        """
        super(SQLAlchemyNode, self).__init__(id, storagename)

    def __hash__(self):
        """Get simplified hash.

        As hash(int) equals int, it won't cause unwanted collisions.
        """
        return hash(self.node_id) ^ hash(self.node_storagename)

    def degree(self, inwards=True, outwards=True, link_type=None):
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
        return len(self.edges(inwards, outwards, link_type))

    def edges(self, inwards=True, outwards=True, link_type=None,
              loops_doubled=True):
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
        edges = SQLAlchemyRelationship.query
        if inwards and outwards:
            edges = edges.filter(db.or_(SQLAlchemyRelationship.id_to ==
                                        self.node_id,
                                        SQLAlchemyRelationship.id_from ==
                                        self.node_id))
        elif inwards:
            edges = edges.filter_by(id_to=self.node_id)
        elif outwards:
            edges = edges.filter_by(id_from=self.node_id)
        else:
            return []
        if link_type:
            edges = edges.filter_by(link_type=link_type)

        if inwards and outwards and loops_doubled:
            # Special case for loops. Second query needed.
            reflexives = SQLAlchemyRelationship.query.filter(
                db.and_(SQLAlchemyRelationship.id_to == self.node_id,
                        SQLAlchemyRelationship.id_from == self.node_id))
            if link_type:
                reflexives = reflexives.filter(link_type=link_type)
            return edges.all() + reflexives.all()

        return edges.all()

    def neighbours(self, inwards=True, outwards=True, link_type=None):
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
        edges = self.edges(inwards, outwards, link_type, loops_doubled=False)
        set1 = set(SQLAlchemyNode(id=node.id_from,
                                  storagename=node.storagename_from)
                   for node in edges)
        set2 = set(SQLAlchemyNode(id=node.id_to,
                                  storagename=node.storagename_to)
                   for node in edges)
        union = set1 | set2

        return {node.get_entity() for node in union}
