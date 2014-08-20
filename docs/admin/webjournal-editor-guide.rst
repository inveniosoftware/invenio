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

.. _webjournal-editor-guide:

WebJournal Editor Guide
=======================

Contents
--------

-  **1. `Introduction <#introduction>`__**

   -  1.1  \ `Concepts <#introductionConcepts>`__

-  **2. `Submit an Article <#addArticle>`__**

   -  **2.1 `Using the web HTML editor <#webEditor>`__**
   -  **2.1 `Offline VS online <#offlineVsOnline>`__**

-  **3. `Edit an Article <#editArticle>`__**
-  **4. `Feature a Record <#editArticle>`__**
-  **5. `Preview an Issue <#previewIssue>`__**
-  **6. `Release an Issue <#releaseIssue>`__**

   -  **6.1 `Issue Updates <#issueUpdates>`__**

-  **7. `Send an Alert <#sendAlert>`__**
-  **8. `Regenerate Your Journal <#cache>`__**

   -  **8.1 `Switch Offline articles to Online <#cache-online>`__**

-  **9. `Other Administrative tasks <#adminTasks>`__**

1. Introduction
---------------

WebJournal is a module of Invenio that assists you in publishing an
online journal. This guide should help you get familiar with the tools
offered by WebJournal.

1.1 Concepts
~~~~~~~~~~~~

An **online journal** (managed by WebJournal) is similar to the
widespread "*blogs*\ " systems, with the major difference that articles
of an online journal are grouped by "**issues**\ ": new blog articles
usually push old articles away one after the other, while an online
journal wipes out all the previous articles once a new issue is
**released**.

As an editor of an online journal, you will have the task to release an
issue once all the articles of this issue have been submitted into the
system. The new release becomes the current one and is accessible
online, while the old issue is archived.

Once an issue has been released, you have the possibility to send an
email **alert** to notify your subscribers about the availability of a
new issue. This alert can contain custom text, or embed your journal
homepage (in the manner of a **newsletter**).

**More about the issues:**

Issues of a journal are numbered: ``10/2009``, ``11/2009``, ``12/2009``,
etc. Every new release increments the previous number, and each year the
issue number is reset: ``12/2009``, ``1/2010``, ``2/2010``.

The format of the issue numbers is important ("number/year") as it is
used in WebJournal URLs (in the reverse form). You can therefore not
really go for another format, though you have the possibility to display
it in a different way on the journal page, thanks to customizable
templates.

The number of issues per year should be defined in advance, though it is
possible to have a variable number of issues (the system proposes the
next issue number, but you can choose to override it with your own issue
number). It is even possible to skip issue numbers, though it is not
recommended: ``1/2010``, ``3/2010``, ``5/2010``, etc.

Issues can be **grouped** together to make a "**publication**\ ": this
is typically used when you want to publish an issue every two weeks,
with a small update every second two weeks: Issue ``10/2009`` has brand
new articles, while the next issue ``11/2009`` should feature the same
articles, plus a few new updates.

Issues must be grouped before they are released: you cannot decide to
group the next issue to be released with the latest issue.

When grouping issues, you first release the group as a whole, and
then "update" the group when you thing they are ready. For example you
release the group ``[10/2009, 11/2009]`` the first week: ``10/2009``
becomes the current issue. The next week, you **update** issue
``10/2009``: the publication ``10-11/2009`` becomes the current issue.

**More about the articles:**

The articles submitted to WebJournal are considered as regular
bibliographic records: the same treatment is applied to them, and the
bibliographic tools found in Invenio can be used to manipulate them.

As a consequence WebJournal articles also appear on the regular search
system of Atlantis Institute of Fictive Science. In order for articles
of unreleased issues not to appear on the regular search interface, the
articles are flagged as **offline** until the issue they belong to is
released (the articles are then flagged **online**).

