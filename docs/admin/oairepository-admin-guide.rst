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

.. _oairepository-admin-guide:

OAIRepository Admin Guide
=========================

1. Overview
-----------

The OAI Repository module handles metadata delivery between OAI-PMH
v.2.0 compliant repositories. Metadata exchange is performed on top of
the `OAI-PMH <http://www.openarchives.org/pmh/>`__, the Open Archives
Initiative's Protocol for Metadata Harvesting. The OAI Repository Admin
Interface can be used to set up a database of OAI sources and open your
repository for OAI harvesting.

2. OAI Repository (*Exporting*)
-------------------------------

The OAI Repository corresponds to a set of metadata exposed for
periodical harvesting by external OAI service providers. The following
steps have to be done in order to expose metadata via OAI:

-  Definition of OAI sets
-  Exposing metadata via OAI Repository Gateway

2.1. Definition of OAI sets
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The definition of the OAI sets in the `OAI Repository Admin
Interface </admin/oairepository/oairepositoryadmin.py>`__
lets you choose:

#. which records are to be exposed via OAI, by using the standard
   `Invenio search syntax </help/search-guide>`__.
#. which `OAI
   sets <http://www.openarchives.org/OAI/openarchivesprotocol.html#Set>`__
   are available in your repository. Simply specify the ``setSpec`` and
   ``setName`` of the set.

Let's say you want to expose all the records in the collection
"``Articles``" that have a report number starting with
`hep- </search?f1=reportnumber&c=Articles&p1=hep-*&as=1>`__:
simply add a new set definition in the `OAI Repository Admin
Interface </admin/oairepository/oairepositoryadmin.py>`__,
choose the ``setName`` (Eg: "HEP Articles") and ``setSpec`` (Eg:
"articles:hep"), and fill in the ``collection`` field with "Articles",
the first ``Phrase`` field with "hep-\*" and choose search field "report
number".

If you want to export all the records in your repository, just leave all
the query parameters blank. You can also omit the OAI setSpec and
setName if you do not want to organize your repository into a hierarchy.

If you want to force all the clients currently harvesting a given set
you are exporting (e.g. because you have enriched a metadata export
format) you can simply touch the corresponding set.

Tip: since the exposed records are retrieved using the Invenio search
engine, you can test your query definition in the `advanced search
interface </?as=1>`__ of your repostory.

2.2. Exposing metadata via OAI Repository Gateway
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2.2.1 oairepositoryupdater commmand-line tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the settings of the OAI Repository are defined, the next step is
to expose the corresponding metadata via the OAI Repository Gateway. This is
done by launching the ``oairepositoryupdater`` script, that will add the
OAI identifier and OAI setSpec(s) to the records to be exposed
(according to the settings defined in the OAI Repository admin
interface).

**Oairepositoryupdater usage**

    ::

         oairepositoryupdater [options]

         Options:
           -r --report            OAI repository status
           -d --detailed-report   OAI repository detailed status
           -n --no-process        Do no upload the modifications

         Scheduling options:
           -u, --user=USER       User name to submit the task as, password needed.
           -t, --runtime=TIME    Time to execute the task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26
           -s, --sleeptime=SLEEP Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d
           -P, --priority=PRIORITY       Priority level (an integer, 0 is default)
           -N, --task_specific_name=TASK_SPECIFIC_NAME   Advanced option

         General options:
           -h, --help            Print this help.
           -V, --version         Print version information.
           -v, --verbose=LEVEL   Verbose level (0=min, 1=default, 9=max).

         Print OAI repository status
           $ oairepositoryupdater -r
         Print OAI repository detailed status
           $ oairepositoryupdater -d

**Oaiharvest usage examples**

To expose the sets defined in the OAI Repository Admin Interface and
update them every day:

    ::

         $ oairepositoryupdater -s24

To print out the current status of your OAI repository. Note that this
is a quick report that might not be accurate if you repository is out of
sync. See oairepositoryupdater -d for a more accurate ( but slower)
report:

    ::

        $ oairepositoryupdater -r

To print out the detailed status of your OAI repository:

    ::

        $ oairepositoryupdater -d

Please see also invenio.conf for more detailed configuration of the OAI
Repository.
