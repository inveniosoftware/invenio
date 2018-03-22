..
    This file is part of Invenio.
    Copyright (C) 2017-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

System architecture
===================


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
