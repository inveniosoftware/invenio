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

.. _bibindex-admin-guide:

BibIndex Admin Guide
====================

+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| WARNING: BIBINDEX ADMIN GUIDE IS UNDER DEVELOPMENT                                                                                                                                                                                                                                                                                                                                 |
+====================================================================================================================================================================================================================================================================================================================================================================================+
| BibIndex Admin Guide is not yet completed. Most of admin-level functionality for BibIndex exists only in commandline mode. We are in the process of developing both the guide as well as the web admin interface. If you are interested in seeing some specific things implemented with high priority, please contact us at info@invenio-software.org. Thanks for your interest!   |
+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Contents
--------

| **1.\ `Overview <#1>`__**
|  **2. `Configure Metadata Tags and Fields <#2>`__**
|         2.1 `Configure Physical MARC Tags <#2.1>`__
|         2.2 `Configure Logical Fields <#2.2>`__
|  **3. `Configure Word/Phrase Indexes <#3>`__**
|         3.1 `Define New Index <#3.1>`__
|         3.2 `Configure Word-Breaking Procedure <#3.2>`__
|         3.3 `Configure Stopwords List <#3.3>`__
|         3.4 `Configure Stemming <#3.4>`__
|         3.5 `Configure Word Length <#3.5>`__
|         3.6 `Configure Removal of HTML Code <#3.6>`__
|         3.7 `Configure Accent Stripping <#3.7>`__
|         3.8 `Configure Fulltext Indexing <#3.8>`__
|               3.8.1 `Configure Solr Fulltext Indexing <#3.8.1>`__
|  **4. `Run BibIndex Daemon <#4>`__**
|         4.1 `Run BibIndex daemon <#4.1>`__
|         4.2 `Checking and repairing indexes <#4.2>`__
|         4.3 `Reindexing <#4.3>`__
|         4.4 `Solr fulltext indexing <#4.4>`__

1. Overview
-----------

2. Configure Metadata Tags and Fields
-------------------------------------

2.1 Configure Physical MARC Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

2.2 Configure Logical Fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3. Configure Word/Phrase Indexes
--------------------------------

3.1 Define New Index
~~~~~~~~~~~~~~~~~~~~

To define a new index you must first give the index a internal name. An
empty index is then created by preparing the database tables.

Before the index can be used for searching, the fields that should be
included in the index must be selected.

When desired to fill the index based on the fields selected, you can
schedule the update by running **bibindex -w indexname** together with
other desired parameters.

3.2 Configure Word-Breaking Procedure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Can be configured by changing
**CFG\_BIBINDEX\_CHARS\_ALPHANUMERIC\_SEPARATORS** and
**CFG\_BIBINDEX\_CHARS\_PUNCTUATION** in the general config file.

How the words are broken up defines what is added to the index. Should
only "director-general" be added, or should "director", "general" and
"director-general" be added? The index can vary between 300 000 and 3
000 000 terms based the policy for breaking words.

3.3 Configure Stopwords List
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BibIndex supports stopword removal by not adding words which exists in a
given stopword list to the index. Stopword removal makes the index
smaller by removing much used words.

Which stopword list that should be used can be configured in the general
config file file by changing the value of the variable
CFG\_BIBINDEX\_PATH\_TO\_STOPWORDS\_FILE. If no stopword list should be
used, the value should be 0.

3.4 Configure stemming
~~~~~~~~~~~~~~~~~~~~~~

The BibIndex indexer supports stemming, removing the ending of words
thus creating a smaller indexer. For example, using English, the word
"information" will be stemmed to "inform"; or "looking", "looks", and
"looked" will be all stemmed to "look", thus giving more hits to each
word.

Currently you can configure the stemming language on a per-index basis.
All searches referring a stemmed index will also be stemmed based on the
same language.

3.5 Configure Word Length
~~~~~~~~~~~~~~~~~~~~~~~~~

By setting the value of **CFG\_BIBINDEX\_MIN\_WORD\_LENGTH** in the
general config file higher than 0, only words with the number of
characters higher than this will be added to the index.

3.6 Configure Removal of HTML and LaTeX Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you set the **Remove HTML Markup** parameter in the admin interface
to 'Yes' the indexer will try to remove all HTML code from documents
before indexing, and index only the text left. (HTML code is defined as
everything between '<' and '>' in a text.)

If you set the **Remove LATEX Markup** parameter in the admin interface
to 'Yes', the indexer will try to remove all LaTeX code from documents
before indexing, and index only the text left. (LaTeX code is defined as
everything between '\\command{' and '}' in a text, or '{\\command ' and
'}').

3.7 Configure Accent Stripping
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3.8 Configure Fulltext Indexing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The metadata tags are usually indexed by its content. There are special
cases however, such as the fulltext indexing. In this case the tag
contains an URL to the fulltext material and we would like to fetch this
material and index words found in this material rather than in the
metadata itself. This is possible via special tag assignement via
``tagToWordsFunctions`` variable.

The default setup is configured in the way that if the indexer sees that
it has to index tag ``8564_u``, it switches into the fulltext indexing
mode described above. It can index locally stored files or even fetch
them from external URLs, depending on the value of the
**CFG\_BIBINDEX\_FULLTEXT\_INDEX\_LOCAL\_FILES\_ONLY** configuration
variable. When fetching files from remote URLs, when it ends on a splash
page (an intermediate page before getting to fulltext file itself), it
can find and follow any further links to fulltext files.

