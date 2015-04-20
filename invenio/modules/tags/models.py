# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""WebTag database models."""

import re

from datetime import date, datetime

from invenio.base.globals import cfg
from invenio.ext.sqlalchemy import db
from invenio.modules.accounts.models import User, Usergroup
from invenio.modules.records.models import Record as Bibrec
from invenio.utils.text import wash_for_xml

from six import iteritems

from sqlalchemy.ext.associationproxy import association_proxy

from werkzeug import cached_property


class Serializable(object):

    """Class which can present its fields as dict for JSON serialization."""

    # Set of fields which are to be serialized
    __public__ = set([])

    def _serialize_field(self, value):
        """Convert value of a field to format suitable for json."""
        if type(value) in (datetime, date):
            return value.isoformat()

        elif hasattr(value, '__iter__'):
            result = []
            for element in value:
                result.append(self._serialize_field(element))
            return result

        elif Serializable in value.__class__.__bases__:
            return value.get_public()

        else:
            return value

    def serializable_fields(self, fields=None):
        """Return model's fields for jsonify.

        Only __public__ or fields + __public__.
        """
        data = {}
        keys = self._sa_instance_state.attrs.items()

        public = set()
        if self.__public__:
            public = public.union(self.__public__)
        if fields:
            public = public.intersection(fields)

        for key, field in keys:
            if key in public:
                value = self._serialize_field(field.value)
                if value:
                    data[key] = value

        return data


#
# TAG
#
class WtgTAG(db.Model, Serializable):

    """A Tag."""

    __tablename__ = 'wtgTAG'
    __public__ = set(['id', 'name', 'id_owner'])

    #
    # Access Rights
    #
    ACCESS_NAMES = {
        0: 'Nothing',
        10: 'View',
        20: 'Add',
        30: 'Add and remove',
        40: 'Manage',
    }

    ACCESS_LEVELS = \
        dict((v, k) for (k, v) in iteritems(ACCESS_NAMES))

    ACCESS_RIGHTS = {
        0: [],
        10: ['view'],
        20: ['view', 'add'],
        30: ['view', 'add', 'remove'],
        40: ['view', 'add', 'remove', 'edit'],
    }

    ACCESS_OWNER_DEFAULT = ACCESS_LEVELS['Manage']
    ACCESS_GROUP_DEFAULT = ACCESS_LEVELS['View']

    # Primary key
    id = db.Column(db.Integer(15, unsigned=True),
                   primary_key=True,
                   nullable=False,
                   autoincrement=True)

    # Name
    name = db.Column(db.String(255),
                     nullable=False,
                     server_default='',
                     index=True)

    # Owner
    id_user = db.Column(db.Integer(15, unsigned=True),
                        db.ForeignKey(User.id),
                        server_default='0')

    # Access rights of owner
    user_access_rights = db.Column(db.Integer(2, unsigned=True),
                                   nullable=False,
                                   default=ACCESS_OWNER_DEFAULT)

    # Group
    # equal to 0 for private tags
    id_usergroup = db.Column(
        db.Integer(15, unsigned=True),
        db.ForeignKey(Usergroup.id),
        server_default='0')

    # Group access rights
    group_access_rights = db.Column(
        db.Integer(2, unsigned=True),
        nullable=False,
        default=ACCESS_GROUP_DEFAULT)

    # Access rights of everyone
    public_access_rights = db.Column(db.Integer(2, unsigned=True),
                                     nullable=False,
                                     default=ACCESS_LEVELS['Nothing'])

    # Visibility in document description
    show_in_description = db.Column(db.Boolean,
                                    nullable=False,
                                    default=True)

    # Relationships
    user = db.relationship(User,
                           backref=db.backref('tags', cascade='all'))

    user_query = db.relationship(User,
                                 backref=db.backref('tags_query',
                                                    cascade='all',
                                                    lazy='dynamic'))

    usergroup = db.relationship(
        Usergroup,
        backref=db.backref('tags', cascade='all'))

    # association proxy of "user_keywords" collection
    # to "keyword" attribute
    records = association_proxy('records_association', 'bibrec')

    # Calculated fields
    @db.hybrid_property
    def record_count(self):
        """TODO."""
        return self.records_association_query.count()

    @record_count.expression
    def record_count(cls):
        """TODO."""
        return db.select([db.func.count(WtgTAGRecord.id_bibrec)]) \
                 .where(WtgTAGRecord.id_tag == cls.id) \
                 .label('record_count')

    @db.validates('user_access_rights')
    @db.validates('group_access_rights')
    @db.validates('public_access_rights')
    def validate_user_access_rights(self, key, value):
        """Check if the value is among defined levels."""
        assert value in WtgTAG.ACCESS_NAMES
        return value


