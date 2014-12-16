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

.. _webjournal-admin-guide:

WebJournal Admin Guide
======================

Contents
--------

-  **1. `Introduction <#introduction>`__**
-  **2. `Add a Journal <#addJournal>`__**
-  **3. `Configure a Journal <#configureJournal>`__**
-  **4. `Sitemap of a Journal <#journalSitemap>`__**
-  **5. `Edit the Layout of a Journal <#journalLayout>`__**

   -  5.1  \ `Edit Format Elements - Best
      Practices <#editJournalElement>`__

   -  5.2  \ `Alert layout - Best Practices <#editJournalAlertLayout>`__

-  **6. `Submit Articles <#addArticles>`__**

   -  6.1  \ `Draft/Unreleased/Offline Articles <#draftArticles>`__
   -  6.2  \ `Preview Unreleased Issues <#draftPreview>`__

-  **7. `Access Control <#accessControl>`__**

   -  7.1  \ `Articles Submission <#accessControlSubmit>`__
   -  7.1  \ `Issue Control System <#accessControlIssue>`__

-  **8. `Troubleshoots <#troubleshoots>`__**

   -  8.1  \ `Update Cache <#updateCache>`__
   -  8.1  \ `Manage Issue Releases <#issueReleases>`__

1. Introduction
---------------

This guide shows how you can set up a new journal managed by the
Invenio WebJournal module. You should first read the `WebJournal
Editor Guide <webjournal-editor-guide>`__ to get an overview of the main
concepts of this module.

2. Add a Journal
----------------

To add a journal, go to the WebJournal admin interface and click "Add
new journal". Provide the name of your journal, and edit the
`configuration <#configureJournal>`__ of the journal. Click "Save".

**Note that by default your Apache user should not be able to save the
configuration** since it should not have rights to write to
``/opt/invenio/etc/webjournal/``. To save the settings you might want to
manually save your configuration to
``/opt/invenio/etc/webjournal/yourJournalName/yourJournalName-config.xml``
or give write permission to ``/opt/invenio/etc/webjournal/``

