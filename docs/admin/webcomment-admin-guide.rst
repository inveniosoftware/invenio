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

.. _webcomment-admin-guide:

WebComment Admin Guide
======================

1. Overview
-----------

WebComment manages all aspects related to comments. From the admin
interface it is possible to check comment statistics as well as manage
comments reported. If the user is authorized for moderation, when
viewing a record special links are displayed to execute actions such as
delete/undelete or unreport comments.

2. Managing WebComment
----------------------

2.1 Viewing comments/review information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From the admin interface it is possible to view statistics related to
the most commented/reviewed records and latest comments/reviews posted.

Depending on the role the user has, it will be possible to view
information related to the collections the user is authorized to.

3. Configuring WebComment
-------------------------

3.1 Configuring moderator per collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration to specify which user is moderator of a given collection
is done through WebAccess administration interface.

In order to permit a given user to be a comment moderator, the following
steps have to be followed:

-  Create a role for the user who is going to moderate (one for each
   moderator)
-  Go to the Action Administration Menu inside of WebAccess admin
   interface
   and assign this role to the action 'moderatecomments'. Specify as
   argument
   the collections allowed for the user.
-  In case you want to give the superadmin user access to all
   collections, follow
   the steps above and write \* as the collection argument.

3.2 Enabling LaTeX/MathJax in comments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to enable LaTeX rendering in comments with the MathJax
module. In order to do that, it is necessary to set the following
directive in the invenio configuration file:

::

    CFG_WEBCOMMENT_USE_MATHJAX_IN_COMMENTS = 1

3.3 Configuring threading
~~~~~~~~~~~~~~~~~~~~~~~~~

Replies to comments can be organized in threads. It is possible to
configure the maximum depth of the threads with the
``CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH`` variable in the
``invenio-local.conf`` file.

Set ``CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH = -1`` to not limit the
depth.

Set ``CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH = 0`` for a "flat"
discussion.

Set ``CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH = 1`` for one-level
deep threads (**default**) etc..

The main advantage of setting a maximum depth is to not enter into deep,
meaningless indentations when users might not understand the concept of
threads, and mix the "reply to" and "add comment" actions. When
``CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH`` is reached, the level of
discussion becomes a "flat" discussion.

For example, with ``CFG_WEBCOMMENT_MAX_COMMENT_THREAD_DEPTH = 1``,
replies to comments would go through to the following states:

State 1

State 2

State 3

State 4

Comment 1

Reply to

Comment 2

Reply to

::

    Reply to
    Comment 1
    -------->

Comment 1

Reply to

**Comment 3**

Reply to

Comment 2

Reply to

::

    Reply to
    Comment 3
    -------->

Comment 1

Reply to

Comment 3

Reply to

**Comment 4**

Reply to

Comment 2

Reply to

::

    Reply to
    Comment 3
    -------->

Comment 1

Reply to

Comment 3

Reply to

Comment 4

Reply to

**Comment 5**

Reply to

Comment 2

Reply to

3.4 Configuring commenting rounds
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can configure WebComment to group comments according to the status
of the commented record. This enables the creation of commenting
*rounds*, so that comments belonging to the same round are grouped
together, and comments belonging to past rounds are less prominently
displayed.

For example, let's say that a collaboration is commenting a draft
document: once a new revision of the document is uploaded by the author,
the already existing comments are grouped together and moved to archive.
The discussion page will then appear empty, and a new commenting round
can start.

The past commenting rounds are still visible as small individual
links at the top of the discussion. A click on one of these links
reveals the comments belonging to this group/round. It is then also
possible to continue replying to comments submitted during this past
round, though it is not possible to add a new comment (not a reply).

::

    > Comments for revision 1
      > Comments for revision 2
        v Comments for revision 3

Great paper. Check typo line 12.

Reply to

Are you sure that figure 5 is ok?

Reply to

Please include the standard logo.

Reply to

::

    New revision
       of file
    ------------>

    >Comments for revision 1
      >Comments for revision 2
      > Comments for revision 3
      v Comments for revision 4


*(blank)*

In order to know what is the current round, the MARC metadata of the
commented record must specify the name of the current group to which new
comments have to be attached. The MARC field specifying the round "name"
can be configured with the ``CFG_WEBCOMMENT_ROUND_DATAFIELD`` of the
``invenio-local.conf`` file. There you can set the MARC code that
contains the round name, for each collection you want to enable rounds.

Note that whatever the current round is, a reply to a comment will
always belong to the round of the parent.

*How to modify the MARC field with the round name?*: this is up to the
admin of the system, but it would typically be done by a WebSubmit
submission. This field might already exists if you store a revision
number in your metadata, or date, etc.

*How to restrict commenting rounds?*: you can combine rounds with the
comment-level restrictions documented in section `Comment-level
restrictions <#3.5.3>`__, which uses a similar mechanism to protect
comments.

3.5 Configuring restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comments restrictions can be configured at several levels, detailed in
the next sections. Note that restrictions applied to comments also apply
to the files attached to comments.

3.5.1 Record-level restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a record is restricted via its collection (``viewrestrcoll``
WebAccess action), the comments submitted for this record are restricted
to users who can view the record.

3.5.2 Discussion-level restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Discussion pages can be restricted with the WebAccess ``viewcomment``
and ``sendcomment`` actions. This let you define who can read or send
comments in particular collections.

3.5.3 Comment-level restrictions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Restrictions can be applied at the level of individual records. When
submitting a comment, WebComment checks in the record metadata if some
restriction should be applied. The field where WebComment is looking for
restrictions can be configured in the the
``CFG_WEBCOMMENT_RESTRICTION_DATAFIELD`` of the ``invenio-local.conf``
file. There you can define for each collection the MARC code containing
the restriction information.

For the restriction to be applied, an authorisation for the
``viewrestrcomment`` WebAccess action must be set up. The "status"
parameter of the ``viewrestrcomment`` must match the value in the MARC
metadata. This lets you define different restrictions based on the value
in the metadata.

Unless the status is empty, the comment will be restricted, even if no
role is specifically linked to the ``viewrestrcomment`` action for this
status.

Note that whatever the status of the record is, a reply to a comment
always inherits the restriction of the parent.

*How to modify the MARC field with the restriction?*: this is up to the
admin of the system, but it would typically be done by a WebSubmit
submission.

3.6 Configuring file attachments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

WebComment allows authorized users to attach files to submitted
comments. This is only available to logged in users, who have been
authorized via the ``attachcommentfile`` WebAccess action. By default no
user (except admin) can attach files.

In addition, you can configure the maximum number of allowed
attachments with the ``CFG_WEBCOMMENT_MAX_ATTACHED_FILES`` (default 5)
variable of the the ``invenio-local.conf`` file. Set
``CFG_WEBCOMMENT_MAX_ATTACHED_FILES = 0`` for unlimited number of files.

Note that this is only applicable only if you installed the jQuery
plugins with ``make install-jquery-plugins``.

You can set up the maximum size (in bytes) of attachments with the
``CFG_WEBCOMMENT_MAX_ATTACHMENT_SIZE`` variable of the the
``invenio-local.conf`` file.

3.7 Configuring email notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

WebComment allows users to subscribe to discussions directly from the
web interface. In addition you can set up automatic notifications that
don't require the users to subscribe. The main use case for this is to
notify the author that a new comment has been submitted on her document.

WebComment checks for automatic notifications of comments in the MARC
record. It specifically looks for emails in fields defined by the
``CFG_WEBCOMMENT_EMAIL_REPLIES_TO`` variable of the the
``invenio-local.conf`` file. There you can define the fields to look for
for specific collections.
