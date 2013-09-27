
# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
BibEdit database models.
"""

# General imports.
from invenio.ext.sqlalchemy import db
from flask import current_app
from werkzeug import cached_property

# Create your models here.


class Bibrec(db.Model):
    """Represents a Bibrec record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec'
    id = db.Column(db.MediumInteger(8, unsigned=True), primary_key=True,
                nullable=False,
                autoincrement=True)
    creation_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00',
                index=True)
    modification_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00',
                index=True)
    master_format = db.Column(db.String(16), nullable=False,
                              server_default='marc')

    @property
    def deleted(self):
        """
           Return True if record is marked as deleted.
        """
        from invenio.search_engine_utils import get_fieldvalues
        # record exists; now check whether it isn't marked as deleted:
        dbcollids = get_fieldvalues(self.id, "980__%")

        return ("DELETED" in dbcollids) or \
               (current_app.config.get('CFG_CERN_SITE')
                and "DUMMY" in dbcollids)

    @staticmethod
    def _next_merged_recid(recid):
        """ Returns the ID of record merged with record with ID = recid """
        from invenio.search_engine_utils import get_fieldvalues
        merged_recid = None
        for val in get_fieldvalues(recid, "970__d"):
            try:
                merged_recid = int(val)
                break
            except ValueError:
                pass

        if not merged_recid:
            return None
        else:
            return merged_recid

    @cached_property
    def merged_recid(self):
        """ Return the record object with
        which the given record has been merged.
        @param recID: deleted record recID
        @type recID: int
        @return: merged record recID
        @rtype: int or None
        """
        return Bibrec._next_merged_recid(self.id)

    @property
    def merged_recid_final(self):
        """ Returns the last record from hierarchy of
            records merged with this one """

        cur_id = self.id
        next_id = Bibrec._next_merged_recid(cur_id)

        while next_id:
            cur_id = next_id
            next_id = Bibrec._next_merged_recid(cur_id)

        return cur_id

    @cached_property
    def is_restricted(self):
        """Returns True is record is restricted."""
        from invenio.search_engine import get_restricted_collections_for_recid

        if get_restricted_collections_for_recid(self.id,
                                                recreate_cache_if_needed=False):
            return True
        elif self.is_processed:
            return True
        return False

    @cached_property
    def is_processed(self):
        """Returns True is recods is processed (not in any collection)."""
        from invenio.search_engine import is_record_in_any_collection
        return not is_record_in_any_collection(self.id,
                                               recreate_cache_if_needed=False)


class BibHOLDINGPEN(db.Model):
    """Represents a BibHOLDINGPEN record."""
    def __init__(self):
        pass
    __tablename__ = 'bibHOLDINGPEN'
    changeset_id = db.Column(db.Integer(11), primary_key=True,
                autoincrement=True)
    changeset_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00', index=True)
    changeset_xml = db.Column(db.Text, nullable=False)
    oai_id = db.Column(db.String(40), nullable=False,
                server_default='')
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), nullable=False, server_default='0')
    bibrec = db.relationship(Bibrec, backref='holdingpen')

class Bibdoc(db.Model):
    """Represents a Bibdoc record."""
    __tablename__ = 'bibdoc'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                nullable=False, autoincrement=True)
    status = db.Column(db.Text, nullable=False)
    docname = db.Column(db.String(250), nullable=True,  # collation='utf8_bin'
                server_default='file', index=True)
    creation_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00', index=True)
    modification_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00', index=True)
    text_extraction_date = db.Column(db.DateTime, nullable=False,
                server_default='1900-01-01 00:00:00')
    doctype = db.Column(db.String(255))

class BibdocBibdoc(db.Model):
    """Represents a BibdocBibdoc record."""
    __tablename__ = 'bibdoc_bibdoc'
    id = db.Column(db.MediumInteger(9, unsigned=True), primary_key=True,
                nullable=False, autoincrement=True)
    id_bibdoc1 = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Bibdoc.id), nullable=True)
    version1 = db.Column(db.TinyInteger(4, unsigned=True))
    format1 = db.Column(db.String(50))
    id_bibdoc2 = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Bibdoc.id), nullable=True)
    version2 = db.Column(db.TinyInteger(4, unsigned=True))
    format2 = db.Column(db.String(50))
    rel_type = db.Column(db.String(255), nullable=True)
    bibdoc1 = db.relationship(Bibdoc, backref='bibdoc2s',
                primaryjoin=Bibdoc.id == id_bibdoc1)
    bibdoc2 = db.relationship(Bibdoc, backref='bibdoc1s',
                primaryjoin=Bibdoc.id == id_bibdoc2)

