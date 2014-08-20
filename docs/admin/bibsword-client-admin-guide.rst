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

.. _bibsword-client-admin-guide:

BibSword client Admin Guide
===========================

1. Overview
-----------

BibSword client enables you to forward a record from Invenio to any
remote server that has an interface implementing the SWORD protocol. The
aim of the BibSword client module is to simplify and to speed up the
submission process of a digital report. Basically, the fulltext and the
metadata are automatically taken from the record stored in Invenio. For
more flexibility, they can be manually added and modified during the
forwarding process.

1.1 Remote authentication
~~~~~~~~~~~~~~~~~~~~~~~~~

For reasons of conveniency, it is annoying to ask a user who is already
authencticated in Invenio to log in a remote server before forwarding a
record. This problem is solved by using the "mediated deposit" function
described by the SWORD protocol specification.

The mediated deposit function allows any user to forward a document in
the name of the author. The solution was then to create a global user account
that is always used to connect to the remote server. This user submits
the record "on behalf of" the real author of the file. So the user does
not even need to have an account on the remote server.

Because of this function, users are allowed to submit what they want as
long as they know the global user. To prevent users from doing anything
they want, access of the BibSword client module is restricted to a group
of user named "bibsword\_curator". However, users can forward their own
record through the WebSubmit workflow that already manages the record
access rights.

1.2 Forwarding status
~~~~~~~~~~~~~~~~~~~~~

When a record is forwarded to a remote SWORD server, it goes through
several well-defined states:

#. submitted: the record is waiting for approval
#. published: the record has been approved and is published
#. unknown: the record has been refused or has never been submitted

For each state, an information is stored on the MARC file of the
submitted record:

-  submitted: an information field (by default the '595\_\_a' tag) is
   added. It contains information about the time and the user having
   done the submission but also the remote id given by the SWORD server
   for the record.
-  published: the remote id is added to the MARC file as an additionnal
   record id (by default the '088\_a' tag).
-  unknown: the record has been refused by the remote server or a
   problem occured during the submission. In this case, the information
   field (by default the '595\_\_a' tag) and the additional record id
   field (by default the '088\_a' tag) are removed.

1.3 Forwarding options
~~~~~~~~~~~~~~~~~~~~~~

By default, the BibSword client sends the fulltext and the metadata stored in
Invenio.

It also allows to select the fulltext to forward and even to upload a new
fulltext. If a new fulltext is uploaded, it is stored in the Invenio
record fulltext as a "Pushed\_via\_Sword" file.

2. BibSword client : Admin Web Interface
----------------------------------------

To access the Admin Web interface, please go to `BibSword Client Admin
Interface </bibsword>`__. Note that you first have
to be logged with a user of the group "bibSword\_curator".

This interface allows to:

-  Consult information about the forwarded records
-  Refresh the status of the forwarded records on the remote server
-  Forward any record to any available SWORD remote server.

2.1 Submission state
~~~~~~~~~~~~~~~~~~~~

The main BibSword Admin Interface shows a table containing information
about every forwarded record.

Submission state table fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------+--------------------------+--------------------------+
| Field                    |                          |                          |
| Definition               |                          |                          |
| Link                     |                          |                          |
+==========================+==========================+==========================+
| Remote server            | Submitter                | Report number            |
| id and name of the       | username and email of    | database id and report   |
| remote server where the  | the user that made the   | number of the forwarded  |
| record has been          | submission               | record                   |
| submitted                | None                     | Go to the record         |
| Go to the information    |                          | information page on      |
| table where to find      |                          | Invenio                  |
| credential and link to   |                          |                          |
| the remote server        |                          |                          |
+--------------------------+--------------------------+--------------------------+

The records are displayed in the order of change of their state. The most recent
change first and the older changes last. To see records which are not
displayed, navigate between pages using the "Prev" - "Next" and
the "First" - "Last" buttons.

You can also select a different number of records displayed per
page by changing the displayed record number.

