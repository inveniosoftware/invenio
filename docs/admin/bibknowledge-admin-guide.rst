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

.. _bibknowledge-admin-guide:

BibKnowledge Admin Guide
========================

Contents
--------

-  **1. `Overview <#shortIntro>`__**
-  **2. `Configure Knowledge Bases <#admin>`__**

   -  2.1  \ `Add a Knowledge Base <#addKB>`__
   -  2.2  \ `Remove a Knowledge Base <#removeKB>`__
   -  2.3  \ `Add a Mapping <#addMappingKB>`__
   -  3.4  \ `Remove a Mapping <#removeMappingKB>`__
   -  3.5  \ `Edit a Mapping <#editMappingKB>`__
   -  3.6  \ `Edit the Attributes of a Knowledge Base <#attrsKB>`__

1. Overview
-----------

The BibKnowledge module provides tools for cataloguers to manage
"knowledge bases", "authority files", and "ontologies". BibKnowledge
contains information for standardisation and record quality checking.
Typical examples: (1) field author institute is often written as "Odd
University Strange Research Lab" though it is officially (canonically)
known as "StrangeLab of the Odd University". (2) If field "author email"
contains "@strange.odd.edu" the author institute should be "StrangeLab
of the Odd University". (3) Ontology files contain information about the
hierarchy of key words.

There are three four types of knowledge bases

-  "map\_from" "map\_to": this is the typical case, the knowledge base
   is essentially a list of left side - right side pairs, like Genf ->
   Geneva or "Odd University Strange Research Lab" -> "StrangeLab of the
   Odd University". The abbreviation for this type is kbr (for
   reference).
-  "authority only": this kind of knowledge base only lists the
   canonical values. Example: "Geneva", "StrangeLab of the Odd
   University". It is a special case of "map\_from" "map\_to", where
   left side and right side are identical. The abbreviation for this
   type is kba (for authority).
-  dynamic: these knowledge bases are "authority only" knowledge bases
   that are built dynamically using a search expression. Example: if the
   author institute is stored in field 100\_\_u, a dynamic knowledge
   base that uses this field, returns all the values of 100\_\_u. The
   abbreviation for this type is kbd (for dynamic).
-  taxonomy (or ontology): an RDF (resource description framework) file
   can be uploaded into invenio and used as a knowledge base.

2. Configure Knowledge Bases
----------------------------

2.1 Add a Knowledge Base
~~~~~~~~~~~~~~~~~~~~~~~~

To add a knowledge base go to the `Manage Knowledge Bases </kb>`__
administration page. Three types of knowledge bases can be added:
"map\_from" "map\_to" by the "Add New Knowledge Base" button, dynamic by
the "Add a dynamic KB" button and a taxonomy by the "Add new Taxonomy"
button. After the knowledge base has been created you will be asked to
fill in its attribute. See `Edit the Attributes of a Knowledge
Base <#attrsKB>`__ to learn more about the attributes of knowledge
bases.

2.2 Remove a Knowledge Base
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove a knowledge base go to the `Manage Knowledge Bases </kb>`__
administration page. Click on the "Delete" button facing the knowledge
base you want to remove and confim. The knowledge base and all the
mapping it includes are removed.

2.3 Add a Mapping
~~~~~~~~~~~~~~~~~

Go to the `Manage Knowledge Bases </kb>`__ administration page and click
on the knowledge base for which you want to add a mapping. Fill in the
form of the "Add New Mapping" section on the left of the page with the
new mapping, and click on "Add New Mapping". The mapping has been
created. Alternatively you can create the mapping without its
attributes, and fill them afterward (See `Edit a
Mapping <#editMappingKB>`__).

2.4 Remove a Mapping
~~~~~~~~~~~~~~~~~~~~

Go to the `Manage Knowledge Bases </kb>`__ administration page and click
on the knowledge base for which you want to remove a mapping. Click on
the "Delete" button facing the mapping you want to delete.

2.5 Edit a Mapping
~~~~~~~~~~~~~~~~~~

Go to the `Manage Knowledge Bases </kb>`__ administration page and click
on the knowledge base for which you want to edit a mapping. Locate the
mapping in the list. You can click on the column headers to order the
list by *Map From* or by *Map To* to help you find it. Once you have
edited the mapping click on the corresponding "Save" button.

2.6 Edit the Attributes of a Knowledge Base
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to the `Manage Knowledge Bases </kb>`__ administration page and click
on the knowledge base you want to edit. In the top menu, click on
"Knowledge Base Attributes". You can then give your knowledge base a
name and a description. Finally click on the "Update Base Attributes"
button.
