# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

""" WebTag database models. """

# Configs
from invenio.webtag_config import \
    CFG_WEBTAG_LAST_MYSQL_CHARACTER

from invenio.webtag_config import \
    CFG_WEBTAG_NAME_MAX_LENGTH, \
    CFG_WEBTAG_ACCESS_NAMES, \
    CFG_WEBTAG_ACCESS_LEVELS, \
    CFG_WEBTAG_ACCESS_RIGHTS, \
    CFG_WEBTAG_ACCESS_OWNER_DEFAULT, \
    CFG_WEBTAG_NAME_REPLACEMENTS_SILENT, \
    CFG_WEBTAG_NAME_REPLACEMENTS_BLOCKING


# Database
from invenio.sqlalchemyutils import db
from sqlalchemy.ext.associationproxy import association_proxy

# Related models
from invenio.bibedit_model import Bibrec
from invenio.websession_model import User, Usergroup

# Functions
from invenio.textutils import wash_for_xml
from datetime import datetime, date
import re

class Serializable(object):
    """Class which can present its fields as dict for json serialization"""
    # Set of fields which are to be serialized
    __public__ = None

    def _serialize_field(self, value):
        """ Converts value of a field to format suitable for json """
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
        """Returns model's fields (__public__) or
           intersection(fields, __public__) for jsonify"""
        data = {}
        keys = self._sa_instance_state.attrs.items()

        public = set()
        if self.__public__:
            public = public.union(self.__public__)
        if fields:
            public = public.intersection(fields)

        for key, field in  keys:
            if key in public:
                value = self._serialize_field(field.value)
                if value:
                    data[key] = value

        return data

#
# TAG
#
class WtgTAG(db.Model, Serializable):
    """ Represents a Tag """
    __tablename__ = 'wtgTAG'
    __public__ = {'id', 'name', 'id_owner'}

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
                            default=CFG_WEBTAG_ACCESS_OWNER_DEFAULT)

    # Access rights of everyone
    public_access_rights = db.Column(db.Integer(2, unsigned=True),
                            nullable=False,
                            default=CFG_WEBTAG_ACCESS_LEVELS['Nothing'])

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

    # association proxy of "user_keywords" collection
    # to "keyword" attribute
    records = association_proxy('records_association', 'bibrec')

    #Calculated fields
    @db.hybrid_property
    def record_count(self):
        return self.records_association_query.count()

    @record_count.expression
    def record_count(cls):
        return db.select([db.func.count(WtgTAGRecord.id_bibrec)]).\
               where(WtgTAGRecord.id_tag==cls.id).\
               label('record_count')

    # Validation
    @db.validates('name')
    def validate_name(self, key, value):
        """
        Check if the tag is valid for insertion.
        Should be run after any cleanup, in case it was reduced to the empty string.

        @param value: Single tag.
        @return: Cleaned version of tag

        Examples:
        >>> validate_name('It is full of spaces')
        True
        >>> validate_name('')
        False
        >>> validate_name(None)
        False
        >>> validate_name('x' * TAG_MAX_LENGTH)
        True
        >>> validate_name('x' * (TAG_MAX_LENGTH + 1)) # Too long
        False
        >>> validate_name('α'.decode('utf-8') * TAG_MAX_LENGTH)
        True
        >>> validate_name('\\uFFFD' * TAG_MAX_LENGTH) # Last XML compatible character
        False
        >>> validate_name(unichr(CFG_WEBTAG_LAST_MYSQL_CHARACTER)) # Not XML compatible
        False
        >>> validate_name(unichr(CFG_WEBTAG_LAST_MYSQL_CHARACTER + 1)) # Outside range
        False
        """
        tag = wash_tag(value)

        # assert tag is not None
        # assert len(tag) > 0
        # assert len(tag) <= CFG_WEBTAG_NAME_MAX_LENGTH
        # assert max(ord(letter) for letter in tag) \
        #        <= CFG_WEBTAG_LAST_MYSQL_CHARACTER

        return tag

    @db.validates('user_access_rights')
    @db.validates('public_access_rights')
    def validate_user_access_rights(self, key, value):
        """ Check if the value is among defined levels """
        assert value in CFG_WEBTAG_ACCESS_NAMES
        return value

