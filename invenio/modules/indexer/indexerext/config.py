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

"""Indexer configuration module."""

from abc import abstractmethod

from invenio.base.i18n import _
from invenio.modules.knowledge.models import KnwKB
from invenio.modules.search.models import Field

from ..errors import IndexerBadConfigurationException
from ..tokenizers.BibIndexTokenizer import BibIndexTokenizer
from ..utils import load_tokenizers


class IndexFactory(object):

    """Abstract class for index factory."""

    @abstractmethod
    def get_index(self):
        """Return a index.

        :return: specific index class
        """
        raise NotImplementedError()

    @abstractmethod
    def get_engine(self):
        """Return a engine.

        :return: specific engine class
        """
        raise NotImplementedError()


class NativeIndexFactory(IndexFactory):

    """Configuration selector for native indexer."""

    def get_index(self):
        """Return a index.

        :return: specific index class
        """
        return NativeIndex

    def get_engine(self):
        """Return a engine.

        :return: specific engine class
        """
        return NativeIndexerConfigurationEngine


class ElasticSearchIndexFactory(IndexFactory):

    """Configuration selector for Elastic Search indexer."""

    def get_index(self):
        """Return a index.

        :return: specific index class
        """
        return ElasticSearchIndex

    def get_engine(self):
        """Return a engine.

        :return: specific engine class
        """
        return ElasticSearchIndexerConfigurationEngine


class Index(object):

    """Describe a index (composed by fields)."""

    def __init__(self, name, description=None, stemming_language=None,
                 synonym_kbrs=None, pre_index_actions=None, field=None,
                 *args, **kwargs):
        """Initialize class.

        Field synonym_kbrs:
            you have to pass a dict like:

            .. code-block:: python

                dict(
                    knwkb: "knowledge name",
                    type: " type of research"
                )

            Where the type can be: "exact", "leading_to_comma" or
            "leading_to_number".

        Field pre_index_actions:
            ou have to pass a array of options like:

            .. code-block:: python

                ['remove_stopwords', 'remove_html_markup',
                 'remove_latex_markup' ]

        :param name: index name
        :param description: general description
        :param stemming_language: stemming language
        :param synonym_kbrs: synonym from knowledge base
        :param pre_index_actions: actions to apply on the field before indexing
        :param field: field associated with this index
        """
        self.name = name
        self.description = description or ""
        self.stemming_language = stemming_language or "en"
        if synonym_kbrs:
            self.synonym_kbrs = synonym_kbrs
        self.pre_index_actions = pre_index_actions or []
        if field:
            self.field = field

    @property
    def synonym_kbrs(self):
        """Get synonym_kbrs."""
        return self._synonym_kbrs or None

    @synonym_kbrs.setter
    def synonym_kbrs(self, value):
        """Set synonym_kbrs."""
        assert 'knwkb' in value
        if isinstance(value['knwkb'], basestring):
            # Load Field from database
            value['knwkb'] = KnwKB.query.filter_by(name=value['knwkb']).one()
        if not isinstance(value['knwkb'], KnwKB):
            raise IndexerBadConfigurationException(
                _("Index %(index_name)s can have synonyms only in "
                  "a Knowledge.", index_name=self.name))
        value['type'] = value['type'] or 'exact'
        self._synonym_kbrs = value

    @property
    def field(self):
        """Get field."""
        return self._field or None

    @field.setter
    def field(self, value):
        """Set field."""
        if isinstance(value, basestring):
            # Load Field from database
            value = Field.query.filter_by(code=value).one()
        if not isinstance(value, Field):
            raise IndexerBadConfigurationException(
                _("Index %(index_name)s can be associated "
                  "only with Field.", index_name=self.name))
        self._field = value