#
# TAG - RECORD
#
class WtgTAGRecord(db.Model, Serializable):

    """Connection between Tag and Record."""

    __tablename__ = 'wtgTAG_bibrec'
    __public__ = set(['id_tag', 'id_bibrec', 'date_added'])

    # tagTAG.id
    id_tag = db.Column(db.Integer(15, unsigned=True),
                       db.ForeignKey(WtgTAG.id),
                       nullable=False,
                       primary_key=True)

    # Bibrec.id
    id_bibrec = db.Column(db.Integer(15, unsigned=True),
                          db.ForeignKey(Bibrec.id),
                          nullable=False,
                          primary_key=True)

    # Annotation
    annotation = db.Column(
        db.Text(convert_unicode=True),
        default='')

    # Creation date
    date_added = db.Column(db.DateTime,
                           default=datetime.now)

    # Relationships
    tag = db.relationship(WtgTAG,
                          backref=db.backref('records_association',
                                             cascade='all'))

    tag_query = db.relationship(WtgTAG,
                                backref=db.backref('records_association_query',
                                                   cascade='all',
                                                   lazy='dynamic'))

    bibrec = db.relationship(Bibrec,
                             backref=db.backref('tags_association',
                                                cascade='all'))

    bibrec_query = db.relationship(Bibrec,
                                   backref=db.backref('tags_association_query',
                                                      cascade='all',
                                                      lazy='dynamic'))

    def __init__(self, bibrec=None, **kwargs):
        """TODO."""
        super(WtgTAGRecord, self).__init__(**kwargs)

        if bibrec is not None:
            self.bibrec = bibrec


# Compiling once should improve regexp speed
class ReplacementList(object):

    """TODO."""

    def __init__(self, config_name):
        """TODO."""
        self.config_name = config_name

    @cached_property
    def replacements(self):
        """TODO."""
        return cfg.get(self.config_name, [])

    @cached_property
    def compiled(self):
        """TODO."""
        return [(re.compile(exp), repl)
                for (exp, repl) in self.replacements]

    def apply(self, text):
        """Apply a list of regular expression replacements to a string.

        :param replacements: list of pairs (compiled_expression, replacement)
        """
        for (reg_exp, replacement) in self.compiled:
            text = re.sub(reg_exp, replacement, text)

        return text


COMPILED_REPLACEMENTS_SILENT = \
    ReplacementList('CFG_TAGS_NAME_REPLACEMENTS_SILENT')

COMPILED_REPLACEMENTS_BLOCKING = \
    ReplacementList('CFG_TAGS_NAME_REPLACEMENTS_BLOCKING')


def wash_tag_silent(tag_name):
    r"""
    Whitespace and character cleanup.

    :param tag_name: Single tag
    :return: Tag Unicode string with all whitespace characters replaced with
        Unicode single space (' '), no whitespace at the start and end of the
        tags, no duplicate whitespace, and only characters valid in XML 1.0.
        Also applies list of replacements from CFG_WEBTAG_REPLACEMENTS_SILENT.

    Examples:

    .. code-block:: pycon

        >>> print(_tag_cleanup('Well formatted string: Should not be changed'))
        Well formatted string: Should not be changed
        >>> print(_tag_cleanup('double  space  characters'))
        double space characters
        >>> print(_tag_cleanup('All\tthe\ndifferent\x0bwhitespace\x0cin\rone '
                               'go'))
        All the different whitespace in one go
        >>> print(_tag_cleanup(' Preceding whitespace'))
        Preceding whitespace
        >>> print(_tag_cleanup('Trailing whitespace '))
        Trailing whitespace
        >>> print(_tag_cleanup('  Preceding and trailing double whitespace  '))
        Preceding and trailing double whitespace
        >>> _tag_cleanup(unichr(CFG_WEBTAG_LAST_MYSQL_CHARACTER))
        u''
        >>> from string import whitespace
        >>> _tag_cleanup(whitespace)
        ''
    """
    if tag_name is None:
        return None

    # convert to string
    if type(tag_name) == unicode:
        tag_name = tag_name.encode('utf-8')

    # wash_for_xml
    tag_name = wash_for_xml(tag_name)

    # replacements
    tag_name = COMPILED_REPLACEMENTS_SILENT.apply(tag_name)

    return tag_name


def wash_tag_blocking(tag_name):
    """Apply list of replacements from CFG_WEBTAG_REPLACEMENTS_BLOCKING."""
    if tag_name is None:
        return None

    # replacements
    tag_name = COMPILED_REPLACEMENTS_BLOCKING.apply(tag_name)

    return tag_name


def wash_tag(tag_name):
    """Apply all washing procedures in order."""
    return wash_tag_blocking(wash_tag_silent(tag_name))
