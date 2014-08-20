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

.. _publiline-admin-guide:

Publiline Admin Guide
=====================

Introduction
------------

The Publiline module was initially created for the ATLAS experiment at
CERN as a means of approving/rejecting ATLAS documents as Scientific
Notes. This guide will outline how to configure the various actors in
this module in order to have a fully functional document approval
workflow. In order to understand the configuration process, however,
please refer to the `"Using Publiline" <#usage>`__ section.

 

Configure Publiline
-------------------

Step 1 : Define a Publication Committee Chair
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Step 2 : Create a Group
~~~~~~~~~~~~~~~~~~~~~~~

Step 3 : Define Project Leader(s)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 

Overview and usage
------------------

Now that Publiline is configured, you can go back to the submission
window and request appoval for a document. You must ensure that you are
the owner or curator for the document you wish to request approval for,
else you will be denied the right to do so. By requesting approval, you
should receive an email confirming the request and the Publication
Committee Chair should also receive an email asking him/her to assign a
referee to make a reccommendation for your document (see the Figure
below).

The Publication Committee Chair can access the Publiline module in order
to select a referee. Once a referee is assigned, he/she will be notified
by email of this as well as all members of the group you created. The
referee is then able to make a recommendation using the features in the
Publiline module. Once this recommendation is made, the Publication
Committee Chair is notified, and he/she makes a final recommendation by
taking into account the decisions of both the Group and the Referee. As
soon as the Publication Committee Chair's decision has been entered, the
Project Leader is notified. He/she then makes the final decision of
whether to approve or reject the document based on the feedback from the
PCC, Referee and Group. A diagram of this workflow is shown below.

|image0|

.. |image0| image:: /_static/admin/publiline-guide-flow.png