Articles are submitted to specific categories of the journal (if
multiple categories are defined for your journal), and are assigned a
unique identifier: both attributes are visible in the URLs when
selecting an article. It is then easy to build links to an article. The
article identifier also corresponds to the identifier of the entry in
Atlantis Institute of Fictive Science.

2. Submit an Article
--------------------

To submit an article, go to the `regular submission page </submit>`__,
and choose the category corresponding to your journal.

(This can vary depending on how the administrator configured the
system).

It is at submission time that you have to decide what issue(s) this
article is to be part of (this can be modified later by editing the
article). If you use "grouped issues", you have to specify that the
article belong to each individual issue of the group.

Note that a small delay exists between the time an article is submitted
and the time it appears online.

2.1 Using the web HTML editor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Depending on how the administrator configured the system, you might be
given the possibility to write your articles online as if you were
editing them from a desktop text editor. If you have already used such a
tool, you should feel at home with the provided editor.

This editor translates your articles into HTML markup, ready for
displaying in a web browser. You therefore do not need to know how to
write HTML code, but you should be aware of a few consequences due to
online publishing. Here is a list of best practices when using the
online HTML editor:

-  You can copy-paste text from other editors. Note that the formatting
   (font, color, size) might not be kept correctly in some cases. If you
   copy-paste text from Microsoft Word, please use the dedicated
   "Word-text cleaner" button of the toolbar.
-  If you want to paste styled text but you do not want to keep its
   style, use the dedicated "Text cleaner" button of the toolbar.
-  Pasting text from your own machine that contains images (or any
   multimedia content) will not paste the images, but just the text. To
   have your images, you must first upload them to the server using the
   "Image" button of the toolbar, and click on the "Upload" tab.
-  Do not upload big images: they might take a long time to load in your
   readers' browsers. WebJournal will usually try to scale down the
   images, but you would achieve better effect by first reducing them
   using a dedicated image processing application.
-  If you want to display images that already exist online, you do not
   need to download them and re-upload them: you can simply link them
   ("Image" button of the toolbar, link to the image).
-  Try not to use custom styles (colors, font, size): you should
   restrict to a layout and styles that have a semantic meaning for your
   article (paragraphs, [STRIKEOUT:stroked text], *italics*, header,
   etc.) and let WebJournal applies the corresponding styles: that will
   ensure a consistent look of all the articles over time, and will make
   possible future re-styling of your journal, even of your past issues.
-  You can view the source of the produced HTML, if you need to apply
   specific modifications that are unsupported by the online editor (for
   eg. linking to a video).

2.2 Offline VS Online
~~~~~~~~~~~~~~~~~~~~~

Depending on how the system was configured by the administrator, you
might be given the choice to have your article offline or online when
adding or editing it:

Offline
    The article is not visible on the regular search interface of
    Atlantis Institute of Fictive Science until the issue has been
    released
Online
    The article is immediately visible on the regular search interface
    of Atlantis Institute of Fictive Science. You should use this option
    if you want to add an article to an already released issue
    (otherwise the article will never be visible on the regular search
    interface).

3. Edit an Article
------------------

You can edit articles in same way as you add articles: you just have
to go to the `regular submission page </submit>`__
and provide the article number you want to modify. If you are logged in
as editor of the journal, you should also see a direct link to edit the
article from the main article page of your journal.

(This can vary depending on how the administrator configured the system).

4. Feature a Record
-------------------

Depending on your journal configuration, you might be given the
possibility to feature on your main journal page records (photos,
videos, etc) found on Atlantis Institute of Fictive Science.

To feature a record, go to you journal `administration
page </admin/webjournal/webjournaladmin.py>`__, and
choose "Feature a record". You must then provide the identifier of the
record you want to feature, as well as the URL of the image you want to
associate to the record. On the very same page you can remove featured
records.

Note that featured records are independent of releases: you can update
them whenever you want.

5. Preview an Issue
-------------------

To preview an issue, go to your journal `administration
page </admin/webjournal/webjournaladmin.py>`__, and
select the "edit" link of the category you want to preview.