Usually adding a journal also requires to set up a dedicated submission,
give some access using WebAccess, and can optionally lead to the
creation of WebSearch collections (you can, but you don't have to, map
your journal categories to WebSearch collections. You can also simply
create a generic collection for all articles in all categories of your
journal, or don't create collections at all). See the section dedicated
to `articles submission <#addArticles>`__.

3. Configure a Journal
----------------------

You can either configure the journal from the admin web interface or
directly by editing the configuration file (see `above
note <#journalConfigurationWritePermission>`__).

The configuration consists in an XML file with the following nodes:

-  view

   -  **niceName**: The name of your journal as displayed on your
      journal pages
   -  **niceURL**: *(not yet used)*
   -  css

      -  **screen**: relative path to your journal CSS file.
      -  **print**: same as **screen**, but used when your users want to
         print your journal

   -  format\_template

      -  **index**: format template of your journal `index
         page <#sitemapIndex>`__
      -  **detailed**: format template of your journal `article
         page <#sitemapDetailed>`__
      -  **search**: format template of your journal `search/archives
         page <#sitemapSearch>`__
      -  **contact**: format template of your journal `contact
         page <#sitemapContact>`__
      -  **popup**: format template of your journal `"pop-up article"
         page <#sitemapPopup>`__

-  model

   -  record

      -  **rule\***: defines the categories of the journal, and the
         query matching articles of this category. Format:
         ``categoryName, query``. The journal categories are not
         necessary mapped to Invenio collections (but they can be, for
         consistency)

-  controller

   -  **issue\_grouping**: the default number of issues that are
      released together when grouping issue. Specify ``1`` if your
      release are not usually grouped.
   -  **issues\_per\_year**: number of expected issues per year. Helps to
      anticipate next issue dates and number.
   -  **hide\_unreleased\_issues**: if all unreleased issue should be
      hidden to readers, type "``all``\ " (recommended). If only future
      unreleased issues must be hidden to readers, type "``future``\ ".
      If unreleased issues must always be accessible to everyone (even
      if displayed empty), use "``none``\ ". Hidden issues are only
      visible to users who can access action "``cfgwebjournal``\ ").
   -  marc\_tags

      -  **issue\_number**: *(not yet used. Should correspond to field
         containing issue number. Now hardcoded to 773\_\_n)*
      -  **order\_number**: *(not yet used. Should correspond to field
         containing article order. Now hardcoded to 773\_\_c)*

   -  **alert\_sender**: email displayed as sender when sending journal
      newsletter
   -  **alert\_recipients**: default list of recipients emails
      (comma-separated) when sending journal newsletter
   -  **languages**: comma-separated list of languages enabled for this
      journal (you should have an article in *each* of these languages)
   -  submission :

      -  **doctype**: the doctype of the submission used to edit record.
         Used to provide journal editors a direct link to submission
         from an article
      -  **identifier\_element**: the WebSubmit element name where the
         submission expects to get the report number of the article to
         edit.
      -  **identifier\_field**: the MARC field on which the submission
         should rely to retrieve the article (identifier to use to
         prefill the *identifier\_element* input field when using
         ``CFG_SITE/submit/direct`` URLs).

   -  **draft\_keyword**: keyword that will be removed from some fields
      of the records of the issue to be released: that is used to
      automatically "publish" records tagged as draft.
   -  **first\_issue**: The first issue number to be ever published for
      this journal: this is only needed at the beginning, in order for
      WebJournal to know what should be the first issue number (Eg. if
      it starts in the middle of the year with a different number than
      ``01``)
   -  **draft\_image\_access\_policy**: '``allow``\ ' or '``deny``\ '
      (default): if we should allow or not (default) access to images
      and files attached to an article even if this article is still
      part of a restricted collection: this allows to workaround the
      time required for an article to appear in a public collection
      after an issue has been released. Access is still forbidden if the
      article does not belong to a released issue, but at least default
      authorizations of the record do not apply.

*\* Means repeatable*

4. Sitemap of a Journal
-----------------------

A journal typically contains the following sections, each generated
using a different template (as defined in your journal configuration):

-  **Index**
   The main page of a journal, containing links to detailed articles.
   Correspond to a given journal, issue and category (by default the
   first category of the latest issue of the journal).
   Accessible at ``http://yourSite/journal/yourJournalName/`` or for a
   specific issue and/or category at
   ``http://yourSite/journal/yourJournalName/year/number/category``
   When ``yourJournalName`` is not provided, the user is automatically
   redirected to the latest issue of your journal. If there are several
   journals available, he is offered a list of journals to choose from.
   When **category** is missing, the first category defined for your
   journal is used. When ``/year/number/`` are missing, the latest issue
   is chosen.
-  **Detailed**
   The page of a single article, in a given category, issue and
   journal.
   Accessible at
   ``http://yourSite/journal/yourJournalName/year/number/category``/**recID**
-  **Search**
   Used for search or access to past issues of a journal
   Accessible at
   ``http://yourSite/journal/``\ search?name=\ ``yourJournalName``
-  **Contact**
   Information about the journal
   Accessible at
   ``http://yourSite/journal/``\ contact?name=\ ``yourJournalName``
-  **Popup**
   Information about the journal
   Accessible at
   ``http://yourSite/journal/``\ contact?name=\ ``yourJournalName``

5. Edit the Layout of a Journal
-------------------------------

The WebJournal module relies on the BibFormat module to generate its
output. You should then already be familiar with its concepts before
reading further. In a few words, you edit the templates of a journal
using HTML, and use special tags for the dynamic parts (navigation menu,
article title, content, etc) of the layout.

The main differences between the use of BibFormat for journals compared
to BibFormat for the formatting of bibliographic records are:

-  Output formats are not used: format templates are directly called
   based on your journal configuration (your configuration *acts* like a
   basic output format)
-  A format template takes care of the full layout of your page: it
   should therefore include the ``tags   <html>``, ``<header>``,
   ``<body>``, etc.
