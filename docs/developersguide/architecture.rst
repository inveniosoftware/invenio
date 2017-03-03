Overview of architecture
========================


Invenio v3.x
------------

.. admonition:: CAVEAT LECTOR

   Invenio v3.0 alpha is a bleeding-edge developer preview version.

Invenio v3.0 build on top of `Flask`_ web development framework, using `Jinja2`_
template engine, `SQLAlchemy`_ Object Relational Mapper, `JSONSchema`_ data
model, `PostgreSQL`_ database for persistence, and `Elasticsearch`_ for
information retrieval.

.. _Flask: http://flask.pocoo.org/
.. _Jinja2: http://jinja.pocoo.org/docs/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _JSONSchema: http://json-schema.org/
.. _PostgreSQL: http://www.postgresql.org/
.. _Elasticsearch: https://www.elastic.co/products/elasticsearch

Invenio's architecture is modular. The code base is split into more than 50
independent components that are `released independently on PyPI
<https://pypi.python.org/pypi?:action=search&term=inveniosoftware&submit=search>`_.
This ensures strict separation of components that talk among themselves over API
and permits rapid development of independent components by independent teams.

Invenio compontents, named *modules*, can be roughly split in three categories:

1. **base modules** provide interfaces to the Flask ecosystem, the Database, and
   other system tools and technologies that the Invenio ecosystem uses. Example:
   ``Invenio-Celery`` that talks to the Celery worker system.

2. **core feature modules** provide most common functionality that each digital
   library instance is likely interested in using. Example: ``Invenio-Records``
   provide record object store.

3. **additional feature modules** offer additional functionality suitable for
   various particular use cases, such as the Integrated Library System, the
   Multimedia Store, or the Data Repository. Example: ``Invenio-Circulation``
   offers circulation and holdings capabilities.

Here is a basic bird-eye overview of available Invenio components and their
dependencies: (*work in progress*)

.. graphviz::

   digraph invenio3 {
     size="20.0 20.0";
     ratio="compress";

     // helper floors
     node [shape=plaintext,style=invis];
     {
       Floor9 -> Floor8 [style=invis];
       Floor8 -> Floor7 [style=invis];
       Floor7 -> Floor6 [style=invis];
       Floor6 -> Floor5 [style=invis];
       Floor5 -> Floor4 [style=invis];
       Floor4 -> Floor3 [style=invis];
       Floor3 -> Floor2 [style=invis];
       Floor2 -> Floor1 [style=invis];
       Floor1 -> Floor0 [style=invis];
     }

     // invenio tools family
     node [shape=ellipse,style=dotted];
     Elasticsearch;
     "JSON Schema";
     MySQL;
     PostgreSQL;
     FS;
     Drive;
     Dropbox;
     S3;
     " Celery ";
     Flask;

     // invenio base plate family
     node [shape=box,style=filled];
     Access;
     Admin;
     Assets;
     Base;
     Celery -> " Celery ";
     Config;
     DB -> MySQL;
     DB -> PostgreSQL;
     I18N;
     JSONSchemas -> "JSON Schema";
     Logging;
     REST;
     Theme;
     Upgrader -> DB;

     // invenio search family
     node [shape=box,style=filled, color=green];
     "Records-UI" -> Records;
     "Records-REST" -> Records;
     "Records-REST" -> PIDStore;
     Records -> DB;
     "Search-UI" -> Search;
     Search -> Records;
     "Records-REST" -> Search;
     PIDStore -> Records;
     PIDStore -> DB;
     node [shape=ellipse,style=filled,color=grey];
     "Search-UI" -> "Query-Parser" ;
     "Search-UI" -> unAPI;
     node [shape=ellipse,style=dotted,color=black];
     Search -> Elasticsearch;

     // invenio deposit family
     node [shape=box,style=filled, color=red];
     "Deposit-UI" -> Deposit;
     "Deposit-REST" -> Deposit;
     Deposit -> Workflows;
     Deposit -> Knowledge;
     Deposit -> Sequencegenerator;
     Workflows -> Records;
     Workflows -> Documents;

     // invenio accounts family
     node [shape=box,style=filled, color="0.5 0.5 1.0"];
     "Profiles-UI" -> Profiles;
     "Profiles-REST" -> Profiles;
     "Groups-UI" -> Groups;
     "Groups-REST" -> Groups;
     Profiles -> Access;
     Profiles -> Accounts;
     Accounts -> Access;
     Groups -> Accounts;

     // invenio helpers family
     node [shape=ellipse,style=filled,color=grey];
     Documents;
     Cloudconnector;
     Testing;
     Utils;
     Ext;
     Webhooks;
     Redirector;

     // invenio OAIS family
     node [shape=box,style=filled,color=orange];
     "OAIS-Audit-Store" -> DB;
     "OAIS-SIP-Store" -> DB;
     "OAIS-AIP-Store" -> Cloudconnector;
     "OAIS-DIP-Store" -> DB;
     Archiver;
     Deposit -> "OAIS-SIP-Store";
     Workflows -> "OAIS-SIP-Store";
     Records -> Archiver;
     Documents -> Archiver;
     Archiver -> "OAIS-AIP-Store";
     Records -> "OAIS-Audit-Store";

     // invenio add-ons family
     node [shape=box, style=filled, color=yellow];
     Alerts -> Records;
     Annotations -> Records;
     Annotations -> Profiles;
     Classifier -> Records;
     Client -> "Records-REST";
     Client -> "Groups-REST";
     Client -> "Profiles-REST";
     Client -> "Deposit-REST";
     Documents -> Cloudconnector;
     Documents -> FS;
     Cloudconnector -> Dropbox;
     Cloudconnector -> Drive;
     Cloudconnector -> S3;
     Collections -> Records;
     Comments -> Records;
     Comments -> Profiles;
     Communities -> Collections;
     Communities -> Groups;
     Communities -> Profiles;
     Deposit -> Documents;
     Deposit -> Records;
     Deposit -> PIDStore;
     Documents -> Records;
     Formatter -> Records;
     Formatter -> "OAIS-DIP-Store";
     Records -> JSONSchemas;
     News -> Theme;
     OAIHarvester -> DB;
     OAIHarvester -> Workflows;
     OAIHarvester -> Records;
     OAuthClient -> Accounts;
     OAuth2Server -> Accounts;
     Pages -> Theme;
     Previewer -> Records;
     Previewer -> "Previewer-ISPY";
     Editor -> "Records-REST";
     Checker -> "Records-REST";
     Merger -> "Records-REST";
     Statistics;
     Tags -> Records;
     Tags -> Profiles;

     // invenio ILS family
     node [shape=box, style=filled, color=purple];
     "Circulation-UI" -> Circulation;
     "Circulation-REST" -> Circulation;
     "Acquisition-UI" -> Acquisition;
     "Acquisition-REST" -> Acquisition;
     Client -> "Circulation-REST";
     Client -> "Acquisition-REST";
     Circulation -> Records;
     Circulation -> Accounts;
     Acquisition -> Records;
     Acquisition -> Accounts;


     // invenio end user
     node [shape=plaintext, color=white];
     Users;
     Users -> "Deposit-UI";
     Users -> "Search-UI";
     Users -> "Records-UI";
     Users -> "Circulation-UI";
     Users -> "Acquisition-UI";

     // floor 0
     {
       rank = same;
       Floor0;
       Elasticsearch;
       MySQL;
       PostgreSQL;
       " Celery ";
       "JSON Schema";
       Flask;
       Drive;
       Dropbox;
       S3;
       FS;
     }

     // floor 1
     {
       rank = same;
       Floor1;
       Access;
       Admin;
       Assets;
       Base;
       Celery;
       Config;
       DB;
       I18N;
       JSONSchemas;
       Logging;
       Theme;
       REST;
       Upgrader;
       DB;
       Testing;
       Utils;
       Ext;
       Webhooks;
       Redirector;
     }

     // floor 8
     {
       rank = same;
       Floor8;
       "Records-UI";
       "Records-REST";
       "Deposit-UI";
       "Deposit-REST";
       "Search-UI";
       "Profiles-UI";
       "Profiles-REST";
       "Groups-UI";
       "Groups-REST";
       "Circulation-UI";
       "Circulation-REST";
       "Acquisition-UI";
       "Acquisition-REST";
     }
     // floor 9
     {
       rank = same;
       Floor9;
       Client;
       Users;
     }

   }

