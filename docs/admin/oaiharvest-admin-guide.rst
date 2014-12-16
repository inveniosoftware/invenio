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

.. _oaiharvest-admin-guide:

OAIHarvest Admin Guide
======================


1. Overview
-----------

The OAI Harvest module handles metadata gathering between OAI-PMH
v.2.0 compliant repositories. Metadata exchange is performed on top of
the `OAI-PMH <http://www.openarchives.org/pmh/>`__, the Open Archives
Initiative's Protocol for Metadata Harvesting. The OAI Harvest Admin
Interface can be used to set up a database of OAI sources and open your
repository for OAI harvesting.

2. OAI Data Harvesting
----------------------

In order to periodically harvest metadata from one or several
repositories, it is possible to organize OAI sources through the
`OAI Harvest Admin Interface </admin/oaiharvest/oaiharvestadmin.py>`__.
The interface allows the administrator to add new repositories as well
as edit and delete existing ones. Once defined, run the ``oaiharvest``
command-line tool to start periodical harvesting of these repositories
based on your settings.

(Note that you can **alternatively** use the ``oaiharvest`` command-line
tool to perform a manual harvesting of a repository independently of the
settings in OAI Harvest admin interface, and save the result into a
file. This lets you specify the OAI arguments for the harvesting (verb,
dates, sets, metadata format, etc.). You would then need to run
``bibconvert`` and ``bibupload`` to integrate the harvested records into
your repository. This method can be useful to play with repositories, or
for writing custom harvesting scripts, but it is not recommended for
periodical harvesting. Run ``oaiharvest -h`` for additional
information.)

2.1 OAI Harvest Admin Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Add OAI sources**

The first step requires the administrator to enter the baseURL of the
OAI repository. This is done for validation purposes - i.e. to check
that the baseURL actually points to an OAI-compliant repository. (Note:
the validation simply performs an 'Identify' query to the baseURL and
parses the reply with crucial tags such as ``OAI-PMH`` and
``Identify``).

Once the baseURL is validated, the administrator is required to fill
into the following fields:

-  **Source name**: this will be the (alphanumeric) name used to refer
   to this OAI repository.
-  **Metadata prefix**: upon validation the baseURL is checked for the
   available metadata formats. The administator can choose the desired
   format to harvest metadata in.
-  **Sets**: upon validation the baseURL is checked for the available
   sets of the repository. The administator can choose the desired sets
   to harvest. If none is checked, all records are harvested. Otherwise
   selective harvesting for checked sets is done.
-  **Frequency**: how often do you intend to harvest from this
   repository? (Note: selecting "never" excludes this source from
   automatic periodical harvesting)
-  **Starting date**: on your first harvesting session, do you intend to
   harvest the whole repository (from beginning) or only newly added
   material (from today)? (WARNING: harvesting large collections of
   material may take very long!)
-  **Postprocess**: how is the harvested material be dealt with after
   harvesting? You can choose among several action to be taken after
   harvesting records:

   -  c: convert - harvested metadata will be converted (given
      BibConvert config file) and saved locally - this is useful when
      harvested metadata is in a format different from marcxml (e.g.
      oai\_dc)
   -  r: extract references - attempt to download full-text pdf for each
      record and run refextract to add references to resulting MARCXML
   -  p: extract plots - attempt to download material (like tarballs)
      for each record and extract plots (only from LaTeX sources) to
      attach with FFT to resulting MARXML
   -  t: attach full-text - attempt to download full-text for each
      record and add it as FFT upload in resulting MARCXML
   -  f: filter - useful when you want to filter harvested data in some
      non-trivial way before uploading
   -  u: upload - metadata will be automatically queued for upload (this
      is useful when harvested metadata is already in marcxml format)

   Note: Select none of the above to only harvest records
-  **BibConvert configuration file**: if postprocess involves
   conversion, the filename of an existing BibConvert configuration file
   (or its full path if file is not in standard BibConvert config
   directory) is needed. This file determines how the metadata
   conversion will take place (e.g. oai\_dc to marcxml). In order to
   ensure that the configuration file performs the desired conversion,
   please test it in advance and follow the instruction contained in the
   `BibConvert Admin
   Guide </help/admin/bibconvert-admin-guide>`__.
   Please note that some conversion parameters previously input at the
   command line can now be handled by the BibConvert Configuration
   Language (namely record separator, file header and file footer).
   Please consult the `BibConvert Admin
   Guide </help/admin/bibconvert-admin-guide>`__
   for more information on this. This allows fully automatised
   harvesting and conversion (and possibly upload) of records provided a
   valid, functioning, BibConvert template is provided.
-  **BibFilter program file**: if postprocess involves filtering, the
   full path of an existing BibFilter script is needed. This file
   determines how the harvested records should be filtered. It should
   produce 4 different MARXML outputs:

   -  \*.insert.xml: full records will be uploaded with "-i" parameter,
      new record
   -  \*.append.xml: record snippets will be uploaded with "-a"
      parameter, record additions
   -  \*.correct.xml: record snippets will be uploaded with "-c"
      parameter, record corrections
   -  \*.holdingpen.xml: full records will be uploaded with "-o"
      parameter, to Holding Pen

   Please refer to `BibUpload Admin
   Guide </help/admin/bibupload-admin-guide>`__ for
   more information in BibUpload parameters. In order to ensure that the
   program performs the desired actions, please test it in advance.

**Edit and delete OAI sources**

Once a source has been added to the database, it will be visible in the
overview page, as shown below