-  Format templates are saved to
   ``/opt/invenio/etc/bibformat/format_templates/webjournal/``.
-  In general, format elements (*in Python*) cannot rely on the ``bfo``
   parameter passed to their ``format(bfo,   ...)`` function to access
   the articles metadata: format elements are not only used in the
   context of a single record/article, but can be used to format several
   records/articles at the same time. A notable exception is in the case
   of template used for the ``article`` page.

5.1 Editing Format Elements - Best practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As said above, WebJournal format elements are not used only to format a
single article/record: they are used as a generic way to provide dynamic
content to your journal, such as the main navigation menu containing the
categories defined for your journal, or a dynamically updated weather
forecast section. As a consequence you should not use the ``bfo`` object
of the ``format_element(bfo, ...)`` function to access the articles
metadata, as it does not correspond to a record (see exceptions further
below). You can however use it to access knowledge bases and user
information.

In order to access the context of the page, you should use the
``parse_url_string(bfo.user_uri['uri'])`` function, which returns a
dictionary with the keys and values:

-  ``journal_name``: the name of the journal as shown in the URLs, and
   generally used as parameter to other functions, as ``string``
-  ``category``: the currently displayed category as ``string``
   (Default: first category)
-  ``issue``: the issue number in the form "08/2007" as ``string``
   (Default: current issue)
-  ``issue_number`` and ``issue_year``: same as ``issue``, but split by
   component, as ``integer``
-  ``recid``: the displayed article ID as ``integer`` (Default: ``-1``)
-  ``verbose``: verbosity, as ``integer`` (Default: ``0``)
-  ``ln``: the language that should be used to display the page, as
   ``string`` (Default: preferred language or ``CFG_SITE_LANG``)
-  ``archive_year``: the year selected on the archive/search page, if
   any, as ``integer`` (Default: ``None``)
-  ``archive_search``: the pattern used on the archive/search page, as
   ``string`` (Default: empty ``string``)

::

    from invenio.legacy.webjournal.utils import parse_url_string

    def format_element(bfo):
        args = parse_url_string(bfo.user_info['uri'])
        journal_name = args['journal_name']
        category = args['category']
        ln = args['ln']
        ...

These values remain empty if they do not make sense in the context. For
example, the recid value will be empty when displaying an index page: we
are not displaying a specific article.

**Note** the difference between ``bfo.lang`` and the "``ln``\ " value
returned by ``parse_url_string(..)``: the former represents the
user-chosen language on your Invenio installation, while the latter is
the more appropriate language to display the journal, based on the
languages defined in your journal configuration file. Propagate
``bfo.lang`` through links, but display your article/interface using the
value returned by ``parse_url_string(..)``.

Other WebJournal helper functions for format elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``webjournal_utils.py`` file contains several functions that should
help you work with the WebJournal module. Please refer to this file for
the list of available functions.

5.2 Alert HTML layout - Best practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The HTML "alert" (or newsletter) is sent based on the homepage ("Index"
format template) of the journal of a specific issue. In order to
maximize the chances for the newsletter to display correctly in the
recipients mail clients, the linked CSS files are embedded into the
source of the email. Because of the very varying level of support for
HTML in mail clients (including web-based ones) you should check that
the markup of your pages will be adequate for your targeted readers, and
simply the markup if necessary.

You can include some specific markup in your "index" format template to
define areas that should not be sent as part of the newsletter. Use
``<!--START_NOT_FOR_ALERT-->`` to mark the beginning of an area that
should not be included in the newsletter, and
``<!--END_NOT_FOR_ALERT-->`` to mark the end of such area.

6. Submit Articles
------------------

Journal articles are nothing more than regular records having some
specific MARC fields. Hence they should be entered into the system like
any other record: provide a submission to your journal editors, or input
MARCXML using BibUpload. Have a look at the `metadata
requirements </help/hacking/webjournal-record-metadata>`__
of a WebJournal record.