For further information, see :ref:`module_anatomy` and :ref:`module_list`
sections.

Invenio v2.x
------------

Invenio v2.x was a transitional release series combining legacy code base
(Invenio v1.x) with new technology (Flask etc as used in Invenio v3.x).

Invenio v1.x
------------

Invenio consists of several more or less independent modules with precisely
defined functionality. The general criterion for module names is to use the
"Bib" prefix to denote modules that work more with the bibliographic data, and
the "Web" prefix to denote modules that work more with the Web interface. (The
difference is of course blurred in some cases, as in the case of search engine
that has got a web interface but searches bibliographic data.)

.. image:: /_static/modules-overview-diagram.jpeg

Follows a brief description of what each module does.

- BibCheck permits administrators and library cataloguers to automate various
  kind of tests on the metadata to see whether the metadata comply with quality
  standards. For example, that certain metadata fields are of a certain length,
  that they have numeric content, that they must not be present when other field
  exists, that their content is governed by an authority base depending on
  values of other fields, etc. The module can report its findings or can even
  automatically correct some kind of errors.

- BibClassify allows automatic extraction of keywords from fulltext documents,
  based on the frequency of specific terms, taken from a controlled vocabulary.
  Controlled vocabularies can be expressed as simple text thesauri or as
  structured, RDF-compliant, taxonomies, to allow a semantic classification.

- BibConvert allows metadata conversion from any structured or semi-structured
  proprietary format into any other format, typically the MARC XML that is
  natively used in Invenio. Nevertheless the input and output formats are fully
  configurable and have been tested on data importations from more than one
  hundred data sources. The power of this utility lies in the fact that no
  structural attributes of data source are presumed, but they are defined in an
  extensive data source configuration. Inevitably, this leads to a high
  complexity of the BibConvert configuration language. Most frequent
  configurations are provided with the Invenio distribution, such as a sample
  configuration from Qualified Dublin Core into the MARCXML. In general the
  BibConvert configuration consists from the source data descriptions and target
  data descriptions. The processor then analyzes and parses the input data and
  creates the resulting data structure, similarly as the XSLT processor would
  do. Typically the BibConvert is aimed at usage for input data that do not
  dispose of an XML representation. The source data is required to be structured
  or semi-structured, (i.e. not expressed in natural language that is a subject
  of information extraction task) and its processing involves several steps
  including record separation and field extraction upto transformation of source
  field values and their formatting.

- BibEdit permits one to edit the metadata via a Web interface.

- BibFormat is in charge of formatting the bibliographic metadata in numerous
  ways. This truly enables the separation of data content administration and
  formatting layout. BibFormat can act in the background and format the records
  when needed, or can preformat records for some often used outputs, such as the
  brief format used when displaying search results. The BibFormat settings can
  be administered either through a user-friendly web interface, or directly by
  editing human-readable configuration files.

- OAIHarvest represents the OAi-PMH compatible harvester allowing the repository
  to gather metadata from fellow OAi-compliant repositories and the OAi-PMH
  repository management. Repository is built directly on top of the database and
  disposes of an OAi repository manager that allows to perform the
  administrative tasks on the repository aside from the principal generic data
  administration module. The database can be partially or completely open for
  harvesting in the scope of the OAi-PMH protocol. In this case, all data is
  provided in raw form, where the semantics of individual tags is indicated
  uniquely by the MARC21 naming convention. This is particularly interesting for
  institutes that are specialized in cross-archive and cross-disciplinary
  services provision, as for example the ARC service provider.