class BibrecBibdoc(db.Model):
    """Represents a BibrecBibdoc record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bibdoc'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), nullable=False,
                server_default='0', primary_key=True)
    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Bibdoc.id), nullable=False,
                server_default='0', primary_key=True)
    docname = db.Column(db.String(250), nullable=False,  # collation='utf8_bin'
                server_default='file', index=True)
    type = db.Column(db.String(255), nullable=True)
    bibrec = db.relationship(Bibrec, backref='bibdocs')
    bibdoc = db.relationship(Bibdoc, backref='bibrecs')

class HstDOCUMENT(db.Model):
    """Represents a HstDOCUMENT record."""
    def __init__(self):
        pass
    __tablename__ = 'hstDOCUMENT'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                nullable=False, autoincrement=True)
    id_bibdoc = db.Column(db.MediumInteger(9, unsigned=True),
                db.ForeignKey(Bibdoc.id), primary_key=True, nullable=False,
                autoincrement=False)
    docname = db.Column(db.String(250), nullable=False, index=True)
    docformat = db.Column(db.String(50), nullable=False, index=True)
    docversion = db.Column(db.TinyInteger(4, unsigned=True),
                nullable=False)
    docsize = db.Column(db.BigInteger(15, unsigned=True),
                nullable=False)
    docchecksum = db.Column(db.Char(32), nullable=False)
    doctimestamp = db.Column(db.DateTime, nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    job_id = db.Column(db.MediumInteger(15, unsigned=True),
                nullable=True, index=True)
    job_name = db.Column(db.String(255), nullable=True, index=True)
    job_person = db.Column(db.String(255), nullable=True, index=True)
    job_date = db.Column(db.DateTime, nullable=True, index=True)
    job_details = db.Column(db.iBinary, nullable=True)

class HstRECORD(db.Model):
    """Represents a HstRECORD record."""
    def __init__(self):
        pass
    __tablename__ = 'hstRECORD'
    id = db.Column(db.Integer(15, unsigned=True), primary_key=True,
                nullable=False, autoincrement=True)
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id), autoincrement=False,
                nullable=False, primary_key=True)
    marcxml = db.Column(db.iBinary, nullable=False)
    job_id = db.Column(db.MediumInteger(15, unsigned=True),
                nullable=False, index=True)
    job_name = db.Column(db.String(255), nullable=False, index=True)
    job_person = db.Column(db.String(255), nullable=False, index=True)
    job_date = db.Column(db.DateTime, nullable=False, index=True)
    job_details = db.Column(db.iBinary, nullable=False)
    affected_fields = db.Column(db.Text(), nullable=False,
                                server_default='')


# GENERATED

class Bib00x(db.Model):
    """Represents a Bib00x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib00x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib00x(db.Model):
    """Represents a BibrecBib00x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib00x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib00x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib00xs')
    bibxxx = db.relationship(Bib00x, backref='bibrecs')

class Bib01x(db.Model):
    """Represents a Bib01x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib01x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib01x(db.Model):
    """Represents a BibrecBib01x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib01x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib01x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib01xs')
    bibxxx = db.relationship(Bib01x, backref='bibrecs')

class Bib02x(db.Model):
    """Represents a Bib02x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib02x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib02x(db.Model):
    """Represents a BibrecBib02x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib02x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib02x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib02xs')
    bibxxx = db.relationship(Bib02x, backref='bibrecs')

class Bib03x(db.Model):
    """Represents a Bib03x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib03x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib03x(db.Model):
    """Represents a BibrecBib03x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib03x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib03x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib03xs')
    bibxxx = db.relationship(Bib03x, backref='bibrecs')

class Bib04x(db.Model):
    """Represents a Bib04x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib04x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib04x(db.Model):
    """Represents a BibrecBib04x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib04x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib04x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib04xs')
    bibxxx = db.relationship(Bib04x, backref='bibrecs')

class Bib05x(db.Model):
    """Represents a Bib05x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib05x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib05x(db.Model):
    """Represents a BibrecBib05x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib05x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib05x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib05xs')
    bibxxx = db.relationship(Bib05x, backref='bibrecs')

class Bib06x(db.Model):
    """Represents a Bib06x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib06x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib06x(db.Model):
    """Represents a BibrecBib06x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib06x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib06x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib06xs')
    bibxxx = db.relationship(Bib06x, backref='bibrecs')

class Bib07x(db.Model):
    """Represents a Bib07x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib07x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib07x(db.Model):
    """Represents a BibrecBib07x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib07x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib07x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib07xs')
    bibxxx = db.relationship(Bib07x, backref='bibrecs')

class Bib08x(db.Model):
    """Represents a Bib08x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib08x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib08x(db.Model):
    """Represents a BibrecBib08x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib08x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib08x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib08xs')
    bibxxx = db.relationship(Bib08x, backref='bibrecs')

class Bib09x(db.Model):
    """Represents a Bib09x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib09x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib09x(db.Model):
    """Represents a BibrecBib09x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib09x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib09x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib09xs')
    bibxxx = db.relationship(Bib09x, backref='bibrecs')

class Bib10x(db.Model):
    """Represents a Bib10x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib10x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib10x(db.Model):
    """Represents a BibrecBib10x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib10x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib10x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib10xs')
    bibxxx = db.relationship(Bib10x, backref='bibrecs')

class Bib11x(db.Model):
    """Represents a Bib11x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib11x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib11x(db.Model):
    """Represents a BibrecBib11x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib11x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib11x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib11xs')
    bibxxx = db.relationship(Bib11x, backref='bibrecs')

class Bib12x(db.Model):
    """Represents a Bib12x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib12x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib12x(db.Model):
    """Represents a BibrecBib12x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib12x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib12x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib12xs')
    bibxxx = db.relationship(Bib12x, backref='bibrecs')

class Bib13x(db.Model):
    """Represents a Bib13x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib13x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib13x(db.Model):
    """Represents a BibrecBib13x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib13x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib13x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib13xs')
    bibxxx = db.relationship(Bib13x, backref='bibrecs')

class Bib14x(db.Model):
    """Represents a Bib14x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib14x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib14x(db.Model):
    """Represents a BibrecBib14x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib14x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib14x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib14xs')
    bibxxx = db.relationship(Bib14x, backref='bibrecs')

class Bib15x(db.Model):
    """Represents a Bib15x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib15x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib15x(db.Model):
    """Represents a BibrecBib15x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib15x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib15x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib15xs')
    bibxxx = db.relationship(Bib15x, backref='bibrecs')

class Bib16x(db.Model):
    """Represents a Bib16x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib16x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib16x(db.Model):
    """Represents a BibrecBib16x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib16x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib16x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib16xs')
    bibxxx = db.relationship(Bib16x, backref='bibrecs')

class Bib17x(db.Model):
    """Represents a Bib17x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib17x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib17x(db.Model):
    """Represents a BibrecBib17x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib17x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib17x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib17xs')
    bibxxx = db.relationship(Bib17x, backref='bibrecs')

class Bib18x(db.Model):
    """Represents a Bib18x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib18x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib18x(db.Model):
    """Represents a BibrecBib18x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib18x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib18x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib18xs')
    bibxxx = db.relationship(Bib18x, backref='bibrecs')

class Bib19x(db.Model):
    """Represents a Bib19x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib19x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib19x(db.Model):
    """Represents a BibrecBib19x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib19x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib19x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib19xs')
    bibxxx = db.relationship(Bib19x, backref='bibrecs')

class Bib20x(db.Model):
    """Represents a Bib20x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib20x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib20x(db.Model):
    """Represents a BibrecBib20x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib20x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib20x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib20xs')
    bibxxx = db.relationship(Bib20x, backref='bibrecs')

class Bib21x(db.Model):
    """Represents a Bib21x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib21x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib21x(db.Model):
    """Represents a BibrecBib21x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib21x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib21x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib21xs')
    bibxxx = db.relationship(Bib21x, backref='bibrecs')

class Bib22x(db.Model):
    """Represents a Bib22x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib22x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib22x(db.Model):
    """Represents a BibrecBib22x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib22x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib22x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib22xs')
    bibxxx = db.relationship(Bib22x, backref='bibrecs')

class Bib23x(db.Model):
    """Represents a Bib23x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib23x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib23x(db.Model):
    """Represents a BibrecBib23x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib23x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib23x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib23xs')
    bibxxx = db.relationship(Bib23x, backref='bibrecs')

class Bib24x(db.Model):
    """Represents a Bib24x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib24x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib24x(db.Model):
    """Represents a BibrecBib24x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib24x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib24x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib24xs')
    bibxxx = db.relationship(Bib24x, backref='bibrecs')

class Bib25x(db.Model):
    """Represents a Bib25x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib25x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib25x(db.Model):
    """Represents a BibrecBib25x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib25x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib25x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib25xs')
    bibxxx = db.relationship(Bib25x, backref='bibrecs')

class Bib26x(db.Model):
    """Represents a Bib26x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib26x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib26x(db.Model):
    """Represents a BibrecBib26x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib26x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib26x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib26xs')
    bibxxx = db.relationship(Bib26x, backref='bibrecs')

class Bib27x(db.Model):
    """Represents a Bib27x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib27x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib27x(db.Model):
    """Represents a BibrecBib27x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib27x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib27x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib27xs')
    bibxxx = db.relationship(Bib27x, backref='bibrecs')

class Bib28x(db.Model):
    """Represents a Bib28x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib28x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib28x(db.Model):
    """Represents a BibrecBib28x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib28x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib28x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib28xs')
    bibxxx = db.relationship(Bib28x, backref='bibrecs')

class Bib29x(db.Model):
    """Represents a Bib29x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib29x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib29x(db.Model):
    """Represents a BibrecBib29x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib29x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib29x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib29xs')
    bibxxx = db.relationship(Bib29x, backref='bibrecs')

class Bib30x(db.Model):
    """Represents a Bib30x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib30x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib30x(db.Model):
    """Represents a BibrecBib30x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib30x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib30x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib30xs')
    bibxxx = db.relationship(Bib30x, backref='bibrecs')

class Bib31x(db.Model):
    """Represents a Bib31x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib31x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib31x(db.Model):
    """Represents a BibrecBib31x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib31x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib31x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib31xs')
    bibxxx = db.relationship(Bib31x, backref='bibrecs')

class Bib32x(db.Model):
    """Represents a Bib32x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib32x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib32x(db.Model):
    """Represents a BibrecBib32x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib32x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib32x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib32xs')
    bibxxx = db.relationship(Bib32x, backref='bibrecs')

class Bib33x(db.Model):
    """Represents a Bib33x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib33x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib33x(db.Model):
    """Represents a BibrecBib33x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib33x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib33x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib33xs')
    bibxxx = db.relationship(Bib33x, backref='bibrecs')

class Bib34x(db.Model):
    """Represents a Bib34x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib34x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib34x(db.Model):
    """Represents a BibrecBib34x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib34x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib34x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib34xs')
    bibxxx = db.relationship(Bib34x, backref='bibrecs')

class Bib35x(db.Model):
    """Represents a Bib35x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib35x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib35x(db.Model):
    """Represents a BibrecBib35x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib35x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib35x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib35xs')
    bibxxx = db.relationship(Bib35x, backref='bibrecs')

class Bib36x(db.Model):
    """Represents a Bib36x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib36x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib36x(db.Model):
    """Represents a BibrecBib36x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib36x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib36x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib36xs')
    bibxxx = db.relationship(Bib36x, backref='bibrecs')

class Bib37x(db.Model):
    """Represents a Bib37x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib37x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib37x(db.Model):
    """Represents a BibrecBib37x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib37x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib37x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib37xs')
    bibxxx = db.relationship(Bib37x, backref='bibrecs')

class Bib38x(db.Model):
    """Represents a Bib38x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib38x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib38x(db.Model):
    """Represents a BibrecBib38x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib38x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib38x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib38xs')
    bibxxx = db.relationship(Bib38x, backref='bibrecs')

class Bib39x(db.Model):
    """Represents a Bib39x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib39x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib39x(db.Model):
    """Represents a BibrecBib39x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib39x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib39x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib39xs')
    bibxxx = db.relationship(Bib39x, backref='bibrecs')

class Bib40x(db.Model):
    """Represents a Bib40x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib40x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib40x(db.Model):
    """Represents a BibrecBib40x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib40x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib40x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib40xs')
    bibxxx = db.relationship(Bib40x, backref='bibrecs')

class Bib41x(db.Model):
    """Represents a Bib41x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib41x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib41x(db.Model):
    """Represents a BibrecBib41x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib41x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib41x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib41xs')
    bibxxx = db.relationship(Bib41x, backref='bibrecs')

class Bib42x(db.Model):
    """Represents a Bib42x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib42x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib42x(db.Model):
    """Represents a BibrecBib42x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib42x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib42x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib42xs')
    bibxxx = db.relationship(Bib42x, backref='bibrecs')

class Bib43x(db.Model):
    """Represents a Bib43x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib43x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib43x(db.Model):
    """Represents a BibrecBib43x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib43x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib43x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib43xs')
    bibxxx = db.relationship(Bib43x, backref='bibrecs')

class Bib44x(db.Model):
    """Represents a Bib44x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib44x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib44x(db.Model):
    """Represents a BibrecBib44x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib44x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib44x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib44xs')
    bibxxx = db.relationship(Bib44x, backref='bibrecs')

class Bib45x(db.Model):
    """Represents a Bib45x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib45x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib45x(db.Model):
    """Represents a BibrecBib45x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib45x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib45x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib45xs')
    bibxxx = db.relationship(Bib45x, backref='bibrecs')

class Bib46x(db.Model):
    """Represents a Bib46x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib46x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib46x(db.Model):
    """Represents a BibrecBib46x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib46x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib46x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib46xs')
    bibxxx = db.relationship(Bib46x, backref='bibrecs')

class Bib47x(db.Model):
    """Represents a Bib47x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib47x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib47x(db.Model):
    """Represents a BibrecBib47x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib47x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib47x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib47xs')
    bibxxx = db.relationship(Bib47x, backref='bibrecs')

class Bib48x(db.Model):
    """Represents a Bib48x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib48x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib48x(db.Model):
    """Represents a BibrecBib48x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib48x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib48x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib48xs')
    bibxxx = db.relationship(Bib48x, backref='bibrecs')

class Bib49x(db.Model):
    """Represents a Bib49x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib49x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib49x(db.Model):
    """Represents a BibrecBib49x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib49x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib49x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib49xs')
    bibxxx = db.relationship(Bib49x, backref='bibrecs')

class Bib50x(db.Model):
    """Represents a Bib50x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib50x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib50x(db.Model):
    """Represents a BibrecBib50x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib50x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib50x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib50xs')
    bibxxx = db.relationship(Bib50x, backref='bibrecs')

class Bib51x(db.Model):
    """Represents a Bib51x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib51x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib51x(db.Model):
    """Represents a BibrecBib51x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib51x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib51x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib51xs')
    bibxxx = db.relationship(Bib51x, backref='bibrecs')

class Bib52x(db.Model):
    """Represents a Bib52x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib52x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib52x(db.Model):
    """Represents a BibrecBib52x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib52x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib52x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib52xs')
    bibxxx = db.relationship(Bib52x, backref='bibrecs')

class Bib53x(db.Model):
    """Represents a Bib53x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib53x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib53x(db.Model):
    """Represents a BibrecBib53x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib53x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib53x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib53xs')
    bibxxx = db.relationship(Bib53x, backref='bibrecs')

class Bib54x(db.Model):
    """Represents a Bib54x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib54x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib54x(db.Model):
    """Represents a BibrecBib54x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib54x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib54x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib54xs')
    bibxxx = db.relationship(Bib54x, backref='bibrecs')

class Bib55x(db.Model):
    """Represents a Bib55x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib55x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib55x(db.Model):
    """Represents a BibrecBib55x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib55x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib55x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib55xs')
    bibxxx = db.relationship(Bib55x, backref='bibrecs')

class Bib56x(db.Model):
    """Represents a Bib56x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib56x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib56x(db.Model):
    """Represents a BibrecBib56x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib56x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib56x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib56xs')
    bibxxx = db.relationship(Bib56x, backref='bibrecs')

class Bib57x(db.Model):
    """Represents a Bib57x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib57x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib57x(db.Model):
    """Represents a BibrecBib57x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib57x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib57x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib57xs')
    bibxxx = db.relationship(Bib57x, backref='bibrecs')

class Bib58x(db.Model):
    """Represents a Bib58x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib58x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib58x(db.Model):
    """Represents a BibrecBib58x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib58x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib58x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib58xs')
    bibxxx = db.relationship(Bib58x, backref='bibrecs')

class Bib59x(db.Model):
    """Represents a Bib59x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib59x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib59x(db.Model):
    """Represents a BibrecBib59x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib59x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib59x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib59xs')
    bibxxx = db.relationship(Bib59x, backref='bibrecs')

class Bib60x(db.Model):
    """Represents a Bib60x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib60x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib60x(db.Model):
    """Represents a BibrecBib60x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib60x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib60x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib60xs')
    bibxxx = db.relationship(Bib60x, backref='bibrecs')

class Bib61x(db.Model):
    """Represents a Bib61x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib61x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib61x(db.Model):
    """Represents a BibrecBib61x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib61x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib61x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib61xs')
    bibxxx = db.relationship(Bib61x, backref='bibrecs')

class Bib62x(db.Model):
    """Represents a Bib62x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib62x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib62x(db.Model):
    """Represents a BibrecBib62x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib62x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib62x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib62xs')
    bibxxx = db.relationship(Bib62x, backref='bibrecs')

class Bib63x(db.Model):
    """Represents a Bib63x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib63x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib63x(db.Model):
    """Represents a BibrecBib63x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib63x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib63x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib63xs')
    bibxxx = db.relationship(Bib63x, backref='bibrecs')

class Bib64x(db.Model):
    """Represents a Bib64x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib64x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib64x(db.Model):
    """Represents a BibrecBib64x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib64x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib64x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib64xs')
    bibxxx = db.relationship(Bib64x, backref='bibrecs')

class Bib65x(db.Model):
    """Represents a Bib65x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib65x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib65x(db.Model):
    """Represents a BibrecBib65x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib65x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib65x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib65xs')
    bibxxx = db.relationship(Bib65x, backref='bibrecs')

class Bib66x(db.Model):
    """Represents a Bib66x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib66x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib66x(db.Model):
    """Represents a BibrecBib66x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib66x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib66x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib66xs')
    bibxxx = db.relationship(Bib66x, backref='bibrecs')

class Bib67x(db.Model):
    """Represents a Bib67x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib67x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib67x(db.Model):
    """Represents a BibrecBib67x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib67x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib67x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib67xs')
    bibxxx = db.relationship(Bib67x, backref='bibrecs')

class Bib68x(db.Model):
    """Represents a Bib68x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib68x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib68x(db.Model):
    """Represents a BibrecBib68x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib68x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib68x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib68xs')
    bibxxx = db.relationship(Bib68x, backref='bibrecs')

class Bib69x(db.Model):
    """Represents a Bib69x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib69x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib69x(db.Model):
    """Represents a BibrecBib69x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib69x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib69x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib69xs')
    bibxxx = db.relationship(Bib69x, backref='bibrecs')

class Bib70x(db.Model):
    """Represents a Bib70x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib70x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib70x(db.Model):
    """Represents a BibrecBib70x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib70x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib70x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib70xs')
    bibxxx = db.relationship(Bib70x, backref='bibrecs')

class Bib71x(db.Model):
    """Represents a Bib71x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib71x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib71x(db.Model):
    """Represents a BibrecBib71x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib71x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib71x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib71xs')
    bibxxx = db.relationship(Bib71x, backref='bibrecs')

class Bib72x(db.Model):
    """Represents a Bib72x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib72x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib72x(db.Model):
    """Represents a BibrecBib72x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib72x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib72x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib72xs')
    bibxxx = db.relationship(Bib72x, backref='bibrecs')

class Bib73x(db.Model):
    """Represents a Bib73x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib73x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib73x(db.Model):
    """Represents a BibrecBib73x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib73x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib73x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib73xs')
    bibxxx = db.relationship(Bib73x, backref='bibrecs')

class Bib74x(db.Model):
    """Represents a Bib74x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib74x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib74x(db.Model):
    """Represents a BibrecBib74x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib74x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib74x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib74xs')
    bibxxx = db.relationship(Bib74x, backref='bibrecs')

class Bib75x(db.Model):
    """Represents a Bib75x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib75x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib75x(db.Model):
    """Represents a BibrecBib75x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib75x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib75x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib75xs')
    bibxxx = db.relationship(Bib75x, backref='bibrecs')

class Bib76x(db.Model):
    """Represents a Bib76x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib76x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib76x(db.Model):
    """Represents a BibrecBib76x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib76x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib76x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib76xs')
    bibxxx = db.relationship(Bib76x, backref='bibrecs')

class Bib77x(db.Model):
    """Represents a Bib77x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib77x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib77x(db.Model):
    """Represents a BibrecBib77x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib77x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib77x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib77xs')
    bibxxx = db.relationship(Bib77x, backref='bibrecs')

class Bib78x(db.Model):
    """Represents a Bib78x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib78x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib78x(db.Model):
    """Represents a BibrecBib78x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib78x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib78x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib78xs')
    bibxxx = db.relationship(Bib78x, backref='bibrecs')

class Bib79x(db.Model):
    """Represents a Bib79x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib79x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib79x(db.Model):
    """Represents a BibrecBib79x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib79x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib79x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib79xs')
    bibxxx = db.relationship(Bib79x, backref='bibrecs')

class Bib80x(db.Model):
    """Represents a Bib80x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib80x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib80x(db.Model):
    """Represents a BibrecBib80x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib80x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib80x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib80xs')
    bibxxx = db.relationship(Bib80x, backref='bibrecs')

class Bib81x(db.Model):
    """Represents a Bib81x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib81x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib81x(db.Model):
    """Represents a BibrecBib81x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib81x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib81x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib81xs')
    bibxxx = db.relationship(Bib81x, backref='bibrecs')

class Bib82x(db.Model):
    """Represents a Bib82x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib82x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib82x(db.Model):
    """Represents a BibrecBib82x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib82x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib82x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib82xs')
    bibxxx = db.relationship(Bib82x, backref='bibrecs')

class Bib83x(db.Model):
    """Represents a Bib83x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib83x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib83x(db.Model):
    """Represents a BibrecBib83x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib83x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib83x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib83xs')
    bibxxx = db.relationship(Bib83x, backref='bibrecs')

class Bib84x(db.Model):
    """Represents a Bib84x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib84x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib84x(db.Model):
    """Represents a BibrecBib84x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib84x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib84x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib84xs')
    bibxxx = db.relationship(Bib84x, backref='bibrecs')

class Bib85x(db.Model):
    """Represents a Bib85x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib85x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib85x(db.Model):
    """Represents a BibrecBib85x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib85x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib85x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib85xs')
    bibxxx = db.relationship(Bib85x, backref='bibrecs')

class Bib86x(db.Model):
    """Represents a Bib86x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib86x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib86x(db.Model):
    """Represents a BibrecBib86x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib86x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib86x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib86xs')
    bibxxx = db.relationship(Bib86x, backref='bibrecs')

class Bib87x(db.Model):
    """Represents a Bib87x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib87x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib87x(db.Model):
    """Represents a BibrecBib87x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib87x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib87x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib87xs')
    bibxxx = db.relationship(Bib87x, backref='bibrecs')

class Bib88x(db.Model):
    """Represents a Bib88x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib88x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib88x(db.Model):
    """Represents a BibrecBib88x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib88x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib88x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib88xs')
    bibxxx = db.relationship(Bib88x, backref='bibrecs')

class Bib89x(db.Model):
    """Represents a Bib89x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib89x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib89x(db.Model):
    """Represents a BibrecBib89x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib89x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib89x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib89xs')
    bibxxx = db.relationship(Bib89x, backref='bibrecs')

class Bib90x(db.Model):
    """Represents a Bib90x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib90x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib90x(db.Model):
    """Represents a BibrecBib90x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib90x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib90x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib90xs')
    bibxxx = db.relationship(Bib90x, backref='bibrecs')

class Bib91x(db.Model):
    """Represents a Bib91x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib91x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib91x(db.Model):
    """Represents a BibrecBib91x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib91x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib91x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib91xs')
    bibxxx = db.relationship(Bib91x, backref='bibrecs')

class Bib92x(db.Model):
    """Represents a Bib92x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib92x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib92x(db.Model):
    """Represents a BibrecBib92x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib92x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib92x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib92xs')
    bibxxx = db.relationship(Bib92x, backref='bibrecs')

class Bib93x(db.Model):
    """Represents a Bib93x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib93x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib93x(db.Model):
    """Represents a BibrecBib93x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib93x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib93x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib93xs')
    bibxxx = db.relationship(Bib93x, backref='bibrecs')

class Bib94x(db.Model):
    """Represents a Bib94x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib94x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib94x(db.Model):
    """Represents a BibrecBib94x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib94x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib94x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib94xs')
    bibxxx = db.relationship(Bib94x, backref='bibrecs')

class Bib95x(db.Model):
    """Represents a Bib95x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib95x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib95x(db.Model):
    """Represents a BibrecBib95x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib95x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib95x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib95xs')
    bibxxx = db.relationship(Bib95x, backref='bibrecs')

class Bib96x(db.Model):
    """Represents a Bib96x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib96x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib96x(db.Model):
    """Represents a BibrecBib96x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib96x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib96x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib96xs')
    bibxxx = db.relationship(Bib96x, backref='bibrecs')

class Bib97x(db.Model):
    """Represents a Bib97x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib97x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib97x(db.Model):
    """Represents a BibrecBib97x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib97x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib97x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib97xs')
    bibxxx = db.relationship(Bib97x, backref='bibrecs')

class Bib98x(db.Model):
    """Represents a Bib98x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib98x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib98x(db.Model):
    """Represents a BibrecBib98x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib98x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib98x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib98xs')
    bibxxx = db.relationship(Bib98x, backref='bibrecs')

class Bib99x(db.Model):
    """Represents a Bib99x record."""
    def __init__(self):
        pass
    __tablename__ = 'bib99x'
    id = db.Column(db.MediumInteger(8, unsigned=True),
                primary_key=True,
                autoincrement=True)
    tag = db.Column(db.String(6), nullable=False, index=True,
                server_default='')
    value = db.Column(db.Text(35), nullable=False,
                index=True)

class BibrecBib99x(db.Model):
    """Represents a BibrecBib99x record."""
    def __init__(self):
        pass
    __tablename__ = 'bibrec_bib99x'
    id_bibrec = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bibrec.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    id_bibxxx = db.Column(db.MediumInteger(8, unsigned=True),
                db.ForeignKey(Bib99x.id),
        nullable=False, primary_key=True, index=True,
                server_default='0')
    field_number = db.Column(db.SmallInteger(5, unsigned=True),
                primary_key=True)
    bibrec = db.relationship(Bibrec, backref='bib99xs')
    bibxxx = db.relationship(Bib99x, backref='bibrecs')


__all__ = ['Bibrec',
           'Bibfmt',
           'BibHOLDINGPEN',
           'Bibdoc',
           'BibdocBibdoc',
           'BibrecBibdoc',
           'HstDOCUMENT',
           'HstRECORD',
           'Bib00x',
           'BibrecBib00x',
           'Bib01x',
           'BibrecBib01x',
           'Bib02x',
           'BibrecBib02x',
           'Bib03x',
           'BibrecBib03x',
           'Bib04x',
           'BibrecBib04x',
           'Bib05x',
           'BibrecBib05x',
           'Bib06x',
           'BibrecBib06x',
           'Bib07x',
           'BibrecBib07x',
           'Bib08x',
           'BibrecBib08x',
           'Bib09x',
           'BibrecBib09x',
           'Bib10x',
           'BibrecBib10x',
           'Bib11x',
           'BibrecBib11x',
           'Bib12x',
           'BibrecBib12x',
           'Bib13x',
           'BibrecBib13x',
           'Bib14x',
           'BibrecBib14x',
           'Bib15x',
           'BibrecBib15x',
           'Bib16x',
           'BibrecBib16x',
           'Bib17x',
           'BibrecBib17x',
           'Bib18x',
           'BibrecBib18x',
           'Bib19x',
           'BibrecBib19x',
           'Bib20x',
           'BibrecBib20x',
           'Bib21x',
           'BibrecBib21x',
           'Bib22x',
           'BibrecBib22x',
           'Bib23x',
           'BibrecBib23x',
           'Bib24x',
           'BibrecBib24x',
           'Bib25x',
           'BibrecBib25x',
           'Bib26x',
           'BibrecBib26x',
           'Bib27x',
           'BibrecBib27x',
           'Bib28x',
           'BibrecBib28x',
           'Bib29x',
           'BibrecBib29x',
           'Bib30x',
           'BibrecBib30x',
           'Bib31x',
           'BibrecBib31x',
           'Bib32x',
           'BibrecBib32x',
           'Bib33x',
           'BibrecBib33x',
           'Bib34x',
           'BibrecBib34x',
           'Bib35x',
           'BibrecBib35x',
           'Bib36x',
           'BibrecBib36x',
           'Bib37x',
           'BibrecBib37x',
           'Bib38x',
           'BibrecBib38x',
           'Bib39x',
           'BibrecBib39x',
           'Bib40x',
           'BibrecBib40x',
           'Bib41x',
           'BibrecBib41x',
           'Bib42x',
           'BibrecBib42x',
           'Bib43x',
           'BibrecBib43x',
           'Bib44x',
           'BibrecBib44x',
           'Bib45x',
           'BibrecBib45x',
           'Bib46x',
           'BibrecBib46x',
           'Bib47x',
           'BibrecBib47x',
           'Bib48x',
           'BibrecBib48x',
           'Bib49x',
           'BibrecBib49x',
           'Bib50x',
           'BibrecBib50x',
           'Bib51x',
           'BibrecBib51x',
           'Bib52x',
           'BibrecBib52x',
           'Bib53x',
           'BibrecBib53x',
           'Bib54x',
           'BibrecBib54x',
           'Bib55x',
           'BibrecBib55x',
           'Bib56x',
           'BibrecBib56x',
           'Bib57x',
           'BibrecBib57x',
           'Bib58x',
           'BibrecBib58x',
           'Bib59x',
           'BibrecBib59x',
           'Bib60x',
           'BibrecBib60x',
           'Bib61x',
           'BibrecBib61x',
           'Bib62x',
           'BibrecBib62x',
           'Bib63x',
           'BibrecBib63x',
           'Bib64x',
           'BibrecBib64x',
           'Bib65x',
           'BibrecBib65x',
           'Bib66x',
           'BibrecBib66x',
           'Bib67x',
           'BibrecBib67x',
           'Bib68x',
           'BibrecBib68x',
           'Bib69x',
           'BibrecBib69x',
           'Bib70x',
           'BibrecBib70x',
           'Bib71x',
           'BibrecBib71x',
           'Bib72x',
           'BibrecBib72x',
           'Bib73x',
           'BibrecBib73x',
           'Bib74x',
           'BibrecBib74x',
           'Bib75x',
           'BibrecBib75x',
           'Bib76x',
           'BibrecBib76x',
           'Bib77x',
           'BibrecBib77x',
           'Bib78x',
           'BibrecBib78x',
           'Bib79x',
           'BibrecBib79x',
           'Bib80x',
           'BibrecBib80x',
           'Bib81x',
           'BibrecBib81x',
           'Bib82x',
           'BibrecBib82x',
           'Bib83x',
           'BibrecBib83x',
           'Bib84x',
           'BibrecBib84x',
           'Bib85x',
           'BibrecBib85x',
           'Bib86x',
           'BibrecBib86x',
           'Bib87x',
           'BibrecBib87x',
           'Bib88x',
           'BibrecBib88x',
           'Bib89x',
           'BibrecBib89x',
           'Bib90x',
           'BibrecBib90x',
           'Bib91x',
           'BibrecBib91x',
           'Bib92x',
           'BibrecBib92x',
           'Bib93x',
           'BibrecBib93x',
           'Bib94x',
           'BibrecBib94x',
           'Bib95x',
           'BibrecBib95x',
           'Bib96x',
           'BibrecBib96x',
           'Bib97x',
           'BibrecBib97x',
           'Bib98x',
           'BibrecBib98x',
           'Bib99x',
           'BibrecBib99x']
