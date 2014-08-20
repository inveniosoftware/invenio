..  This file is part of Invenio
    Copyright (C) 2014 CERN.

    Invenio is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the Free Software Foundation, Inc.,
    59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

.. _common-concepts:

Common Concepts
===============

The description of concepts you will encounter here and there in the
Invenio.  Our interpretation may differ from the practice found in
other products, so please read this carefully.

1. sysno - (ALEPH|old) system number

   Stands for (ALEPH|old) system number only.  Which means that, for
   outside-CERN Invenio installations, stands for an 'old system
   number' whatever it is, if they want to publicise it instead of our
   internal auto-incremented Invenio record identifiers.

2. recID - Invenio record identifier

   Each record has got an auto-incremented ID in the "bibrec" table
   (formerly called "bibitem").  This is the basic "record identifier"
   concept in Invenio.

3. docID - eventual fulltext document identifier

   Each fulltext file may have eventual docID.  This will permit us to
   interconnect records (recID) with fulltext files (docID), if we
   want to.  At the moment there is only one-way connection from recID
   to docID via HTTP field 856.  This is ugly.  I think we may
   probably profit by introducing recID-docID relationship in several
   ways: file protection, reference extraction, fulltext
   indexing... (?!)

4. field - logical field concept such as "reportnumber"

   A bibliographic record is composed of 'fields' such as title or
   author.  Note that we consider 'field' to be a logical concept,
   that is compound and may consist of several physical MARC fields.
   For example, "report number" field consists of several MARC fields
   such as 088 $a, 037 $a, 909C0 $r.  Another example: "first report
   number" consist of only one MARC field, 037 $a.

5. tag - physical field concept such as "088 $a".

   Having defined the concept of 'logical field', let's now turn to
   the 'physical field' that denotes basically the concept of 'MARC
   field' as defined in MARC-21 standard.  In addition to tag, a field
   may contain two identifiers to describe the data content, and
   subfield codes to denote various parts of the content.  See our
   HOWTO MARC guide on this.

   Thus said, in the implementation of our bibliographic tables
   (bibXXx) we have sort of generalized the term 'tag' to stand for::

      tag = tag code + identifier1 + identifier2 + subfield code

   This convention, while taking some freedom from the MARC-21
   standard, enables us to write things like "field: base number, tag:
   909C0b, value: 11".  If this interpretation is indeed too free with
   respect to the standard usage of terms, we may change them in the
   future.

6. collection - here we distinguish (i) primary collection concept
                and (ii) specific collection concept.

   The (i) primary collections are basic organizational structure of
   how the records are grouped together in collections.  The primary
   collections are used in the navigable search interface under the
   'Narrow search' box.  The (ii) specific collections present an
   orthogonal view on the data organization, that is useful to group
   together some records from different primary collections, if they
   present a common pattern.  The specific collections are used in the
   search interface under the 'Focus on' box.

   The primary collections are defined mainly by the collection
   identifier ("980 $a,b"); and the specific collections are as
   defined by any query that is possible for a search engine to
   execute (see also "dbquery" column in the "collection" table).

   In the past we used to use the term "catalogue", that is now
   deprecated, and that can be interchanged with "collection".

7. doctype - stands for web document type concept, used in WebSubmit

   The "document type" is used solely for submission purposes, and
   fulltext access purposes ("setlink"-like).  For example, a document
   type "photo" may be used in many collections such as "Foo Photos",
   "Bar PhotoLab", etc.  Similarly, one collection can cover several
   doctypes.  (M:N relationship)

8. baskets, alerts, settings - covering personal features

   Denote personal features, for which we previously used the terms
   "shelf" and "profile" that are now deprecated.
