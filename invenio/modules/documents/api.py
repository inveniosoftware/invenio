# -*- coding: utf-8 -*-
##
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

import fs
import six

from fs.opener import opener

from invenio.modules.jsonalchemy.wrappers import SmartJson
from invenio.modules.jsonalchemy.jsonext.engines.sqlalchemy import SQLAlchemyStorage
from invenio.modules.jsonalchemy.reader import Reader


from . import signals, errors
from .models import Document as DocumentModel


class Document(SmartJson):
    """
    Document
    """
    storage_engine = SQLAlchemyStorage(DocumentModel)

    @classmethod
    def create(cls, data, model='document_base', master_format='json',
               **kwargs):
        document = Reader.translate(data, cls, master_format=master_format,
                                    model=model, namespace='documentext',
                                    **kwargs)
        cls.storage_engine.save_one(document.dumps())
        signals.document_created.connect(document)
        return document

    @classmethod
    def get_document(cls, uuid, include_deleted=False):
        """
        Returns document instance identified by UUID.

        :returns: a :class:`Document` instance.
        """
        try:
            document = cls(cls.storage_engine.get_one(uuid))
        except:
            raise errors.DocumentNotFound

        if not include_deleted and document['deleted']:
            raise errors.DeletedDocument
        return document

    def _save(self):
        self.storage_engine.update_one(self.dumps(), id=self['_id'])

    def setcontents(self, source, name=None, chunk_size=65536):
        """
        A convenience method to create a new file from a string or file-like
        object.

        NOTE: All paths has to be absolute or specified in full URI format.

        :param data: .
        :param name: File URI or filename generator taking `self` as argument.
        """

        if isinstance(source, six.text_type):
            self['source'] = source
            f = opener.open(source, 'rb')
        else:
            f = source

        if name is None:
            name = fs.path.basename(source)

        if callable(name):
            name = name(self)
        else:
            name = fs.path.abspath(name)

        signals.document_before_content_set.connect(self, name)

        data = f.read()
        _fs, filename = opener.parse(name)
        _fs.setcontents(filename, data, chunk_size)
        _fs.close()

        signals.document_after_content_set.connect(self, name)

        try:
            f.close()
        except:
            pass

        self['uri'] = name
        self._save()

    def open(self, mode='r', **kwargs):
        """Open a the 'uri' as a file-like object."""
        _fs, filename = opener.parse(self['uri'])
        return _fs.open(filename, mode=mode, **kwargs)

    def delete(self, force=False):
        """
        Deletes the document.

        :param force: If it is True than the document is deleted including
            attached files and metadata.
        """

        self['deleted'] = True

        if force:
            signals.document_before_file_delete.connect(self)
            fs, filename = opener.parse(self['uri'])
            fs.remove(filename)
            self['uri'] = None

        self._save()
