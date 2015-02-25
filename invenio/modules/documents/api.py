# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""
    invenio.modules.documents.api
    -----------------------------

    Documents API

    Following example shows how to handle documents metadata::

        >>> from flask import g
        >>> from invenio.base.factory import create_app
        >>> app = create_app()
        >>> ctx = app.test_request_context()
        >>> ctx.push()
        >>> from invenio.modules.documents import api
        >>> from invenio.modules.jsonalchemy.jsonext.engines import memory
        >>> app.config['DOCUMENTS_ENGINE'] = \
        "invenio.modules.jsonalchemy.jsonext.engines.memory:MemoryStorage"
        >>> d = api.Document.create({'title': 'Title 1'})
        >>> d['title']
        'Title 1'
        >>> d['creator']
        0
        >>> d['title'] = 'New Title 1'
        >>> d = d.update()
        >>> api.Document.get_document(d['_id'])['title']
        'New Title 1'
        >>> ctx.pop()
"""

import fs
import six

from datetime import datetime
from fs.opener import opener

from invenio.modules.jsonalchemy.wrappers import SmartJson
from invenio.modules.jsonalchemy.reader import Reader

from . import signals, errors


class Document(SmartJson):
    """Document"""

    __storagename__ = 'documents'

    @classmethod
    def create(cls, data, model='document_base', master_format='json',
               **kwargs):
        document = Reader.translate(data, cls, master_format=master_format,
                                    model=model, namespace='documentext',
                                    **kwargs)
        cls.storage_engine.save_one(document.dumps())
        signals.document_created.send(document)
        return document

    @classmethod
    def get_document(cls, uuid, include_deleted=False):
        """Returns document instance identified by UUID.

        Find existing document::

            >>> from flask import g
            >>> from invenio.base.factory import create_app
            >>> app = create_app()
            >>> ctx = app.test_request_context()
            >>> ctx.push()
            >>> from invenio.modules.documents import api
            >>> from invenio.modules.jsonalchemy.jsonext.engines import memory
            >>> app.config['DOCUMENTS_ENGINE'] = \
            "invenio.modules.jsonalchemy.jsonext.engines.memory:MemoryStorage"
            >>> d = api.Document.create({'title': 'Title 1'})
            >>> e = api.Document.get_document(d['_id'])

        If you try to find deleted document you will get an exception::

            >>> e.delete()
            >>> api.Document.get_document(d['_id'])
            Traceback (most recent call last):
             ...
            DeletedDocument

        and also if you try to find not existing document::

            >>> import uuid
            >>> api.Document.get_document(str(uuid.uuid4()))
            Traceback (most recent call last):
             ...
            DocumentNotFound
            >>> ctx.pop()


        :returns: a :class:`Document` instance.
        :raises: :class:`~.invenio.modules.documents.errors.DocumentNotFound`
            or :class:`~invenio.modules.documents.errors.DeletedDocument`
        """
        try:
            document = cls(cls.storage_engine.get_one(uuid),
                           process_model_info=True)
        except:
            raise errors.DocumentNotFound

        if not include_deleted and document['deleted']:
            raise errors.DeletedDocument
        return document

    def _save(self):
        try:
            self.__class__.storage_engine.update_one(self.dumps(),
                                                     id=self['_id'])
        except:
            self.__class__.storage_engine.save_one(self.dumps(),
                                                   id=self['_id'])

    def update(self):
        """Update document object."""
        self['modification_date'] = datetime.now()
        self._save()
        return self

    def setcontents(self, source, name, chunk_size=65536):
        """A convenience method to create a new file from a string or file-like
        object.

        :note: All paths has to be absolute or specified in full URI format.

        :param data: .
        :param name: File URI or filename generator taking `self` as argument.
        """

        if isinstance(source, six.string_types):
            self['source'] = source
            f = opener.open(source, 'rb')
        else:
            f = source

        if callable(name):
            name = name(self)
        else:
            name = fs.path.abspath(name)

        signals.document_before_content_set.send(self, name=name)

        if self.get('source', '') != name:
            data = f.read()
            _fs, filename = opener.parse(name)
            _fs.setcontents(filename, data, chunk_size)
            _fs.close()

        signals.document_after_content_set.send(self, name=name)

        if hasattr(f, 'close'):
            f.close()

        self['uri'] = name
        self._save()

    def open(self, mode='r', **kwargs):
        """Open a the 'uri' as a file-like object."""
        _fs, filename = opener.parse(self['uri'])
        return _fs.open(filename, mode=mode, **kwargs)

    def delete(self, force=False):
        """Deletes the instance of document.

        :param force: If it is True then the document is deleted including
            attached files and metadata.
        """

        self['deleted'] = True

        if force and self.get('uri') is not None:
            signals.document_before_file_delete.send(self)
            fs, filename = opener.parse(self['uri'])
            fs.remove(filename)
            self['uri'] = None

        self._save()