#
# TAG - RECORD
#
class WtgTAGRecord(db.Model, Serializable):
    """ Represents a connection between Tag and Record """

    __tablename__ = 'wtgTAG_bibrec'
    __public__ = {'id_tag', 'id_bibrec', 'date_added'}

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

    # Constructor
    def __init__(self, bibrec=None, **kwargs):
        super(WtgTAGRecord, self).__init__(**kwargs)

        self.bibrec = bibrec


#
# TAG - USERGROUP
#
class WtgTAGUsergroup(db.Model, Serializable):
    """ Represents access rights of the group concerning the tag """

    __tablename__ = 'wtgTAG_usergroup'
    __public__ = {'id_tag', 'id_usergroup', 'group_access_rights'}

    # tagTAG.id
    id_tag = db.Column(db.Integer(15, unsigned=True),
                       db.ForeignKey(WtgTAG.id),
                       nullable=False,
                       primary_key=True)

    # usergroup.id
    id_usergroup =  id_usergroup = db.Column(db.Integer(15, unsigned=True),
                    db.ForeignKey(Usergroup.id),
                    nullable=False, server_default='0',
                    primary_key=True)

    # Access rights
    group_access_rights = db.Column(db.Integer(2, unsigned=True),
                           nullable=False,
                           default=CFG_WEBTAG_ACCESS_LEVELS['View'])

    # Relationships
    tag = db.relationship(WtgTAG,
                          backref=db.backref('group_rights', cascade='all'))

    group = db.relationship(Usergroup,
                            backref=db.backref('tag_rights', cascade='all'))

    # Validation
    @db.validates('group_access_rights')
    def validate_user_access_rights(self, key, value):
        """ Check if the value is among defined levels """
        assert value in CFG_WEBTAG_ACCESS_NAMES
        return value


# Compiling once should improve regexp speed
COMPILED_REPLACEMENTS_SILENT = [(re.compile(exp), repl)
                                for (exp, repl)
                                in CFG_WEBTAG_NAME_REPLACEMENTS_SILENT]

COMPILED_REPLACEMENTS_BLOCKING = [(re.compile(exp), repl)
                                 for (exp, repl)
                                 in CFG_WEBTAG_NAME_REPLACEMENTS_BLOCKING]

def _apply_replacements(replacements, text):
    """ Applies a list of regular expression replacements
        to a string.
        @param replacements list of pairs (compiled_expression, replacement)
    """
    for (reg_exp, replacement) in replacements:
        text = re.sub(reg_exp, replacement, text)

    return text

def wash_tag_silent(tag_name):
    """
    Whitespace and character cleanup.

    @param tag_name: Single tag.
    @return: Tag Unicode string with all whitespace characters replaced with
    Unicode single space (' '), no whitespace at the start and end of the tags,
    no duplicate whitespace, and only characters valid in XML 1.0.
    Also applies list of replacements from CFG_WEBTAG_REPLACEMENTS_SILENT.

    Examples:
    >>> print(_tag_cleanup('Well formatted string: Should not be changed'))
    Well formatted string: Should not be changed
    >>> print(_tag_cleanup('double  space  characters'))
    double space characters
    >>> print(_tag_cleanup('All\\tthe\\ndifferent\\x0bwhitespace\\x0cin\\rone go'))
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
    tag_name = _apply_replacements(COMPILED_REPLACEMENTS_SILENT, tag_name)

    return tag_name

def wash_tag_blocking(tag_name):
    """ Applies list of replacements from CFG_WEBTAG_REPLACEMENTS_BLOCKING """

    if tag_name is None:
        return None

     # replacements
    tag_name = _apply_replacements(COMPILED_REPLACEMENTS_BLOCKING, tag_name)

    return tag_name

def wash_tag(tag_name):
    """ Applies all washing procedures in order """

    return wash_tag_blocking(wash_tag_silent(tag_name))
