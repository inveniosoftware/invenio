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

.. _bibclassify-admin-guide:

BibClassify Admin Guide
=======================

1. Overview
-----------

BibClassify automatically extracts keywords from fulltext documents. The
automatic assignment of keywords to textual documents has clear benefits
in the digital library environment as it aids catalogization,
classification and retrieval of documents.

1.1 Thesaurus
~~~~~~~~~~~~~

BibClassify performs an extraction of keywords based on the recurrence
of specific terms, taken from a controlled vocabulary. A controlled
vocabulary is a thesaurus of all the terms that are relevant in a
specific context. When a context is defined by a discipline or branch of
knowledge then the vocabulary is said to be a *subject thesaurus*.
Various existing subject thesauri can be found
`here <http://www.fbi.fh-koeln.de/institut/labor/Bir/thesauri_new/thesen.htm>`__.

A subject thesaurus can be expressed in several different formats.
Different institutions/disciplines have developed different ways of
representing their vocabulary systems. The taxonomy used by bibclassify
is expressed in RDF/SKOS. It allows not only to list keywords but to
specify relations between the keywords and alternative ways to represent
the same keyword.

    ::

        <Concept rdf:about="http://cern.ch/thesauri/HEP.rdf#scalar">
         <composite rdf:resource="http://cern.ch/thesauri/HEP.rdf#Composite.fieldtheoryscalar"/>
         <prefLabel xml:lang="en">scalar</prefLabel>
         <note xml:lang="en">nostandalone</note>
        </Concept>

        <Concept rdf:about="http://cern.ch/thesauri/HEP.rdf#fieldtheory">
         <composite rdf:resource="http://cern.ch/thesauri/HEP.rdf#Composite.fieldtheoryscalar"/>
         <prefLabel xml:lang="en">field theory</prefLabel>
         <altLabel xml:lang="en">QFT</altLabel>
         <hiddenLabel xml:lang="en">/field theor\w*/</hiddenLabel>
         <note xml:lang="en">nostandalone</note>
        </Concept>

        <Concept rdf:about="http://cern.ch/thesauri/HEP.rdf#Composite.fieldtheoryscalar">
         <compositeOf rdf:resource="http://cern.ch/thesauri/HEP.rdf#scalar"/>
         <compositeOf rdf:resource="http://cern.ch/thesauri/HEP.rdf#fieldtheory"/>
         <prefLabel xml:lang="en">field theory: scalar</prefLabel>
         <altLabel xml:lang="en">scalar field</altLabel>
        </Concept>

In RDF/SKOS, every keyword is wrapped around a *concept* which
encapsulates the full semantics and hierarchical status of a term -
including synonyms, alternative forms, broader concepts, notes and so on
- rather than just a plain keyword.

The specification of the SKOS language and `various
manuals <http://www.w3.org/TR/2005/WD-swbp-thesaurus-pubguide-20050517/>`__
that aid the building of a semantic thesaurus can be found at the `SKOS
W3C
website <http://www.w3.org/TR/2005/WD-swbp-skos-core-guide-20051102/>`__.
Furthermore, BibClassify can function on top of an extended version of
SKOS, which includes special elements such as key chains, composite
keywords and special annotations. The extension of the SKOS language is
documented in the `hacking
guide </help/hacking/bibclassify-internals>`__.

1.2 Keyword extraction
~~~~~~~~~~~~~~~~~~~~~~

BibClassify computes the keywords of a fulltext document based on the
frequency of thesaurus terms in it. In other words, it calculates how
many times a thesaurus keyword (and its alternative and hidden labels,
defined in the taxonomy) appears in a text and it ranks the results.
Unlike other similar systems, BibClassify does not use any machine
learning or AI methodologies - a just plain phrase matching using
`regular expressions <http://en.wikipedia.org/wiki/Regex>`__: it
exploits the conformation and richness of the thesaurus to produce
accurate results. It is then clear that BibClassify performs best on top
of rich, well-structured, subject thesauri expressed in the RDF/SKOS
language.

A detailed account of the phrase matching mechanisms used by BibClassify
is included in the `hacking
guide </help/hacking/bibclassify/>`__.

2. Running BibClassify
----------------------

 **Dependencies.** BibClassify requires Python