The default setup also differentiate between metadata and fulltext
indexing, so that ``any field`` index does process only metadata, not
fulltext. If you want to have the fulltext indexed together with the
metadata, so that both are searched by default, you can go to BibIndex
Admin interface and in the Manage Logical Fields explicitly add the tag
``8564_u`` under ``any field`` field.

3.8.1 Configure Solr Fulltext Indexing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Solr can be used to index fulltext and to serve fulltext queries. To use
it, the following steps are necessary:

First, Solr is installed:

    ::

        $ cd <invenio source tree>
        $ sudo make install-solrutils

Second, ``invenio-local.conf`` is amended:

    ::

        CFG_SOLR_URL = http://localhost:8983/solr

Third, Solr is set to index fulltext:

    ::

        UPDATE idxINDEX SET indexer='SOLR' WHERE name='fulltext'

Fourth, Solr is started:

    ::

        <invenio installation>/lib/apache-solr-3.1.0/example$ sudo -u www-data java -jar start.jar

4. Run BibIndex Daemon
----------------------

4.1 Run BibIndex daemon
~~~~~~~~~~~~~~~~~~~~~~~

To index your newly created or modified documents, bibindex must be run
periodically via bibsched. This is achieved by the sleep option (-s) to
bibindex. For more information please see `HOWTO Run <howto-run>`__
admin guide.

4.2 Checking and repairing indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Upon each indexing run, bibindex checks and reports any inconsistencies
in the indexes. You can also manually check for the index corruption
yourself by using the check (-k) option to bibindex.

If a problem is found during the check, bibindex hints you to run
repairing (-r). If you run it, then during repair bibindex tries to
correct problems automatically by its own means. Usually it succeeds.

When the automatic repairing does not succeed though, then manual
intervention is required. The easiest thing to get the indexes back to
shape are commands like: (assuming the problem is with the index ID 1):

    ::

          $ echo "DELETE FROM idxWORD01R WHERE type='TEMPORARY' or type='FUTURE';" | \
            /opt/invenio/bin/dbexec

to leave only the 'CURRENT' reverse index. After that you can rerun the
index checking procedure (-k) and, if successful, continue with the
normal web site operation. However, a full reindexing should be
scheduled for the forthcoming night or weekend.

4.3 Reindexing
~~~~~~~~~~~~~~

The procedure of reindexing is taking place into the real indexes that
are also used for searching. Therefore the end users will feel
immediately any change in the indexes. If you need to reindex your
records from scratch, then the best procedure is the following: reindex
the collection index only (fast operation), recreate collection cache,
and only after that reindex all the other indexes (slow operation). This
will ensure that the records in your system will be at least browsable
while the indexes are being rebuilt. The steps to perform are:

First we reindex the collection index:

    ::

          $ bibindex --reindex -f50000 -wcollection # reindex the collection index (fast)
          $ echo "UPDATE collection SET reclist=NULL;" | \
            /opt/invenio/bin/dbexec # clean collection cache
          $ webcoll -f # recreate the collection cache
          $ bibsched # run the two above-submitted tasks
          $ sudo apachectl restart

Then we launch (slower) reindexing of the remaining indexes:

    ::

          $ bibindex --reindex -f50000 # reindex other indexes (slow)
          $ webcoll -f
          $ bibsched # run the two above-submitted tasks, and put the queue back in auto mode
          $ sudo apachectl restart

You may optionally want to reindex the word ranking tables:

    ::

          $ bibsched # wait for all active tasks to finish, and put the queue into manual mode
          $ cd invenio-0.92.1 # source dir
          $ grep rnkWORD ./modules/miscutil/sql/tabbibclean.sql | \
            /opt/invenio/bin/dbexec # truncate rank indexes
          $ echo "UPDATE rnkMETHOD SET last_updated='0000-00-00 00:00:00';" | \
            /opt/invenio/bin/dbexec # rewind the last ranking time

Secondly, if you have been using custom ranking methods using new
rnkWORD\* tables (most probably you have not), you would have to
truncate them too:

    ::

          # find out which custom ranking indexes were added:
          $ echo "SELECT id FROM rnkMETHOD" | /opt/invenio/bin/dbexec
          id
          66
          67
          [...]
         
          # for every ranking index id, truncate corresponding ranking tables:
          $ echo "TRUNCATE rnkWORD66F" | /opt/invenio/bin/dbexec
          $ echo "TRUNCATE rnkWORD66R" | /opt/invenio/bin/dbexec
          $ echo "TRUNCATE rnkWORD67F" | /opt/invenio/bin/dbexec
          $ echo "TRUNCATE rnkWORD67R" | /opt/invenio/bin/dbexec

At last, we launch reindexing of the ranking indexes:

    ::

          $ bibrank -f50000
          $ bibsched # run the three above-submitted tasks, and put the queue back in auto mode
          $ sudo apachectl restart

and we are done.

In the future Invenio should ideally run indexing into invisible tables
that would be switched against the production ones once the indexing
process is successfully over. For the time being, if reindexing takes
several hours in your installation (e.g. if you have 1,000,000 records),
you may want to mysqlhotcopy your tables and run reindexing on those
copies yourself.

4.4 Solr fulltext indexing
~~~~~~~~~~~~~~~~~~~~~~~~~~

If Solr is used for both fulltext and ranking, only the ``BibRank``
daemon shall run. Since Solr documents can only be overriden and not
updated, the ``BibRank`` daemon also indexes fulltext.