2.2 Refresh forwarded record status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each time the submission state table is loaded, the BibSword client
module checks each displayed record with the "submitted" status to see if
their status has been changed to "published" or to "removed".

To minimize table loading time, the default number of displayed
records is set to 10. However it is possiblie to select a different number of
displayed fields. (5 - 10 - 25 - 50 - all)

In some unusual cases, a "published" record can be removed from the
SWORD remote server. In this case, the status of the submitted record is
not automatically updated. To update "published" record, click the
"Refresh all" button. It will check the status of every forwarded record
on each remote server.

2.3 Setting up a record forwarding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The forwarding of a record from the admin interface is done through four
different forms. Each of them has a precise purpose and is generated
dynamically according to the record and the remote server information.

#. Select the record and the remote server
#. Select the remote server collection
#. Select the remote server categories
#. Check, add, modify and/or delete media and metadata to be forwarded

To forward a record, click the "New Submission" button from the
BibSword Admin Interface.

Alternatively, you can access the SWORD forward interface from any
record information page by clicking the "Push to *Remote Server*"
located on the toolbar bellow the record information box. Note that in
this case, you are directly redirected to step two of the forward
process.

**Step 1/4: Select record and remote server**

The form has the following fields:

-  **Report number:** specify the record to forward, enter its report
   number (e.g: *PUPT-1665*)
-  **Remote server:** specify the remote server where to forward the
   record, select it in the dropdown list

Both fields are mandatory. If you forget one of them or if you give an
nonexistient report number, an error message will be displayed and you
will be invited to give all information correctly.

You can abort the submission by pushing the "cancel" button and be
redirected to the BibSword Admin Interface.

**Step 2/4: Select the remote server collection**

The second step displays information about the selected remote server as
well as the implemented version of SWORD and the maximum size of file to
forward. At this point, it is possible to modify the remote server and
the record by pushing "Modify server".

The pupose of this step is to select the remote collection. The
collection contains the URL where to sent information to the remote
server.

The form has the following fields:

-  **Remote collection:** specify the collection in the dropdown list.

Most of the remote servers have a collection called "test". This
collection is very useful to check the correct function of the
implementation of a remote server. When a record is sent to the "test"
collection of a remote server, the SWORD remote interface will act
exactly the same as with a normal forward but without to save the
record.

You can abort the submission by pushing the "Cancel" button and be
redirected to the BibSword Admin Interface.

**Step 3/4: Select Remote Categories**

The third step displays information about the Remote Server as well as
information concerning the selected collection. At this point, it is
possible to modify the remote server and the record by pushing "Modify
server". It is also possible to modify the selected Remote Collection by
pushing "Modify collection".

This step allows to select remote categories. Categories are used for
two purposes:

-  Specify the exact place where the record will be stored in the remote
   server
-  Specify all the topics related to the record for easy
   localisation of the record

The form has the following fields:

-  **Mandatory category:** Select the specific topic of the record for
   the collection from the dropdown list
-  **Optional categories:** Select all categories related to the record
   from the multiple choice list (CTRL+CLICK to select many)

If you forget to select a mandatory category, a message will be displayed
and you will be invited to give a mandatory category.

You can abort the submission by pushing the "Cancel" button and be
redirected to the BibSword Admin Interface.

**Step 4/4: Select fulltext and check metadata**

The last step contains many boxes, one for each following pupose:

-  **Submitter:** Shows the remote server, the collection and the
   categories you have selected in the step 1 to 3. You can modify it by
   pushing the "Modify destination" button
-  **Submitter:** Shows the username and the email address used for the
   forward. Once the record is accepted, an email will be sent back to
   this email address.
-  **Media:** Displays each file of the fulltext as a checkbox field.
   The files are organized by categories as they where found in Invenio.
   The files from the "Main" category are selected by default. The user
   can choose the file he wants to forward and also decide to add a file
   by uploading it directly in this function. The uploaded file will be
   stored in Invenio in the "Pushed\_via\_SWORD" category.