- BibIndex module takes care of the indexation of metadata, references and full
  text files. Two kinds of indexes -- word and phrase index -- are being
  maintained. The user can define several logical indexes (e.g. author index,
  title index, etc.) and the correspondence of which physical MARC21 metadata
  tag goes into which logical field index. An index consists of two parts: (i) a
  forward index listing various words (or phrases) found in the given field,
  with the set of record identifiers where the given word can be found; and (ii)
  a reverse index listing record identifiers, with the set of words of the given
  record that go to the forward index. Such a two-part indexing technique allows
  one to rapidly update only those words that have changed in the input metadata
  record. The indexes were designed with the aim to provide fast user-response
  search times and are faster than native MySQL (full text) indexes.

- BibMatch permits to filter input XML files against the database content,
  attempting to match records via certain criteria, for example to avoid
  doubly-inputted records.

- BibRank permits to set up various ranking criteria that will be used later by
  the search engine. For example, ranking by the word frequency, or by some
  metadata tag value such as journal name by means of the journal impact factor
  knowledge base, or even by the number of downloads of a particular paper. Note
  that BibRank is independent of BibIndex.

- BibSched The bibliographic task scheduler is central unit of the system that
  allows all other modules to access the bibliographic database in a controlled
  manner, preventing sharing violation threats and assuring the coherent
  execution of the database update tasks. The module comes with an
  administrative interface that allows to monitor the task queue including
  various possibilities of a manual intervention, for example to re-schedule
  queued tasks, change the task order, etc.

- BibUpload allows to load the new bibliographic data into the database. To
  effectuate this task the data must be a well-formed XML file that complies
  with the current metadata tag selection schema. Usually, the properly
  structured input files of BibUpload come from the BibConvert utility.

- ElmSubmit is an email submission gateway that permits for automatic document
  uploads from trusted sources via email. (Usually web submission or harvesting
  is preferred.)

- MiscUtil is a collection of miscellaneous utilities that other modules are
  using, like the international messages, etc.

- WebAccess module is responsible for granting access to users for performing
  various actions within the system. A Role-Based Access Control (RBAC)
  technique is used, where users belong to several groups according to their
  role in the system. Each user group can be granted to perform certain actions
  depending on possible one more action arguments. WebAccess is presently used
  mainly for the administrative interface. There are basically two kinds of
  actions: (i) configuration of administrative modules and (ii) running
  administrative tasks.

- WebAlert module allows the end user to be alerted whenever a new document
  matching her personal criteria is inserted into the database. The criteria
  correspond to a typical user query as if it would be done via the search
  interface. For example, a user may want to get notified whenever a new
  document containing certain words, or of a certain subject, is inserted. A
  user may create several alerts with a daily, weekly, or a monthly frequency.
  The results of alert searches are either sent back to the user by email or can
  also be stored into her baskets.

- WebBasket module enables the end user of the system to store the documents she
  is interested in in a personal basket or a personal shelf. The concept is
  similar to popular shopping carts. One user may own several baskets. A basket
  can be either private or public, allowing a simple document sharing mechanism
  within a group.

- WebComment provides a community-oriented tool to rank documents by the readers
  or to share comments on the documents by the readers. Integrated with the
  group-aware WebBasket, WebGroup, WebMessage tools, WebComment is at the heart
  of the social network features of the Invenio software.

- WebHelp presents some global user-level, admin-level, and hacker-level
  documenation on Invenio. The module-specific documentation is included within
  each particular module.

- WebMessage permits the communication between (possibly anonymous) end users
  via web message boards, to invite readers to join the groups, etc.

- WebSearch module handles user requests to search for a certain words or
  phrases in the database. Two types of searching can be performed: a word
  search or a phrase search. The system allows for complex boolean queries,
  regular expression searching, or a combined metadata, references and full text
  file searching in one go. Users have a possibility to browse for present index
  terms. If no direct match could have been found with the user-typed query
  pattern, the system proposes alternative matches as a search guidance. The
  search indexes were designed to provide fast response times for middle-sized
  data collections of up to 106 records. The metadata corpus is organized into
  metadata collections that are directly accessible through the browse function,
  similarly to the popular concept of Web Directories. Orthogonal views on the
  document corpus are enabled in the search interface via a concept of virtual
  collections: for example, a document may be classified both according to its
  type (e.g. preprint, book) and according to its Dewey decimal classification
  number. Such a flexible organization views allows for the creation of easy
  navigation schemata to the end users.

- WebSession is a session and user management module that permits to
  differentiate between users. Useful for personalization of the interface and
  services like personal baskets and alerts.

- WebStat is a configurable system that permits to gather statistics about the
  health of the server, the usage of the system, as well as about some
  particular system features.

- WebStyle is a library of design-related modules that defines look and feel of
  Invenio pages.