+------------+
| name       |
| baseURL    |
| metadatapr |
| efix       |
| frequency  |
| bibconvert |
| file       |
| postproces |
| s          |
| actions    |
+============+
| cds        |
| http://cds |
| .cern.ch/o |
| ai2d       |
| marcxml    |
| daily      |
| NULL       |
| h-u        |
| edit /     |
| delete /   |
| test /     |
| history /  |
| harvest    |
+------------+

At this point it will be possible to edit the definition of this
source by clicking on the appropriate action button. All the fields
described in 2.2.1 can be modified (except for the Starting date). There
is no more validation at this stage, hence, please take extra care when
editing important fields such as baseurl and metadataprefix.

OAI repositories can be removed from the database by clicking on the
appropriate action button in the overview page.

**Testing OAI sources**

This interface provides the possibility to test OAI harvesting settings.
In order to see the harvesting and postprocessing results, administrator
has to provide record identifier (insige the harvested OAI source) and
click "test" button. After doing this, two new frames will appear. The
upper contatins original OAI XML harvested from the source. The second
contains the result of all the postprocessing activities or an error
message.

**Viewing the harvesting history**

This page allows the administrator to see which records have been
recently harvested. All the data is shown in database insertion order.
If there was more than 10 inserted records during a day, only first 10
will be displayed. In order to do manipulations connected with the rest,
the administrator has to proceed to day details page which is available
by "View next entries..." link.

The same page provides the possibility of reharvesting the records
present in the past. All have to be done in order to achieve this is
selecting appropriate records by checking the checkboxes on the right
side of the entry and clicking "reharvest selected records" button.

**Harvesting particular records**

This page provides the possibility of harvesting records manually. The
administrator has to provide an internal OAI source identifier. After this,
record will be harvested, converted and filtered according to the source
settings and scheduled to be uploaded into the database.

2.2 oaiharvest commmand-line tool
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once administrators have set up their desired OAI repositories in the
database through the Admin Interface they can invoke ``oaiharvest`` to
start up periodical harvesting.

**Oaiharvest usage**

    ::

        oaiharvest [options]

        Manual single-shot harvesting mode:
          -o, --output         specify output file
          -v, --verb           OAI verb to be executed
          -m, --method         http method (default POST)
          -p, --metadataPrefix metadata format
          -i, --identifier     OAI identifier
          -s, --set            OAI set(s). Whitespace-separated list
          -r, --resuptionToken Resume previous harvest
          -f, --from           from date (datestamp)
          -u, --until          until date (datestamp)
          -c, --certificate    path to public certificate (in case of certificate-based harvesting)
          -k, --key            path to private key (in case of certificate-based harvesting)
          -l, --user           username (in case of password-protected harvesting)
          -w, --password       password (in case of password-protected harvesting)

        Automatic periodical harvesting mode:
          -r, --repository="repo A"[,"repo B"]   which repositories to harvest (default=all)
          -d, --dates=yyyy-mm-dd:yyyy-mm-dd      reharvest given dates only

        Scheduling options:
          -u, --user=USER   User name under which to submit this task.
          -t, --runtime=TIME    Time to execute the task. [default=now]
                    Examples: +15s, 5m, 3h, 2002-10-27 13:57:26.
          -s, --sleeptime=SLEEP Sleeping frequency after which to repeat the task.
                    Examples: 30m, 2h, 1d. [default=no]
          -L  --limit=LIMIT Time limit when it is allowed to execute the task.
                    Examples: 22:00-03:00, Sunday 01:00-05:00.
                    Syntax: [Wee[kday]] [hh[:mm][-hh[:mm]]].
          -P, --priority=PRI    Task priority (0=default, 1=higher, etc).
          -N, --name=NAME   Task specific name (advanced option).

        General options:
          -h, --help        Print this help.
          -V, --version     Print version information.
          -v, --verbose=LEVEL   Verbose level (0=min, 1=default, 9=max).
              --profile=STATS   Print profile information. STATS is a comma-separated
                    list of desired output stats (calls, cumulative,
                    file, line, module, name, nfl, pcalls, stdname, time).

``oaiharvest`` performs a number of operations on the repositories
listed in the database. By default ``oaiharvest`` considers all
repositories, one by one (this gets overridden when ``--repository``
argument is passed).

For each repository that is considered, ``oaiharvest`` behaves
according to the arguments passed at the command line:

-  If the ``--dates`` argument is not passed, it checks whether an
   update from the repository is needed (Note: the update status is
   calculated based on the time of the last harvesting and the frequency
   chosen by the administrator).

   -  If an update is needed, it harvests all the metadata that the
      repository has added since the data of the last update. When the
      update is finished, the last update value is set to the current
      time and date.
   -  If an update is not needed, the source is skipped.

-  If the ``--dates`` argument is passed, it simply harvests the
   metadata of the repository from/until the given dates. The last
   update date is left unchanged.
-  Finally, it performs the operations indicated in the postprocess
   mode, i.e. convert and/or upload the harvested metadata.


**Oaiharvest usage examples**

In most cases, administrators will want ``oaiharvest`` to run in the
background, i.e. run in sleep mode and wake up periodically (e.g. every
24 hours) to check whether updates are needed:

    ::

        $ oaiharvest -s 24h

In other cases, administrators may want to perform periodical harvesting
only on specific sources:

    ::

        $ oaiharvest -r cds -s 12h

Another option is that administrators may want to harvest from certain
repositories within two specific dates. This will be regarded as a
one-off operation and will not affect the last update value of the
source:

    ::

        $oaiharvest -r cds -d 2005-05-05:2005-05-30