-  **Metadata:** Display each metadata found in the MARC file of the
   record. The submitter can modify them as he wants. Be careful,
   changing a metadata before forwarding a record to a SWORD Remote
   Server will not change it in Invenio. The result of modifing metadata
   will then be that those data will not be the same in Invenio and on
   the Remote Server.

Mandatory fields are displayed with a \* after the field label. If one
mandatory field is missing or not well formed, an error message
specifying the wrong field will be displayed and you will be invited to
enter a correct value.

You can abort the submission by pushing the "Cancel" button and be
redirected to the BibSword Admin Interface.

2.4 Forwarding process
~~~~~~~~~~~~~~~~~~~~~~

Once a record is submitted to a Remote Server, several actions are launched:

-  **Data integrity:** Before sending anything, the BibSword Client
   module checks whether the record has already been submitted. If that is the
   case, the action will be aborted and an error message will be returned
   to the user.
-  **Media deposit:** The media is sent to the Remote Collection URL. If
   many files have been selected, they are set in a compressed zip
   archive. If the action failed for any reason such as wrong credentials,
   no response or corrupted media, it will be aborted and an error
   message will be sent back to the user.
-  **Response parsing:** The response of the media deposit is a XML Atom
   Element file. This file contains the URL of the media on the Remote
   Server. The BibSword client module parses this file to retreive the
   URL and send it to the next step.
-  **Metadata submission:**\ Before submitting the metadata, they are
   formatted according to the information given in the last form.
   If any error happens during the metadata deposit process, an error
   message is sent back to the end user.
-  **Forward acknowlegment:** Enventually, when the metadata has been
   correctly submitted to the Remote Server, an acknowlegment XML Atom
   Entry is sent back containing the URL to the media, the metadata and
   the status of the forwarded record. These information allow the user
   to consult, modify and delete the submitted record.

2.5 Email acknowlegment
~~~~~~~~~~~~~~~~~~~~~~~

Once a record has been submitted, it is not directly published on the
remote server. It needs to be accepted by the remote mandator. To
inform the user of the publication of the record, the remote server
sent him an Email containing the link to the record and the password to
be able to do any modification. This email is also sent to the SWORD
Invenio user.

3. BibSword client : User Web Interface
---------------------------------------

Users are allowed to forward their document to a SWORD remote server
using the BibSword client module. For security and integrity reasons,
this action is reachable by users only via the WebSubmit module. This
module defines different workflow for the submission of report. The idea
here is to add the "Forward from Invenio to any remote server" function
in some existing workflow. This workflow already implements credential
checking. So it is easy ensure that an user will not be able to
forward a report he is not autorized to manage.

3.1 The "Demo Export via SWORD" Action
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

3.2 Adding an "Export via SWORD" in an existing workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

4. Configuring a new remote server
----------------------------------

To add a new remote server, the following actions have to be done:

-  Inserting remote server information in the swrREMOTESERVER table
-  Setting up the type of metadata file
-  Adding a link button in the record information page

3.1 The swrREMOTESERVER table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The swrREMOTESERVER table contains links to and credentials of all
SWORD remote servers.
.

srwREMOTESERVER table fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------+--------------------------+--------------------------+
| Field                    |                          |                          |
| Definition               |                          |                          |
| Type                     |                          |                          |
+==========================+==========================+==========================+
| id                       | name                     | host                     |
| unique identification    | name of the remote       | URL where to send the    |
| key of the table         | server (e.g.: *arXiv*)   | authentication request   |
| int(15) unique           | varchar(50) unique       | (e.g.: *arXiv.org*)      |
| primary\_key             |                          | varchar(50) unique       |
+--------------------------+--------------------------+--------------------------+

3.2 The metadata file type
~~~~~~~~~~~~~~~~~~~~~~~~~~

3.3 Link to a new remote server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

5. References
-------------