You can also preview any issue of your journal by specifying the correct
issue number in your journal URL. In that case, make sure you are logged
into `Atlantis Institute of Fictive Science <http://localhost:4000>`__,
otherwise you will not be able to access the unreleased issue.

6. Release an Issue
-------------------

To release an issue, go to your journal `administration
page </admin/webjournal/webjournaladmin.py>`__, and
select "Release now". You should then be given the choice of the issue
number to release. By default the next issue number is selected, but you
can decide to:

-  Add a higher issue number to create a `grouped
   issue <#groupedIssue>`__ ("publication")
-  Add a higher issue number and deselect the suggested one to skip the
   release of the suggested issue number.
-  Add a custom issue number (Eg. the system suggest you issue number
   ``52/2008``, but you want to jump to ``01/2009``)

You can group as many issue as you want. Only the selected issue
number(s) will be published. Click on the "Publish" button once done.

Depending on the configuration set by your administrator, when an issue
is released, any article still marked as "Offline" for this issue is
switched to "Online" to ensure consistency between the journal view and
Atlantis Institute of Fictive Science. Read more about `Offline/Online
articles <#offlineVsOnline>`__. You also have the possibility to mark
"Online" any further set of articles added for this issue by
`regenerating the issue <#cache-online>`__ and ticking the adequate
checkbox.

6.1 Issue Updates
~~~~~~~~~~~~~~~~~

We call **issue update** the action of releasing an individual issue of
a grouped issue ("publication"). Eg. you grouped issues
``[15/2009, 16/2009]``: releasing issue ``16/2009`` is an update to the
publication ``15-16/2009``

If you have previously grouped some issues, you first have to publish
the pending one before releasing a completely new issue. Eg. you want to
release issue ``17/2009`` but you had previously grouped the issues
``[15/2009, 16/2009]``, without releasing issue ``16/2009``: you first
have to release the pending update ``16/2009`` before you can release
``17/2009``.

If you just want to add an article to an already released issue without
using grouped issues, simply submit your article for this issue, and
`update the cache <#cache>`__. (If necessary note that you can either
mark the article as "Online" when submitting it, or by ticking the
adequate checkbox when `regenerating the issue <#cache-online>`__. Read
more about `Offline/Online articles <#offlineVsOnline>`__)

7. Send an Alert
----------------

To send an alert about a new issue, go to your journal `administration
page </admin/webjournal/webjournaladmin.py>`__, and
click on the "send alert" link for the issue you want to send the alert.

Update the recipients address and the text of the alert if needed.

If you keep the box "Send journal front-page" checked, your
subscribers will receive the front page of your new release by email. If
you uncheck this box (or if your subscribers have configured their email
clients to not display HTML emails) the textual version of the alert
will be shown instead.

Note that you can only send an alert for an issue that has been already
released, and that you will be warned if you try to send an alert that
has already been sent for a past issue.

8. Regenerate Your Journal
--------------------------

In order to optimize the display speed of the journal for your readers,
the WebJournal module creates static versions of your journal. These
static pages need to be recreated if you update the journal after it has
been released.

To do so, go to your journal `administration
page </admin/webjournal/webjournaladmin.py>`__, and
click on the "regenerate" link of the issue you want to update.

8.1 Switch Offline articles to Online
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When regenerating the cache of a journal issue you have the possibility
to switch all the articles still marked as "Offline" (i.e. drafts) to
"Online" (similarly to what is taking place when releasing an issue).
Tick the corresponding checkbox if you which so. Note that the box is
disabled if trying to re-generate the cache for an issue unreleased yet.

Read more about `Offline/Online articles <#offlineVsOnline>`__.

9. Other Administrative tasks
-----------------------------

Administrative tasks such as adding or removing a journal, editing its
layout and settings have to be performed by an administrator-level user.

Please refer to `WebJournal Admin
Guide </help/admin/webjournal-admin-guide>`__.