`RDFLib <http://rdflib.net/>`__ in order to process the RDF/SKOS
taxonomy.

In order to extract relevant keywords from a document ``fulltext.pdf``
based on a controlled vocabulary ``thesaurus.rdf``, you would run
BibClassify as follows:

    ::

        $ bibclassify.py -k thesaurus.rdf fulltext.pdf

Launching ``bibclassify --help`` shows the options available for
BibClassify:

::

    Usage: bibclassify [OPTION]... [FILE/URL]...
           bibclassify [OPTION]... [DIRECTORY]...
    Searches keywords in FILEs and/or files in DIRECTORY(ies). If a directory is
    specified, BibClassify will generate keywords for all PDF documents contained
    in the directory.  Can also run in a daemon mode, in which case the files to
    be run are looked for from the database (=records modified since the last run).

    General options:
      -h, --help                display this help and exit
      -V, --version             output version information and exit
      -v, --verbose=LEVEL       sets the verbose to LEVEL (=0)
      -k, --taxonomy=NAME       sets the taxonomy NAME. It can be a simple
                                controlled vocabulary or a descriptive RDF/SKOS
                                and can be located in a local file or URL.

    Standalone file mode options:
      -o, --output-mode=TYPE    changes the output format to TYPE (text, marcxml or
                                html) (=text)
      -s, --spires              outputs keywords in the SPIRES format
      -n, --keywords-number=INT sets the number of keywords displayed (=20), use 0
                                to set no limit
      -m, --matching-mode=TYPE  changes the search mode to TYPE (full or partial)
                                (=full)
      --detect-author-keywords  detect keywords that are explicitely written in the
                                document
    Daemon mode options:
      -i, --recid=RECID         extract keywords for a record and store into DB
                                (=all necessary ones for pre-defined taxonomies)
      -c, --collection=COLL     extract keywords for a collection and store into DB
                                (=all necessary ones for pre-defined taxonomies)

    Taxonomy management options:
      --check-taxonomy          checks the taxonomy and reports warnings and errors
      --rebuild-cache           ignores the existing cache and regenerates it
      --no-cache                don't cache the taxonomy

    Backward compatibility options (discouraged):
      -q                        equivalent to -s
      -f FILE URL               sets the file to read the keywords from

    Examples (standalone file mode):
        $ bibclassify -k HEP.rdf http://arxiv.org/pdf/0808.1825
        $ bibclassify -k HEP.rdf article.pdf
        $ bibclassify -k HEP.rdf directory/

    Examples (daemon mode):
        $ bibclassify -u admin -s 24h -L 23:00-05:00
        $ bibclassify -u admin -i 1234
        $ bibclassify -u admin -c Preprints

 **NB.** BibClassify can run as a CDS Invenio module or as a standalone
program. If you already run a server with a Invenio installation, you
can simply run */opt/invenio/bin/bibclassify [options]*. Otherwise, you
can run from BibClassify sources *bibclassify [options]*.

As an example, running BibClassify on document
`nucl-th/0204033 <http://cds.cern.ch/record/547024>`__ using the
high-energy physics RDF/SKOS taxonomy (``HEP.rdf``) would yield the
following results (based on the HEP taxonomy from October 10th 2008):

::

    Input file: 0204033.pdf

    Author keywords:
    Dense matter
    Saturation
    Unstable nuclei

    Composite keywords:
    10  nucleus: stability [36, 14]
    6  saturation: density [25, 31]
    6  energy: symmetry [35, 11]
    4  nucleon: density [13, 31]
    3  energy: Coulomb [35, 3]
    2  energy: density [35, 31]
    2  nuclear matter: asymmetry [21, 2]
    1  n: matter [54, 36]
    1  n: density [54, 31]
    1  n: mass [54, 16]

    Single keywords:
    61  K0
    23  equation of state
    12  slope
    4  mass number
    4  nuclide
    3  nuclear model
    3  mass formula
    2  charge distribution
    2  elastic scattering
    2  binding energy

or, the following keyword-cloud HTML visualization:
|tag-cloud for document nucl-th/0204033|

.. |tag-cloud for document nucl-th/0204033| image:: /_static/admin/bibclassify-admin-guide-cloud.jpeg