6.1 Draft/Unreleased/Offline Articles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since articles are just regular records, you should ensure that your
readers do not have access to these records before the issue they belong
to is released. Indeed, even though the articles can be hidden from the
journal interface (depending on the value of the configuration variable
**hide\_unreleased\_issues**), they are still accessible from the
standard Invenio interface (the CDS Invenio search/browse interface is
independent from the WebJournal Module, as the WebJournal interface is
independent from the CDS Invenio search/browse interface)

In order to deal with unreleased articles, you can prepare a submission
that can change some field of a record to flag it as "*draft*\ " or
"*offline*\ " when necessary. These draft records should go to a
restricted "Drafts" collection that only editors can see. Just before
the issue is ready to be released, the editor can remove the "Draft"
flag from each article.

A suggested setting is to map each category of your journal to both a
public and a restricted WebSearch collections. For example, your "sport"
category may have a public "Sport" collection, and a restricted
"Restricted Sport" collection. Your submission would for example
flag/unflag the "Draft" by changing the collection field ``980__a``
based on the parameter of the submission: ``980__a:myJournalSportDraft``
<-> ``980__a:myJournalSportDraft``.

One of the drawbacks of this solution is that each article has to be
manually "approved" *just before* releasing the issue. A workaround is
to set your journal configuration variable **remove\_keyword** to value
"``DRAFT``\ ": that tells WebJournal to remove all occurrences of this
keyword from the articles when a new issue is released. You then no
longer have to take care of manually remove the "draft" flag from all
these articles.

Note that this technique applies only to *all* articles of the
*released issue*, but that the following tags are not affected by this
removal: ``100``, ``245``, ``246``, ``520``, ``590`` and ``700``. You
should therefore carefully choose your keyword so that it does not
interfere with other values of your record.

6.2 Preview Unreleased Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By tweaking the URL, you can access the desired journal issue. Even if
the unreleased issue is hidden to users, editors should be allowed to
access it (See `Issue Control System <#accessControlIssue>`__ section).

7. Access Control
-----------------

7.1 Articles Submission
~~~~~~~~~~~~~~~~~~~~~~~

Since submission is performed using WebSubmit, you can apply the
standard procedures to restrict submissions of records.

7.2 Issue Control System
~~~~~~~~~~~~~~~~~~~~~~~~

You can restrict access to the issue control system by using the
"``cfgwebjournal``\ " WebAccess action. This action takes the journal
name as parameter in order to restrict access to selected journal(s)
only. A second parameter "``with_editor_rights``\ " must be set to "yes"
in order for the authorized roles to edit apply changes using the
interface (including sending alerts, releasing issues, etc.)

Note that this action also lets your editors change your journal
configuration file (unless the file is protected on disk, which is
recommended).

8. Troubleshoots
----------------

8.1 Update Cache
~~~~~~~~~~~~~~~~

WebJournal makes heavy use of caches in order to optimize the serving
speed. Journal editors can regenerate the journal cache, but it does not
apply to old issues, or cache that has been generated by some widgets.
To clean the cache, remove the files in
``/opt/invenio/var/cache/webjournal/``\ **yourjournal**. Cached files
starts with ``issue_year``, followed by the ``category`` so that it is
easy to remove the caches for a specific issue/section. Examples:

::

      $ rm /opt/invenio/var/cache/webjournal/AtlantisTimes/07_2009_*
      $ rm /opt/invenio/var/cache/webjournal/AtlantisTimes/07_2009_index_News*

You might want to remove some other specific files created by some
widgets, for example:

::

      $ rm /opt/invenio/var/cache/webjournal/AtlantisTimes/weather.html

8.2 Manage Issue Releases
~~~~~~~~~~~~~~~~~~~~~~~~~

Issues are usually managed by the journal editors, using the web
interface. You might have to help your editors if they released an issue
by mistake, or created. Have a look at the `WebJournal Table
Structure </help/hacking/webjournal-table-structure>`__
hacking guide to find out how you can easily update entries in the
WebJournal tables.
