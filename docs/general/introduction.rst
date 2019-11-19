..
    This file is part of Invenio.
    Copyright (C) 2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Introduction
============

Invenio is an open source framework for building large-scale digital
repositories.

A framework
-----------
Invenio is first and foremost a framework. It's a framework that you can use
to build a turn-key repository solution, but it is not by itself a final
turn-key repository software. Using Invenio requires you to develop code.

Several repositories have been built on top of Invenio v3, including e.g.:

- `Zenodo <https://zenodo.org>`_ - General purpose research data repository.
- `CERN Open Data <http://opendata.cern.ch>`_ - Open data repository for CERN.
- `CERN Videos <https://videos.cern.ch>`_ - Digital Assets Management system
  with video encoding support.

Several repository software solutions are in the progress of being written on
top of Invenio, including e.g.:

- RERO ILS and Invenio ILS - Integrated Library System.
- WEKO3 - Repository infrastructure for 500+ japanese universities.

Scalability & Safety
--------------------
Two of the main strengths of Invenio is the scalability and safety. Invenio is
built to run on anything from a single machine to clusters of 100s of machines,
to handle 100 records or 100 million records as well as to handle a 1 megabyte
or a 1 petabyte.

That's why we say Invenio is a framework for large-scale digital repositories.
Often, large-scale repositories does not fit in a standard box, which is why
Invenio is first and foremost a framework that helps you build your repository
faster and on a high-quality reliable foundation.

Flexible metadata
-----------------
In its core, Invenio provides you with a flexible record and persistent
identifier store capable of handling 100 millions of records. Records can
use existing metadata formats such as JSON-LD, MARC21, DublinCore, DataCite, as
well as your own custom or derived metadata format. Invenio easily handle
multiple types of records such as bibliographic records, authority records,
people, grants, funders, books and photos to name a few.

Internally Invenio natively store records as JSON documents whose structure
can be validated and described with JSONSchemas. Records can easily be linked
via JSONRef providing you with powerful tools to model your records. Invenio
further comes with robust metadata transformation layer that can serialize
records to e.g. MARCXML, DataCite XML, JSON-LD, Citation Style Language (CSL)
JSON and many other formats.

In addition Invenio provides a persistent identifier store and a resolver
that allows you to use your preferred persistent identifier scheme for
identifying records such as DOIs (Digital Object Identifiers), Handles, PURLs,
URNs or your own local identifier. The persistent identifier resolver further
has support for advanced features such as tombstone pages, redirection and
merged records.

Powerful search
---------------
Under the hood, Invenio uses Elasticsearch, the world's most popular open
source search engine that provides powerful distributed and massively scalable
search engine. Invenio provides all the features of Elasticsearch such as
full-text search, powerful query syntax, advanced stemming and aggregations,
super-fast auto-completion suggesters as well as geospatial search.

Invenio further leverages both instant indexing as well as extremely fast
distributed bulk indexing with rates beyond 10,000 records/second.

File management
---------------
Invenio handles both millions of files and petabytes of data. Invenio provides
natively on object storage REST API that concurrently can use multiple
underlying storage systems such as S3, XRootD, NAS, WebDAV.

The file store further handles integrity checking according to desired
schedules and supports even checking close to 1M files in less than an hour
if your storage backend can support it.

The file store further comes with quota management that allows you detailed
control of max file sizes and upload limits.
