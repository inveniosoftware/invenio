from uuid import uuid4

from sqlalchemy_utils import UUIDType

from invenio.ext.sqlalchemy import db, utils


class SQLAlchemyNode(object):

    """TODO"""

    def _edges(self, inwards=True, outwards=True, link_type=None):
        """TODO"""
        query = SQLAlchemyEdge.query

        if inwards and outwards:
            query = query.filter((SQLAlchemyEdge.id_to == self['_id']) |
                                 (SQLAlchemyEdge.id_from == self['_id']))
        elif inwards:
            query = query.filter(SQLAlchemyEdge.id_to == self['_id'])
        elif outwards:
            query = query.filter(SQLAlchemyEdge.id_from == self['_id'])

        if link_type:
            query = query.filter(SQLALchemyEdge.link_type == link_type)

        return query

    def in_edges(self, link_type=None):
        """TODO"""
        edges = self._edges(outwards=False, link_type=link_type)

        return edges.all()

    def in_degree(self, link_type=None):
        """TODO"""
        return len(self.in_edges())

    def out_edges(self, link_type=None):
        """TODO"""
        edges = self._edges(inwards=False, link_type=link_type)

        return edges.all()

    def out_degree(self, link_type=None):
        """TODO"""
        return len(self.out_edges())

    def predecessors(self, link_type=None):
        """TODO"""
        in_edges = self.in_edges(link_type=link_type)

        return [edge.from_node() for edge in in_edges]

    def successors(self, link_type=None):
        """TODO"""
        out_edges = self.out_edges(link_type=link_type)

        return [edge.to_node() for edge in out_edges]


class SQLAlchemyEdge(db.Model):

    """Represent a graph edge."""

    __tablename__ = "relationship"

    uuid = db.Column(UUIDType(binary=False), primary_key=True)

    model_from = db.Column(db.String(255), nullable=True, index=True)
    id_from = db.Column(db.Integer(unsigned=True), nullable=True, index=True)

    link_type = db.Column(db.String(255), index=True)
    attributes = db.Column(db.JSON)

    model_to = db.Column(db.String(255), nullable=True, index=True)
    id_to = db.Column(db.Integer(unsigned=True), nullable=True, index=True)

    def __init__(self, json_from, link_type, attributes, json_to, uuid=None):
        """Initialize a relationship between two records.

        :param json_from: JSON
            The source record.
        :param link_type: string
            The kind of relationship.
        :param json_to: JSON
            The target record.
        :param uuid: UUID
            Presetted UUID. Optional.

        """
        self.uuid = uuid4() if uuid is None else uuid
        self.model_from = json_from.__storagename__
        self.id_from = str(json_from['_id'])
        self.link_type = link_type
        self.attributes = attributes
        self.model_to = json_to.__storagename__
        self.id_to = str(json_to['_id'])

    def get_uuid(self):
        return self.uuid

    def from_node(self):
        return (self.model_from, self.id_from)

    def to_node(self):
        return (self.model_to, self.id_to)

    def get_link_type(self):
        return self.link_type

    def get_attributes(self):
        return self.attributes

    @utils.session_manager
    def save(self):
        db.session.add(self)