- WebSubmit is a comprehensive submission system allowing authorized individuals
  (authors, secretaries and repository maintenance staff) to submit individual
  documents into the system. The submission system disposes of a flow-control
  mechanism that assures the data approval by authorized units. In total there
  are several different exploitable submission schemas at a disposal, including
  an automated full text document conversion from various textual and image
  formats. This module also disposes of information extraction functionality,
  focusing on bibliographic entities such as references, authors, keywords or
  other implicit metadata.



  Base modules
  ============

  The **base modules** provide interfaces to the base technology modules
  used by the Invenio package ecosystem.

  cookiecutter-invenio-module
  +++++++++++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/cookiecutter-invenio-module>`_
  - releases: `<https://github.com/inveniosoftware/cookiecutter-invenio-module/releases>`_
  - known issues: `<https://github.com/inveniosoftware/cookiecutter-invenio-module/issues>`_
  - documentation: `<https://cookiecutter-invenio-module.readthedocs.io/>`_

  generator-invenio-js-module
  +++++++++++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/generator-invenio-js-module>`_
  - releases: `<https://github.com/inveniosoftware/generator-invenio-js-module/releases>`_
  - known issues: `<https://github.com/inveniosoftware/generator-invenio-js-module/issues>`_
  - documentation: `<https://www.npmjs.com/package/generator-invenio-js-module>`_

  invenio-admin
  +++++++++++++

  Invenio module that adds administration panel to the system.

  - source code: `<https://github.com/inveniosoftware/invenio-admin>`_
  - releases: `<https://github.com/inveniosoftware/invenio-admin/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-admin/issues>`_
  - documentation: `<https://invenio-admin.readthedocs.io/>`_

  invenio-assets
  ++++++++++++++

  Media assets management for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-assets>`_
  - releases: `<https://github.com/inveniosoftware/invenio-assets/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-assets/issues>`_
  - documentation: `<https://invenio-assets.readthedocs.io/>`_

  invenio-base
  ++++++++++++

  Base package for building the Invenio application.

  - source code: `<https://github.com/inveniosoftware/invenio-base>`_
  - releases: `<https://github.com/inveniosoftware/invenio-base/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-base/issues>`_
  - documentation: `<https://invenio-base.readthedocs.io/>`_

  invenio-celery
  ++++++++++++++

  Celery module for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-celery>`_
  - releases: `<https://github.com/inveniosoftware/invenio-celery/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-celery/issues>`_
  - documentation: `<https://invenio-celery.readthedocs.io/>`_

  invenio-config
  ++++++++++++++

  Invenio configuration loader.

  - source code: `<https://github.com/inveniosoftware/invenio-config>`_
  - releases: `<https://github.com/inveniosoftware/invenio-config/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-config/issues>`_
  - documentation: `<https://invenio-config.readthedocs.io/>`_

  invenio-db
  ++++++++++

  Database management for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-db>`_
  - releases: `<https://github.com/inveniosoftware/invenio-db/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-db/issues>`_
  - documentation: `<https://invenio-db.readthedocs.io/>`_

  invenio-formatter
  +++++++++++++++++

  Jinja utilities for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-formatter>`_
  - releases: `<https://github.com/inveniosoftware/invenio-formatter/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-formatter/issues>`_
  - documentation: `<https://invenio-formatter.readthedocs.io/>`_

  invenio-i18n
  ++++++++++++

  Invenio internationalization module.

  - source code: `<https://github.com/inveniosoftware/invenio-i18n>`_
  - releases: `<https://github.com/inveniosoftware/invenio-i18n/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-i18n/issues>`_
  - documentation: `<https://invenio-i18n.readthedocs.io/>`_

  invenio-logging
  +++++++++++++++

  Module providing logging capabilities.

  - source code: `<https://github.com/inveniosoftware/invenio-logging>`_
  - releases: `<https://github.com/inveniosoftware/invenio-logging/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-logging/issues>`_
  - documentation: `<https://invenio-logging.readthedocs.io/>`_

  invenio-mail
  ++++++++++++

  Invenio mail module.

  - source code: `<https://github.com/inveniosoftware/invenio-mail>`_
  - releases: `<https://github.com/inveniosoftware/invenio-mail/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-mail/issues>`_
  - documentation: `<https://invenio-mail.readthedocs.io/>`_

  invenio-oauth2server
  ++++++++++++++++++++

  Invenio module that implements OAuth 2 server.

  - source code: `<https://github.com/inveniosoftware/invenio-oauth2server>`_
  - releases: `<https://github.com/inveniosoftware/invenio-oauth2server/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-oauth2server/issues>`_
  - documentation: `<https://invenio-oauth2server.readthedocs.io/>`_

  invenio-oauthclient
  +++++++++++++++++++

  Invenio module that provides OAuth web authorization support.

  - source code: `<https://github.com/inveniosoftware/invenio-oauthclient>`_
  - releases: `<https://github.com/inveniosoftware/invenio-oauthclient/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-oauthclient/issues>`_
  - documentation: `<https://invenio-oauthclient.readthedocs.io/>`_

  invenio-rest
  ++++++++++++

  REST API module for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-rest>`_
  - releases: `<https://github.com/inveniosoftware/invenio-rest/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-rest/issues>`_
  - documentation: `<https://invenio-rest.readthedocs.io/>`_

  invenio-theme
  +++++++++++++

  Invenio standard theme.

  - source code: `<https://github.com/inveniosoftware/invenio-theme>`_
  - releases: `<https://github.com/inveniosoftware/invenio-theme/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-theme/issues>`_
  - documentation: `<https://invenio-theme.readthedocs.io/>`_

  invenio-upgrader
  ++++++++++++++++

  Upgrader engine for Invenio modules.

  - source code: `<https://github.com/inveniosoftware/invenio-upgrader>`_
  - releases: `<https://github.com/inveniosoftware/invenio-upgrader/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-upgrader/issues>`_
  - documentation: `<https://invenio-upgrader.readthedocs.io/>`_

  invenio-webhooks
  ++++++++++++++++

  Invenio module for processing webhook events.

  - source code: `<https://github.com/inveniosoftware/invenio-webhooks>`_
  - releases: `<https://github.com/inveniosoftware/invenio-webhooks/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-webhooks/issues>`_
  - documentation: `<https://invenio-webhooks.readthedocs.io/>`_

  Core feature modules
  ====================

  The **core feature modules** provide most common functionality that each digital
  library instance is likely interested in using, such as record store,
  search, deposit, or access control capabilities.

  invenio-access
  ++++++++++++++

  Invenio module for common role based access control.

  - source code: `<https://github.com/inveniosoftware/invenio-access>`_
  - releases: `<https://github.com/inveniosoftware/invenio-access/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-access/issues>`_
  - documentation: `<https://invenio-access.readthedocs.io/>`_

  invenio-accounts
  ++++++++++++++++

  Invenio user management and authentication.

  - source code: `<https://github.com/inveniosoftware/invenio-accounts>`_
  - releases: `<https://github.com/inveniosoftware/invenio-accounts/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-accounts/issues>`_
  - documentation: `<https://invenio-accounts.readthedocs.io/>`_

  invenio-collections
  +++++++++++++++++++

  Invenio module for organizing metadata into collections.

  - source code: `<https://github.com/inveniosoftware/invenio-collections>`_
  - releases: `<https://github.com/inveniosoftware/invenio-collections/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-collections/issues>`_
  - documentation: `<https://invenio-collections.readthedocs.io/>`_

  invenio-deposit
  +++++++++++++++

  Module for depositing record metadata and uploading files.

  - source code: `<https://github.com/inveniosoftware/invenio-deposit>`_
  - releases: `<https://github.com/inveniosoftware/invenio-deposit/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-deposit/issues>`_
  - documentation: `<https://invenio-deposit.readthedocs.io/>`_

  invenio-files-js
  ++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-files-js>`_
  - releases: `<https://github.com/inveniosoftware/invenio-files-js/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-files-js/issues>`_
  - documentation: `<https://www.npmjs.com/package/invenio-files-js>`_

  invenio-files-rest
  ++++++++++++++++++

  Files download/upload REST API similar to S3 for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-files-rest>`_
  - releases: `<https://github.com/inveniosoftware/invenio-files-rest/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-files-rest/issues>`_
  - documentation: `<https://invenio-files-rest.readthedocs.io/>`_

  invenio-indexer
  +++++++++++++++

  Indexer for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-indexer>`_
  - releases: `<https://github.com/inveniosoftware/invenio-indexer/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-indexer/issues>`_
  - documentation: `<https://invenio-indexer.readthedocs.io/>`_

  invenio-jsonschemas
  +++++++++++++++++++

  Invenio module for building and serving JSONSchemas.

  - source code: `<https://github.com/inveniosoftware/invenio-jsonschemas>`_
  - releases: `<https://github.com/inveniosoftware/invenio-jsonschemas/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-jsonschemas/issues>`_
  - documentation: `<https://invenio-jsonschemas.readthedocs.io/>`_

  invenio-marc21
  ++++++++++++++

  Invenio module with nice defaults for MARC21 overlay.

  - source code: `<https://github.com/inveniosoftware/invenio-marc21>`_
  - releases: `<https://github.com/inveniosoftware/invenio-marc21/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-marc21/issues>`_
  - documentation: `<https://invenio-marc21.readthedocs.io/>`_

  invenio-oaiserver
  +++++++++++++++++

  Invenio module that implements OAI-PMH server.

  - source code: `<https://github.com/inveniosoftware/invenio-oaiserver>`_
  - releases: `<https://github.com/inveniosoftware/invenio-oaiserver/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-oaiserver/issues>`_
  - documentation: `<https://invenio-oaiserver.readthedocs.io/>`_

  invenio-pidstore
  ++++++++++++++++

  Invenio module that stores and registers persistent identifiers.

  - source code: `<https://github.com/inveniosoftware/invenio-pidstore>`_
  - releases: `<https://github.com/inveniosoftware/invenio-pidstore/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-pidstore/issues>`_
  - documentation: `<https://invenio-pidstore.readthedocs.io/>`_

  invenio-previewer
  +++++++++++++++++

  Invenio module for previewing files.

  - source code: `<https://github.com/inveniosoftware/invenio-previewer>`_
  - releases: `<https://github.com/inveniosoftware/invenio-previewer/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-previewer/issues>`_
  - documentation: `<https://invenio-previewer.readthedocs.io/>`_

  invenio-query-parser
  ++++++++++++++++++++

  Search query parser supporting Invenio and SPIRES search syntax.

  - source code: `<https://github.com/inveniosoftware/invenio-query-parser>`_
  - releases: `<https://github.com/inveniosoftware/invenio-query-parser/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-query-parser/issues>`_
  - documentation: `<https://invenio-query-parser.readthedocs.io/>`_

  invenio-records
  +++++++++++++++

  Invenio-Records is a metadata storage module.

  - source code: `<https://github.com/inveniosoftware/invenio-records>`_
  - releases: `<https://github.com/inveniosoftware/invenio-records/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-records/issues>`_
  - documentation: `<https://invenio-records.readthedocs.io/>`_

  invenio-records-files
  +++++++++++++++++++++

  Invenio modules that integrates records and files.

  - source code: `<https://github.com/inveniosoftware/invenio-records-files>`_
  - releases: `<https://github.com/inveniosoftware/invenio-records-files/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-records-files/issues>`_
  - documentation: `<https://invenio-records-files.readthedocs.io/>`_

  invenio-records-js
  ++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-records-js>`_
  - releases: `<https://github.com/inveniosoftware/invenio-records-js/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-records-js/issues>`_
  - documentation: `<https://www.npmjs.com/package/invenio-records-js>`_

  invenio-records-rest
  ++++++++++++++++++++

  REST API for invenio-records module.

  - source code: `<https://github.com/inveniosoftware/invenio-records-rest>`_
  - releases: `<https://github.com/inveniosoftware/invenio-records-rest/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-records-rest/issues>`_
  - documentation: `<https://invenio-records-rest.readthedocs.io/>`_

  invenio-records-ui
  ++++++++++++++++++

  User interface for Invenio-Records.

  - source code: `<https://github.com/inveniosoftware/invenio-records-ui>`_
  - releases: `<https://github.com/inveniosoftware/invenio-records-ui/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-records-ui/issues>`_
  - documentation: `<https://invenio-records-ui.readthedocs.io/>`_

  invenio-search
  ++++++++++++++

  Invenio module for information retrieval.

  - source code: `<https://github.com/inveniosoftware/invenio-search>`_
  - releases: `<https://github.com/inveniosoftware/invenio-search/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-search/issues>`_
  - documentation: `<https://invenio-search.readthedocs.io/>`_

  invenio-search-js
  +++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-search-js>`_
  - releases: `<https://github.com/inveniosoftware/invenio-search-js/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-search-js/issues>`_
  - documentation: `<https://www.npmjs.com/package/invenio-search-js>`_

  invenio-search-ui
  +++++++++++++++++

  UI for Invenio-Search.

  - source code: `<https://github.com/inveniosoftware/invenio-search-ui>`_
  - releases: `<https://github.com/inveniosoftware/invenio-search-ui/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-search-ui/issues>`_
  - documentation: `<https://invenio-search-ui.readthedocs.io/>`_

  invenio-userprofiles
  ++++++++++++++++++++

  Invenio module that adds userprofiles to the platform.

  - source code: `<https://github.com/inveniosoftware/invenio-userprofiles>`_
  - releases: `<https://github.com/inveniosoftware/invenio-userprofiles/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-userprofiles/issues>`_
  - documentation: `<https://invenio-userprofiles.readthedocs.io/>`_

  Additional feature modules
  ==========================

  The **additional feature modules** offer additional functionality suitable for
  various particular use cases, such as the Integrated Library System, the
  Multimedia Store, or the Data Repository.

  invenio-acquisitions
  ++++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-acquisitions>`_
  - releases: `<https://github.com/inveniosoftware/invenio-acquisitions/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-acquisitions/issues>`_
  - documentation: `<https://invenio-acquisitions.readthedocs.io/>`_

  invenio-annotations
  +++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-annotations>`_
  - releases: `<https://github.com/inveniosoftware/invenio-annotations/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-annotations/issues>`_
  - documentation: `<https://invenio-annotations.readthedocs.io/>`_

  invenio-authorities
  +++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-authorities>`_
  - releases: `<https://github.com/inveniosoftware/invenio-authorities/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-authorities/issues>`_
  - documentation: `<https://invenio-authorities.readthedocs.io/>`_

  invenio-circulation
  +++++++++++++++++++

  Invenio module for the circulation of bibliographic items.

  - source code: `<https://github.com/inveniosoftware/invenio-circulation>`_
  - releases: `<https://github.com/inveniosoftware/invenio-circulation/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-circulation/issues>`_
  - documentation: `<https://invenio-circulation.readthedocs.io/>`_

  invenio-client
  ++++++++++++++

  Command line client for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-client>`_
  - releases: `<https://github.com/inveniosoftware/invenio-client/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-client/issues>`_
  - documentation: `<https://invenio-client.readthedocs.io/>`_

  invenio-comments
  ++++++++++++++++

  Invenio module that adds record commenting feature.

  - source code: `<https://github.com/inveniosoftware/invenio-comments>`_
  - releases: `<https://github.com/inveniosoftware/invenio-comments/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-comments/issues>`_
  - documentation: `<https://invenio-comments.readthedocs.io/>`_

  invenio-communities
  +++++++++++++++++++

  Invenio module that adds support for communities.

  - source code: `<https://github.com/inveniosoftware/invenio-communities>`_
  - releases: `<https://github.com/inveniosoftware/invenio-communities/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-communities/issues>`_
  - documentation: `<https://invenio-communities.readthedocs.io/>`_

  invenio-csl-js
  ++++++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-csl-js>`_
  - releases: `<https://github.com/inveniosoftware/invenio-csl-js/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-csl-js/issues>`_
  - documentation: `<https://www.npmjs.com/package/invenio-csl-js>`_

  invenio-csl-rest
  ++++++++++++++++

  REST API for Citation Style Language styles.

  - source code: `<https://github.com/inveniosoftware/invenio-csl-rest>`_
  - releases: `<https://github.com/inveniosoftware/invenio-csl-rest/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-csl-rest/issues>`_
  - documentation: `<https://invenio-csl-rest.readthedocs.io/>`_

  invenio-github
  ++++++++++++++

  Invenio module that adds GitHub integration to the platform.

  - source code: `<https://github.com/inveniosoftware/invenio-github>`_
  - releases: `<https://github.com/inveniosoftware/invenio-github/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-github/issues>`_
  - documentation: `<https://invenio-github.readthedocs.io/>`_

  invenio-groups
  ++++++++++++++

  Invenio module that adds support for user groups.

  - source code: `<https://github.com/inveniosoftware/invenio-groups>`_
  - releases: `<https://github.com/inveniosoftware/invenio-groups/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-groups/issues>`_
  - documentation: `<https://invenio-groups.readthedocs.io/>`_

  invenio-ill
  +++++++++++

  - source code: `<https://github.com/inveniosoftware/invenio-ill>`_
  - releases: `<https://github.com/inveniosoftware/invenio-ill/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-ill/issues>`_
  - documentation: `<https://invenio-ill.readthedocs.io/>`_

  invenio-memento
  +++++++++++++++

  Invenio module makes your site Memento compliant.

  - source code: `<https://github.com/inveniosoftware/invenio-memento>`_
  - releases: `<https://github.com/inveniosoftware/invenio-memento/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-memento/issues>`_
  - documentation: `<https://invenio-memento.readthedocs.io/>`_

  invenio-metrics
  +++++++++++++++

  Invenio module for collecting and publishing metrics.

  - source code: `<https://github.com/inveniosoftware/invenio-metrics>`_
  - releases: `<https://github.com/inveniosoftware/invenio-metrics/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-metrics/issues>`_
  - documentation: `<https://invenio-metrics.readthedocs.io/>`_

  invenio-migrator
  ++++++++++++++++

  Utilities for migrating past Invenio versions to Invenio 3.0.

  - source code: `<https://github.com/inveniosoftware/invenio-migrator>`_
  - releases: `<https://github.com/inveniosoftware/invenio-migrator/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-migrator/issues>`_
  - documentation: `<https://invenio-migrator.readthedocs.io/>`_

  invenio-oaiharvester
  ++++++++++++++++++++

  Invenio module for OAI-PMH metadata harvesting between repositories.

  - source code: `<https://github.com/inveniosoftware/invenio-oaiharvester>`_
  - releases: `<https://github.com/inveniosoftware/invenio-oaiharvester/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-oaiharvester/issues>`_
  - documentation: `<https://invenio-oaiharvester.readthedocs.io/>`_

  invenio-openaire
  ++++++++++++++++

  OpenAIRE service integration for Invenio repositories.

  - source code: `<https://github.com/inveniosoftware/invenio-openaire>`_
  - releases: `<https://github.com/inveniosoftware/invenio-openaire/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-openaire/issues>`_
  - documentation: `<https://invenio-openaire.readthedocs.io/>`_

  invenio-opendefinition
  ++++++++++++++++++++++

  Invenio module integrating Invenio repositories and OpenDefinition.

  - source code: `<https://github.com/inveniosoftware/invenio-opendefinition>`_
  - releases: `<https://github.com/inveniosoftware/invenio-opendefinition/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-opendefinition/issues>`_
  - documentation: `<https://invenio-opendefinition.readthedocs.io/>`_

  invenio-orcid
  +++++++++++++

  ORCID integration for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-orcid>`_
  - releases: `<https://github.com/inveniosoftware/invenio-orcid/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-orcid/issues>`_
  - documentation: `<https://invenio-orcid.readthedocs.io/>`_

  invenio-pages
  +++++++++++++

  Static pages module for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-pages>`_
  - releases: `<https://github.com/inveniosoftware/invenio-pages/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-pages/issues>`_
  - documentation: `<https://invenio-pages.readthedocs.io/>`_

  invenio-previewer-ispy
  ++++++++++++++++++++++

  Invenio previewer for ISPY visualisations.

  - source code: `<https://github.com/inveniosoftware/invenio-previewer-ispy>`_
  - releases: `<https://github.com/inveniosoftware/invenio-previewer-ispy/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-previewer-ispy/issues>`_
  - documentation: `<https://invenio-previewer-ispy.readthedocs.io/>`_

  invenio-sequencegenerator
  +++++++++++++++++++++++++

  Invenio module for generating sequences.

  - source code: `<https://github.com/inveniosoftware/invenio-sequencegenerator>`_
  - releases: `<https://github.com/inveniosoftware/invenio-sequencegenerator/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-sequencegenerator/issues>`_
  - documentation: `<https://invenio-sequencegenerator.readthedocs.io/>`_

  invenio-sipstore
  ++++++++++++++++

  Submission Information Package store for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-sipstore>`_
  - releases: `<https://github.com/inveniosoftware/invenio-sipstore/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-sipstore/issues>`_
  - documentation: `<https://invenio-sipstore.readthedocs.io/>`_

  invenio-tags
  ++++++++++++

  Invenio module for record tagging by authenticated users.

  - source code: `<https://github.com/inveniosoftware/invenio-tags>`_
  - releases: `<https://github.com/inveniosoftware/invenio-tags/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-tags/issues>`_
  - documentation: `<https://invenio-tags.readthedocs.io/>`_

  invenio-xrootd
  ++++++++++++++

  XRootD file storage support for Invenio.

  - source code: `<https://github.com/inveniosoftware/invenio-xrootd>`_
  - releases: `<https://github.com/inveniosoftware/invenio-xrootd/releases>`_
  - known issues: `<https://github.com/inveniosoftware/invenio-xrootd/issues>`_
  - documentation: `<https://invenio-xrootd.readthedocs.io/>`_

  Standalone utilities
  ====================

  The **standalone utilities** developed for use in the Invenio ecysystem.

  cernservicexml
  ++++++++++++++

  Small library to generate a CERN XSLS Service XML.

  - source code: `<https://github.com/inveniosoftware/cernservicexml>`_
  - releases: `<https://github.com/inveniosoftware/cernservicexml/releases>`_
  - known issues: `<https://github.com/inveniosoftware/cernservicexml/issues>`_
  - documentation: `<https://cernservicexml.readthedocs.io/>`_

  citeproc-py-styles
  ++++++++++++++++++

  CSL styles.

  - source code: `<https://github.com/inveniosoftware/citeproc-py-styles>`_
  - releases: `<https://github.com/inveniosoftware/citeproc-py-styles/releases>`_
  - known issues: `<https://github.com/inveniosoftware/citeproc-py-styles/issues>`_
  - documentation: `<https://citeproc-py-styles.readthedocs.io/>`_

  datacite
  ++++++++

  Python API wrapper for the DataCite Metadata Store API.

  - source code: `<https://github.com/inveniosoftware/datacite>`_
  - releases: `<https://github.com/inveniosoftware/datacite/releases>`_
  - known issues: `<https://github.com/inveniosoftware/datacite/issues>`_
  - documentation: `<https://datacite.readthedocs.io/>`_

  dcxml
  +++++

  Dublin Core XML generation from Python dictionaries.

  - source code: `<https://github.com/inveniosoftware/dcxml>`_
  - releases: `<https://github.com/inveniosoftware/dcxml/releases>`_
  - known issues: `<https://github.com/inveniosoftware/dcxml/issues>`_
  - documentation: `<https://dcxml.readthedocs.io/>`_

  dictdiffer
  ++++++++++

  Dictdiffer is a library that helps you to diff and patch dictionaries.

  - source code: `<https://github.com/inveniosoftware/dictdiffer>`_
  - releases: `<https://github.com/inveniosoftware/dictdiffer/releases>`_
  - known issues: `<https://github.com/inveniosoftware/dictdiffer/issues>`_
  - documentation: `<https://dictdiffer.readthedocs.io/>`_

  dojson
  ++++++

  DoJSON is a simple Pythonic JSON to JSON converter.

  - source code: `<https://github.com/inveniosoftware/dojson>`_
  - releases: `<https://github.com/inveniosoftware/dojson/releases>`_
  - known issues: `<https://github.com/inveniosoftware/dojson/issues>`_
  - documentation: `<https://dojson.readthedocs.io/>`_

  domapping
  +++++++++

  DoMapping generates Elasticsearch mappings from JSON Schemas.

  - source code: `<https://github.com/inveniosoftware/domapping>`_
  - releases: `<https://github.com/inveniosoftware/domapping/releases>`_
  - known issues: `<https://github.com/inveniosoftware/domapping/issues>`_
  - documentation: `<https://domapping.readthedocs.io/>`_

  doschema
  ++++++++

  JSON Schema utility functions and commands.

  - source code: `<https://github.com/inveniosoftware/doschema>`_
  - releases: `<https://github.com/inveniosoftware/doschema/releases>`_
  - known issues: `<https://github.com/inveniosoftware/doschema/issues>`_
  - documentation: `<https://doschema.readthedocs.io/>`_

  flask-breadcrumbs
  +++++++++++++++++

  Flask-Breadcrumbs adds support for generating site breadcrumb navigation.

  - source code: `<https://github.com/inveniosoftware/flask-breadcrumbs>`_
  - releases: `<https://github.com/inveniosoftware/flask-breadcrumbs/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-breadcrumbs/issues>`_
  - documentation: `<https://flask-breadcrumbs.readthedocs.io/>`_

  flask-celeryext
  +++++++++++++++

  Flask-CeleryExt is a simple integration layer between Celery and Flask.

  - source code: `<https://github.com/inveniosoftware/flask-celeryext>`_
  - releases: `<https://github.com/inveniosoftware/flask-celeryext/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-celeryext/issues>`_
  - documentation: `<https://flask-celeryext.readthedocs.io/>`_

  flask-cli
  +++++++++

  Backport of Flask 1.0 new click integration.

  - source code: `<https://github.com/inveniosoftware/flask-cli>`_
  - releases: `<https://github.com/inveniosoftware/flask-cli/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-cli/issues>`_
  - documentation: `<https://flask-cli.readthedocs.io/>`_

  flask-iiif
  ++++++++++

  Flask-IIIF extension provides easy IIIF API standard integration.

  - source code: `<https://github.com/inveniosoftware/flask-iiif>`_
  - releases: `<https://github.com/inveniosoftware/flask-iiif/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-iiif/issues>`_
  - documentation: `<https://flask-iiif.readthedocs.io/>`_

  flask-menu
  ++++++++++

  Flask-Menu is a Flask extension that adds support for generating menus.

  - source code: `<https://github.com/inveniosoftware/flask-menu>`_
  - releases: `<https://github.com/inveniosoftware/flask-menu/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-menu/issues>`_
  - documentation: `<https://flask-menu.readthedocs.io/>`_

  flask-notifications
  +++++++++++++++++++

  - source code: `<https://github.com/inveniosoftware/flask-notifications>`_
  - releases: `<https://github.com/inveniosoftware/flask-notifications/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-notifications/issues>`_
  - documentation: `<https://flask-notifications.readthedocs.io/>`_

  flask-sitemap
  +++++++++++++

  - source code: `<https://github.com/inveniosoftware/flask-sitemap>`_
  - releases: `<https://github.com/inveniosoftware/flask-sitemap/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-sitemap/issues>`_
  - documentation: `<https://flask-sitemap.readthedocs.io/>`_

  flask-sso
  +++++++++

  Flask-SSO extension that eases Shibboleth authentication.

  - source code: `<https://github.com/inveniosoftware/flask-sso>`_
  - releases: `<https://github.com/inveniosoftware/flask-sso/releases>`_
  - known issues: `<https://github.com/inveniosoftware/flask-sso/issues>`_
  - documentation: `<https://flask-sso.readthedocs.io/>`_

  idutils
  +++++++

  Small library for persistent identifiers used in scholarly communication.

  - source code: `<https://github.com/inveniosoftware/idutils>`_
  - releases: `<https://github.com/inveniosoftware/idutils/releases>`_
  - known issues: `<https://github.com/inveniosoftware/idutils/issues>`_
  - documentation: `<https://idutils.readthedocs.io/>`_

  intbitset
  +++++++++

  C-based extension implementing fast integer bit sets.

  - source code: `<https://github.com/inveniosoftware/intbitset>`_
  - releases: `<https://github.com/inveniosoftware/intbitset/releases>`_
  - known issues: `<https://github.com/inveniosoftware/intbitset/issues>`_
  - documentation: `<https://intbitset.readthedocs.io/>`_

  jsonresolver
  ++++++++++++

  JSON data resolver with support for plugins.

  - source code: `<https://github.com/inveniosoftware/jsonresolver>`_
  - releases: `<https://github.com/inveniosoftware/jsonresolver/releases>`_
  - known issues: `<https://github.com/inveniosoftware/jsonresolver/issues>`_
  - documentation: `<https://jsonresolver.readthedocs.io/>`_

  kwalitee
  ++++++++

  Kwalitee is a tool that runs static analysis checks on Git repository.

  - source code: `<https://github.com/inveniosoftware/kwalitee>`_
  - releases: `<https://github.com/inveniosoftware/kwalitee/releases>`_
  - known issues: `<https://github.com/inveniosoftware/kwalitee/issues>`_
  - documentation: `<https://kwalitee.readthedocs.io/>`_

  requirements-builder
  ++++++++++++++++++++

  Build requirements files from setup.py requirements.

  - source code: `<https://github.com/inveniosoftware/requirements-builder>`_
  - releases: `<https://github.com/inveniosoftware/requirements-builder/releases>`_
  - known issues: `<https://github.com/inveniosoftware/requirements-builder/issues>`_
  - documentation: `<https://requirements-builder.readthedocs.io/>`_

  workflow
  ++++++++

  Simple workflows for Python

  - source code: `<https://github.com/inveniosoftware/workflow>`_
  - releases: `<https://github.com/inveniosoftware/workflow/releases>`_
  - known issues: `<https://github.com/inveniosoftware/workflow/issues>`_
  - documentation: `<https://workflow.readthedocs.io/>`_

  xrootdpyfs
  ++++++++++

  XRootDPyFS is a PyFilesystem interface to XRootD.

  - source code: `<https://github.com/inveniosoftware/xrootdpyfs>`_
  - releases: `<https://github.com/inveniosoftware/xrootdpyfs/releases>`_
  - known issues: `<https://github.com/inveniosoftware/xrootdpyfs/issues>`_
  - documentation: `<https://xrootdpyfs.readthedocs.io/>`_