class NativeIndex(Index):

    """Describe a native index."""

    def __init__(self, native=None, *args, **kwargs):
        """Initialize class.

        :param native: special configuration applied to native index
        """
        super(NativeIndex, self).__init__(*args, **kwargs)
        if native:
            self.tokenizer = native['tokenizer'] \
                if 'tokenizer' in native else None

    @property
    def tokenizer(self):
        """Get tokenizer."""
        return self._tokenizer or None

    @tokenizer.setter
    def tokenizer(self, value):
        """Set field."""
        if isinstance(value, basestring):
            # Load tokenizers
            tokenizers = load_tokenizers()
            value = tokenizers[value]() if value in tokenizers else None
        if value and not isinstance(value, BibIndexTokenizer):
            raise IndexerBadConfigurationException(
                _("Native Index %(index_name)s can't use "
                  "the tokenizer %(tokenizer)s",
                  index_name=self.name,
                  tokenizer=value))
        self._tokenizer = value


class ElasticSearchIndex(Index):

    """Describe a Elastic Search index."""

    def __init__(self, elasticsearch=None, *args, **kwargs):
        r"""Initialize class.

        :param elasticsearch: special configuration applied to \
            elasticsearch index
        """
        super(ElasticSearchIndex, self).__init__(*args, **kwargs)
        if elasticsearch:
            self.analyzer = elasticsearch['analyzer'] \
                if 'analyzer' in elasticsearch else None


class VirtualIndex(object):

    """Describe a virtual index (composed by indices)."""

    default_namespace = 'default'

    def __init__(self, name, description=None, indices=None, namespace=None):
        r"""Initialize class.

        :param name: index name
        :param description: index description
        :param indices: list of indices to describe the virtual index
        :param namespace: set the namespace of the virtual index \
            (e.g. records or documents, default value = 'default')
        """
        self.name = name
        self.description = description or ""
        self.indices = indices
        self.namespace = namespace or VirtualIndex.default_namespace

    @property
    def indices(self):
        """Get indices."""
        return self._indices or []

    @indices.setter
    def indices(self, value):
        """Set indices."""
        value = {value.name: value} if isinstance(value, Index) else value
        if not all(isinstance(index, Index) for index in value.itervalues()):
            raise IndexerBadConfigurationException(_(
                "Virtual Index can contain only Indices"
            ))
        self._indices = value or {}


class IndexerConfiguration(object):

    """Describe a indexer configuration."""

    def __init__(self, virtual_indices):
        """Initialize class.

        :param virtual_indices: list of virtual indices or single virtual index
        """
        self.virtual_indices = virtual_indices

    @property
    def virtual_indices(self):
        """Get virtual indices."""
        return self._virtual_indices or []

    @virtual_indices.setter
    def virtual_indices(self, virtual_indices):
        """Set virtual indices."""
        virtual_indices = [virtual_indices] \
            if isinstance(virtual_indices, VirtualIndex) \
            else virtual_indices

        self._virtual_indices = virtual_indices or []

    def filter_by_namespace(self, namespace=None):
        """Get the list of virtual indices of a specific namespace.

        :param namespace: namespace's name
        :return: list of virtual indices inside the specified namespace
        """
        if isinstance(namespace, dict):
            namespace = namespace.itervalues
        elif isinstance(namespace, str):
            namespace = [namespace]

        return filter(
            lambda vi: vi.namespace in namespace,
            self.virtual_indices) if namespace else self.virtual_indices


class IndexerConfigurationEngine(object):

    """Abstract Engine for indexing configuration."""

    def __init__(self, index_configuration):
        """Initialize engine.

        :param index_configuration: index configuration object
        """
        self.index_configuration = index_configuration

    @abstractmethod
    def create():
        """Execute actions to create indices on a specific indexer."""
        raise NotImplementedError()

    @abstractmethod
    def drop():
        """Execute actions to drop indices on a specific indexer."""
        raise NotImplementedError()

    @abstractmethod
    def recreate():
        """Execute actions to recreate indices on a specific indexer."""
        raise NotImplementedError()

    @abstractmethod
    def clear():
        """Execute actions to clear indices on a specific indexer."""
        raise NotImplementedError()

    @abstractmethod
    def index():
        """Execute actions to start indexing on a specific indexer."""
        raise NotImplementedError()

    @abstractmethod
    def reindex():
        """Execute actions to start reindexing on a specific indexer."""
        raise NotImplementedError()


class NativeIndexerConfigurationEngine(IndexerConfigurationEngine):

    """Engine for native configuration."""


class ElasticSearchIndexerConfigurationEngine(IndexerConfigurationEngine):

    """Engine for Elastic Search configuration."""
