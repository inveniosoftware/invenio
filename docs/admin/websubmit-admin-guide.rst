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

.. _websubmit-admin-guide:

WebSubmit Admin Guide
=====================

*Disclaimer:* Though this guide provides all the necessary information
to start learning WebSubmit from scratch and reach a good level in
administrating it, this guide is not yet fully complete, and might
contain information that has not been strictly verified (sample codes
are for eg. provided "AS IS", only to offer some guidance to the admin).

Specific topics would benefit from to being more developed, such as HOW-TOs,
sample workflows (for eg. approval workflows and referee management). At
this point the demo submissions that come standard with the Atlantis
demo site remain essential companions to this guide.

**Contributions are welcome (for eg. sample workflows, function
descriptions, etc.)**

Contents
--------

-  **1. `Overview <#shortIntro>`__**

   -  1.1  \ `How WebSubmit works <#philosophy>`__
   -  1.2  \ `Behind the scenes <#behindthescenes>`__

-  **2. `Configure Submissions: a Tutorial <#2>`__**

   -  2.1  \ `Creating the submission <#2.1>`__
   -  2.2  \ `Building the interface <#2.2>`__
   -  2.3  \ `Adding the functions <#2.3>`__
   -  2.4  \ `Restricting the submission <#2.4>`__

-  **3. `WebSubmit Elements <#3>`__**

   -  3.1  \ `Existing elements <#3.1>`__
   -  3.2  \ `Creating a new element <#3.2>`__
   -  3.3  \ `Creating a new check <#3.3>`__

-  **4. `WebSubmit Functions <#4>`__**

   -  4.1  \ `Existing functions <#4.1>`__
   -  4.2  \ `Creating a new function <#4.2>`__

-  **5. `File Management with WebSubmit <#5>`__**

   -  5.1  \ `**Option 1:** File Input element + FFT <#5.1>`__
   -  5.2  \ `**Option 2:** File Input element +
      Move\_Files\_To\_Storage function <#5.2>`__
   -  5.3  \ `**Option 3:** Create\_Upload\_Files\_Interface +
      Move\_Uploaded\_Files\_To\_Storage functions <#5.3>`__
   -  5.4  \ `**Option 4:** Upload\_File element instance +
      Move\_Uploaded\_Files\_To\_Storage function <#5.4>`__
   -  5.5  \ `**Option 5:** FCKeditor element instance +
      Move\_FCKeditor\_Files\_To\_Storage function <#5.5>`__
   -  5.6  \ `**Option 6:** Upload\_Photo\_interface element instance +
      Move\_Photos\_To\_Storage function <#5.6>`__
   -  5.7  \ `Alternatives to WebSubmit: BibDocFile CLI or BibDocFile
      Web Interface <#5.7>`__

-  **6. `Access restrictions <#6>`__**

   -  6.1  \ `Admin-level <#6.1>`__
   -  6.2  \ `User-level <#6.2>`__

-  **7. `Linking to submissions <#linking>`__**

   -  7.1  \ `Adding a link from the submissions
      page <#linkingfromsubmissions>`__
   -  7.2  \ `Linking to a submission with direct URL (in email,
      formats, etc.) <#linkingwithurl>`__

-  **8. `Terminology <#terminology>`__**

   -  8.1  \ `8.1 The document type of a file
      (``doctype``) <#terminologydocumenttype>`__
   -  8.2  \ `8.2 The submission directory
      (``curdir``) <#terminologycurdir>`__

-  **9. `Load/dump Submissions <#load_dump_cli>`__**

(Check out the `old WebSubmit admin guide <#oldwebsubmitguide>`__)

1. Overview
-----------

1.1 How WebSubmit Works
~~~~~~~~~~~~~~~~~~~~~~~

WebSubmit provides the infrastructure to set up customized pages for
your users to submit new metadata and files to your repository. It is
highly flexible in order to accomodate to the various type of documents
that you might need to archive. As a consequence of this flexibility, it
requires a good level of understanding of the concepts behind WebSubmit.

A simplied schema of a typical WebSubmit workflow is the following one
(figure 1): one or several pages are presented to the user to enter some
information, such as title of the document, authors, etc. Each of these
pages contain a form with one or several `WebSubmit elements <#3>`__,
which can either display some information to the user, or ask for input
from the user. `WebSubmit elements <#3>`__ are described more in
detailed further below. After the user has finished filling the forms on
all pages, a series of `WebSubmit functions <#4>`__ are called. These
functions will typically (1) post-process the data, (2) create a
MARCXML, (3) upload the created MARCXML file, and (4) send confirmation
email(s).

|image0| Figure 1

One thing worth learning from this simple workflow is that (1) functions
are executed one after each other, (2) that each function can have side
effects, such as sending email, and that (3) the output of these
functions is displayed to the user. Typical submissions use many
side-effect functions, and only one function that give some feedback to
the user (in the form of a web page). Also most submissions usually need
only a single page.

Finally, note that you can plug a check for each field of a page, so that
the user cannot proceed further if some invalid text has been entered.

|image1| Figure 2

Functions are also organized in steps (Figure 2). By default, WebSubmit
runs the "step 1 block" and then stops: to run the next steps one must
have a function at the end of step 1 that jump to another block (for eg.
CaseEDS function) or have a WebSubmit element that set the input form
"step" to the value of the block number (such as
"``Create_Modify_Interface``\ " function).

|image2| Figure 3

A set of WebSubmit functions comes installed by default in Invenio, to
provide all the necessary functionality to create your own workflow.
The behaviour of these functions can be customized through their
parameters. Advanced users can also create their own functions in Python
(see further below in this guide). The main difficulty for beginners is
to pick the adequate function and carefully choose their ordering. It is
recommended to get inspiration from the sample demo submission at first.

At this point it is particularly important to understand that the
WebSubmit engine s more or less limited to 1) displaying page to collect
data, and 2) run functions. It does not take care of building a record
and inserting it into a collection, but expects to have a set of
functions configured to do so.

Such a multi-page submission could appear to users as shown in figure 4.
Note that this figure shows a special page *0*. This "cover" page is
mandatory for all submissions, and is automatically generated by
WebSubmit. It can be customized to 1) display a description of the
submission, 2) show the available "actions" (described further below)
and 3) let the users choose among the available "categories" (described
further below).

|image3|

→

|image4|

→

|image5|

→

|image6|

Page "0"

 

Page 1

 

Page 2

 

Functions ouput

Figure 4

Indeed, typical submissions do not contain only one, but several
independant workflows called "actions": one action might be dedicated to
the submission of a document, while another one will let the user modify
a previously submitted record. Different actions can therefore display
different sets of pages and call different post-processing functions.
The first page of a submission (page "0") will let users chose among the
offered actions.

By convention we use 3-letters names for the actions of a submission.
For example:

-  **SBI**: submit a new record
-  **MBI**: modify the metadata of a record
-  **SRV**: submit a revised file

|image7| Figure 5

Actions are displayed as several buttons (blue by default) for users to
choose from to start a new submission (Figure 6):

|image8| Figure 6

Figure 6 also shows the possibility to select among various categories
prior to jumping into one of the available actions. These categories
usually don't have a direct impact on the chosen workflow. Think of them
simply as a simple WebSubmit element place on the first page, that is
common to all the actions of your submission (indeed you could set up
your submissions to have such categories inside your submission actions
pages, but that would require additional work).

Last, but not least, a submission is usually referred to by a short name
(at most 5 letters), reused in many places in the WebSubmit admin
interface.

To summarize:

-  A **submission** is made of different actions
-  An **action** is a workflow made of pages, checks and a flow of
   functions.
-  A **page** contains several WebSubmit elements, usually input
   elements with some label.
-  A **WebSubmit element** is a control on the interface to input or
   display values.
-  Javacript **checks** can be attached to WebSubmit elements, in order
   to validate the input data before going to a futher step of the
   submission.
-  A **function** performs some post-processing operations, usually on
   data collected thanks to WebSubmit elements. Functions can have
   side-effects and outputs
-  Functions are organized in **steps**, blocks of functions

Another concept remains to be explained, but this functionality tends
to disappear from submissions, and might be deprecated at some point. We
provide the explanation about it below only for completeness, but it is
strongly discouraged to go that way:

It is possible to group actions in **sets**: an action set is a
succession of actions which should be done in a given order when a
user starts.

For example the submission of a document can be composed of two
actions: Submission of Bibliographic Information (SBI) and Fulltext
Transfer (FTT) which should be done one after the other.
When the user starts the submission, we want the submission to get
him first in SBI and when he finishes SBI to carry him to FTT. SBI
and FTT are in this case in the same action set. They will both have
a level of 1 ("level" is a bad name, it should be "action set
number"), SBI will have a score of 1, and FTT a score of 2 (which
means it will be started after SBI). If you set the stpage of FTT to
2, the user will be directly carried to the 2nd page of the FTT web
form. This value is usually set to 1.
The endtxt field contains the text which will be displayed to the
user at the end of the first action (here it could be "you now have
to transfer your files")
A single action like "Modify Bibliographic Information" should have
the 3 columns to 0,0 and 1.


1.2 Behind the scenes
~~~~~~~~~~~~~~~~~~~~~

This section highlights a few key behaviours of WebSubmit which are
particularly important to understand when designing a submission.

When a user starts a new submission, a working directory is created on
disk in order to store all the collected values. This working directory
is usually called the "``curdir``\ ". It is located in a subdirectory of
``/opt/invenio/var/data/submit/storage/``\ *{action
directory}*\ ``/``\ *{submission code}*\ ``/``\ *{submission access
number}* where *{submission code}* is the short name of a submission and
*{submission access number}* is a unique submission session identifier
(displayed on the web submission interface as the *submission
number*).\ *{action directory}* is ``running`` for SBI actions,
``modify`` for "MBI" actions, ``revise`` for "SRV" actions, etc. (This
is configured in the "Actions" part of the WebSubmit admin interface)

Whenever the user moves from one page to the other, or submit the
form, the curdir is populated with files named after the submission
elements displayed on the page, with their content being the user
inserted values (User uploaded files can be found by default in the
``curdir/files/`` directory). It is these files that WebSubmit functions
such "``Create_Record``\ " or "``Modify_Record``\ " will use in order to
create the MARCXML to upload (Note that the output of these functions
will be a file named "``recmysql``\ " in the ``curdir``, that will
contain the MARCXML to upload)

The curdir contains a few other additional files:

-  ``function_log``: the list of functions called by the WebSubmit
   engines
-  ``SuE``: the email of the submitter
-  ``doctype``: the short name (code name) of the current submission
-  ``act``: the current action (SBI, MBI, etc.)
-  ``step``: the step of the functions
-  ``curpage``: the current page of the submission
-  ``ln``: the language chosen by the user to display the web interface
-  ``combo``\ *{doctype}*: for eg. ``comboDEMOART`` contains the chosen
   category on page "0".
-  etc.

The path to the ``curdir`` can sometimes be slightly different,
depending on the chosen action. For eg. the SRV action will use
``/opt/invenio/var/data/submit/storage/revise/``\ *{submission
code}*\ ``/``\ *{submission access number}* where *{submission code}*

When the functions will run they will most probably create additional
files, such as "``SN``\ " created by the "``Create_Recid``\ " function
which reserves a record id, "``RN``\ " created by function
"``Report_Number_Generation``\ " to reserve a report number, or the
"``recmysql``\ " file already mentionned above. Many of these output
file then become input parameters for the next functions to be executed.
This shows the importance of running a well defined set of functions in
a well defined order.

The ``curdir`` is not removed after the end of the submission. This
gives you the opportunity to keep track of past submissions in case
something would have gone unexpected. However the use of the
"``Move_to_Done``\ " function will create a zipped archive of this
directory (+ rename it using the report number of the record, found in
file ``curdir/RN``), and will move it to a different directory,
``/opt/invenio/var/data/submit/storage/done/running/``.

2. Configure Submissions: a Tutorial
------------------------------------

This chapter is a quick walkthrough for creating your submission. It is
not trying to explain everything, but simply goes through the main steps
necessary to configure a submission.

2.1 Creating the submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1.** Go to the `WebSubmit admin
interface </admin/websubmit/websubmitadmin.py>`__
and click on the "Add New Doctype" button at the bottom of the screen.
Give your submission an ID (eg. ``DEMOTEST``. This cannot be changed
later and should be kept short. It is used in URLs to link to your
submission), a name and a description. The name and the description will
be displayed on the users end. The description can contain HTML markup.
You can also choose to clone from an already existing submission so that
existing configuration for pages, functions, elements, etc. are copied
over to your new submission (this might be not wanted if the submission
you copy from include submission specific elements).

**2.** From the submission page, select from the "Add a new Submission"
menu the action to add to your newly created submission. For eg. select
"[SBI] Submit New Record" to create an action that will allow users to
submit new documents. Press the "Add Submission" button to add the
chosen action. You are given the possibility to clone the configuration
from another existing submission. Start with a blank one or choose an
existing one, then press "Continue".

**3.** On the following page, fill in the form:

-  Choose if the action is to be displayed on the start page of your
   submission.
-
-  Enter the "``Status Text``\ ": not really used in user interface (*to
   be checked*): label for your action in the WebSubmit admin interface.
-  Other fields are related to action sets (*chained actions*). It is
   recommended to leave the default values.

   -  Input the "``End text``\ ": text displayed at the end of the
      previous action to link to this one, provided that this action is
      chained to another (leaving empty is recommended).
   -  Choose the "``Stpage``\ ": the page number that should be used as
      starting point when reaching this action from another chained
      action: leaving '0' is recommended).
   -  The "``level``\ ": the group of actions to which this one belongs,
      in case it is chained with another action(s) (leaving emtpy is
      recommended).
   -  The "``score``\ ": the order in which grouped actions are chained
      (leaving empty is recommended).

Once done, press the "Save Details" button.

**4.** (Optional) Repeat steps 2 and 3 for any other workflow you want
to support in your submission. If the action you want to add is not part
of the list, click on the `available
actions </admin/websubmit/websubmitadmin.py/actionlist>`__
menu, press the "Add Action" button and enter the "``action code``\ "
(for eg. ``SBI``), "``description``\ " (displayed as the page title when
going through the submission pages), "``dir``\ " (in which subdirectory
of the default base submission folder the running/done submissions for
this action will be saved, for eg. ``submit``), and "``status text``\ "
(displayed as the label for the action button on the main submission
interface). Press Save Details, and you are ready to use this action.

**5.** (Optional) To propose a list of categories on the splash page
(page 0) of your submission, select your submission from the main
`WebSubmit admin
interface </admin/websubmit/websubmitadmin.py>`__,
scroll down to the "Categories" section on the page, enter a new
category, with "``ID``\ " being the key code of the new category you
want to add (this value will be saved in the corresponding file in
``curdir`` directory of your submission. Reminder: the file in
``curdir`` containing this value will be named ``comboDEMOTEST``,
provided that "``DEMOTEST``\ " is your submission ID) and
"``description``\ " being the value displayed to the user for this
category. Press "``Add Category``\ " to add the category.

**6.** (Optional) To enter the list of persons that will be recognized
as referees of a submission (for eg. by the "``Is_Referee``\ "
function), select your submission from the main `WebSubmit admin
interface </admin/websubmit/websubmitadmin.py>`__,
scroll down to the "Manage Referees" section on the page, and click on
the "Manage Referees" button.

Select the user(s) from the list (users must have an account on the
system), choose which category they manage, and click "Add". Once done,
click "Finished".

**7.** The skeleton of your submission is now basically ready. You will
need to add new pages to it, as well as insert post-processing
functions. These steps are defined in the next sections. What you can do
now is to make the submission visible on the main `submissions users
page </submit>`__. To do so, click on the `Organise
Main
Page </admin/websubmit/websubmitadmin.py/organisesubmissionpage>`__
of the main menu, select your submission in the "Document Type Name"
menu, choose from the next menu to which branch of the submission tree
you want to attach this submission, and press "Add". Reorganize the tree
as wanted from this interface.

2.2 Building the interface
~~~~~~~~~~~~~~~~~~~~~~~~~~

**1.** Go to the main `WebSubmit admin
interface </admin/websubmit/websubmitadmin.py>`__
and select your submission. Choose the action (SBI, MBI, etc.) for which
you want to build the interface and click on the corresponding "view
interface" link.

**2.** If you want to add a new page, click on the "Add a Page" button.
Follow the "view page" link displayed next to the newly created page, or
the one next to the page you want to modify.

**3.** To add a new field on the page, press the "Add a Field" button
(at the bottom of the screen). On the following page:

-  Select a field from the existing list of WebSubmit elements.
-  Enter a field label. It will be displayed just before the field on
   your page. The label can contain HTML. Note that this label will not
   be used in modification actions (MBI) built using the
   "``Create_Modify_Interface``\ " function. Instead, the "Modification
   Text" attribute of the element will be used.
-  Set if the field should be mandatory or not. Note that some elements
   (`User Defined Input Elements <#3.2.1>`__, `Hidden Input
   Elements <#3.2.5>`__ and `Response Elements <#3.2.5>`__) should never
   be set "mandatory".
-  Give a short description to the label. It will be used for eg. to
   notify the user that mandatory field named *XXX* has not been filled
   in.
-  Select a Javascript check from the list if you want to validate the
   content of the field according to some criteria.

Once done, hit the "Add Field" button.

Note that this step is simply instantiating a WebSubmit element to
include on your page. If you want to include a field that does not exist
in the available elements, you should first create it. Learn more about
the creation of WebSubmit elements in the `*WebSubmit Elements* <#3>`__
chapter of this guide.

**4.** Repeat step 3 as many times as needed. You can reorder the
fields on the page, remove them or change their attribute. The "edit"
link next to each field will let you change its attributes. The
"element" link will however let you change the attribute of the
WebSubmit element itself, i.e. affecting all the submissions having such
a field on their page.

**5.** You can preview the page by pressing the "View Page Preview"
button at the top of the page. Note that `Response Elements <#3.2.5>`__
will however not be previewed.

**6.** From the "page" interface you can go back successively to the
action interface and the main submission interface by clicking on the
"Finished" buttons at the bottom of the pages.

2.3 Adding the functions
~~~~~~~~~~~~~~~~~~~~~~~~

**1.** Go to the main `WebSubmit admin interface </admin/websubmit/websubmitadmin.py>`__
and select your submission. Choose the action (SBI, MBI, etc.) for which
you want to build the interface and click on the corresponding "view
functions" link.

**2.** To insert a function into the workflow, press the "Add a
Function" button at the bottom of the screen. On the following page:

-  Select a function from the existing list of WebSubmit functions.
-  Enter the "``Step``" to which this function should be added (for
   eg. "1").
-  Enter the "``Score``" of the function, i.e. its order in the list
   of functions of the chosen step (for eg. 20). If a function already
   exists for the chosen score, functions will simply be shifted.

Once done, hit the "Save Details" button.

Note that this step is simply inserting an already existing WebSubmit
function in your workflow. If you want to include a totally new function
you should first create it. Learn more about the creation of WebSubmit
functions in the `*WebSubmit Functions* <#4>`__ chapter of this guide.

**3.** Once the function is inserted you can change its parameters by
clicking on the "View parameters" link. Each function has a different
set of parameters. Check the function documentation (available from the
`Available
Functions </admin/websubmit/websubmitadmin.py/functionlist>`__
menu of the WebSubmit admin interface) to learn more about the offered
options.

**4.** Repeat steps 2 and 3 as many times as needed. You can reorder the
functions on the page or remove them.

2.4 Restricting the submission
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Access to the submission interface is mostly restricted via the
WebAccess module. You can check out the `Access Restrictions <#6>`__
chapter of this guide and refer to the `WebAccess
admin </help/admin/webaccess-admin-guide>`__ guide
for detailed information.

In addition to WebAccess you can use the following functions to restrict
your submission:

If you have set up an action that requires to modify an existing record
(to add file, modify metadata, etc.) you can add the
"``Is_Original_Submitter``" function in order to only let the original
submitter of the record modify the record. This function must be added
at the beginning of your list of functions (usually after the
"``Get_Recid``" function), for **each action**, and **each step**.
Check out the `*Adding the functions* <#2.3>`__ section of this guide to
learn how to add this function to your workflow.

You can also use the "``User_is_Record_Owner_or_Curator``" function to
enable access to the original submitter of the record AND users
connected to a specific WebAccess role.

If you have set up an action (for eg. "APP") that requires to approve a
document by a referee (defined in the list of referees for your
submission) you can add the "``Is_Referee``" function in order to only
let the referee go through. This function must be added at the beginning
of your list of functions (usually after the "``Get_Recid``"
function), for **each action**, and **each step**. Check out the
`*Adding the functions* <#2.3>`__ section of this guide to learn how to
add this function to your workflow.

3. WebSubmit Elements
---------------------

WebSubmit elements are the building blocks of submission pages. This
section focuses on how to use or create them. Refer to the overview of
this guide to learn more about the concept of WebSubmit elements.

3.1 Existing elements
~~~~~~~~~~~~~~~~~~~~~

The list of existing elements can be found in the `"available elements"
section </admin/websubmit/websubmitadmin.py/elementlist>`__
of the WebSubmit admin interface. By default these elements are
instances used in the demo submissions. You can reuse them, but it is
recommended to create new elements to use in your own submissions,
excepted for complex "response" elements that are generic enough.

Once instantiated for a submission, elements become *fields* on the
submission page. It is important to make a difference between the fields
attributes, which are submission specific, and the element attributes,
which apply to all submission using them.

3.2 Creating a new element
~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes the creation of a customized element. It does not
show how to add an already existing element to your submission. Refer to
the `Tutorial <#2>`__ to learn how to add an existing element to your
submission.

To create a new element, go to the the `"available elements"
section </admin/websubmit/websubmitadmin.py/elementlist>`__
of the WebSubmit admin interface, scroll down to the bottom of the page
and press the "Add New Element" button.

Fill in the form:

-  **Element Name**: The name of the element (Eg: ``DEMO_TITLE``)
-  **Modification Text**: The prefix to be used when the element is used
   by the "``Create_Modify_Interface``\ " function (i.e. in MBI actions)
-  **Element Type**: The type of element:

   -  *User Defined Input*: the element is a static area displaying the
      content of the field "Element Description". The content must be
      HTML-escaped (or can be HTML).
   -  *File Input*: the element is a basic control to upload files
   -  *Hidden Input*: the element is an hidden form input field, and its
      value is the one defined in the "Value" field (below).
   -  *Text Input*: the element is a simple text field. Initial value is
      the one defined in the "Value" field.
   -  *Response*: the element executes the Python code from the "Element
      Description" field. The code is executed at runtime when
      displaying the page. The element output consists in the value
      assigned to the variable "``text``\ " in the scope of this field
      at the end of the execution of the element.
   -  *Select Box*: a list control. The full HTML code of the list must
      be given in the "Element Description" field. For eg:

      ::

          <select name="DEMO_LANG">
                  <option value="eng">English</option>
                  <option value="fre">French</option>
                  <option value="ger">German</option>
          </select>

      The submitted value will be the one defined in the "``value``\ "
      parameter.

   -  *Text Area Element*: An HTML text area field.

-  **Marc Code**: the MARC code from which the value could be retrieved
   when the element is used by the "``Create_Modify_Interface``\ "
   function (i.e. in MBI actions)
-  **Size**: The size of the text input field (for "Text Input" Element
   Types)
-  **No. Rows**: The number of rows for "Text Area" Element Types
-  **No. Columns**: The number of columns for "Text Area" Element Types
-  **Maximum Length**: The maximum length (in characters) for "Text
   Input" Element Types. Note that it only sets a limits in the user's
   browser, but is not check server-side.
-  **Value**: The initial value for "Text Input" or "Hidden Input"
   elements
-  **Element Description**: The content/code for "User Defined Input",
   "Select Box" and "Response" elements

Once done, hit the "Save Details" button. You are done with the creation
of your element. You can then add it to your submission page.

**About element names**: some names are "reserved", and should not be
used as names for elements, as they would overlap with filenames created
internally by WebSubmit in the submission directory (curdir). You can
still use these element names, but should be aware of the potential side
effects of changing such variables with user submitted values. An
up-to-date list of reserved filenames for your installation can be found
by running
``python -c 'from invenio.legacy.websubmit.config import CFG_RESERVED_SUBMISSION_FILENAMES;print CFG_RESERVED_SUBMISSION_FILENAMES'``.

3.2.1 User Defined Input Elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This element is simply displaying the the content defined in the field
"Element Description". The content must be HTML-escaped (or can be
HTML). This is element is not really suitable for user-input values.

3.2.2 File Input Elements
^^^^^^^^^^^^^^^^^^^^^^^^^

The element displays a basic control to upload files. The file uploaded
with this element can be found upon submission inside
``[..]/files/ELEMENT_NAME/`` (where ``ELEMENT_NAME`` is your element
name, for eg. ``DEMOART_FILE``) within the submission directory.

You can then further process the uploaded file with relevant WebSubmit
functions (eg. stamp the file), and attach it to the record (see
`section 5. *File Management with WebSubmit* <#5>`__ of this guide).

3.2.3 Hidden Input Elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Simply create an hidden input field, with the value defined in the
"Value" field of the element. The uploaded value can be found as any
other element in the submission directory upon submission of the form.

The main usage of this field is to upload a statically defined value in
order to check if the form has already been submitted. Static values to
be part of the record would better be defined in the BibConvert
configuration file used to create the record.

3.2.4 Text Input Elements
^^^^^^^^^^^^^^^^^^^^^^^^^

A simple text input field, Nothing much to say about it excepted that it
is usually the most used of all elements.

3.2.5 Response Elements
^^^^^^^^^^^^^^^^^^^^^^^

Response elements are elements evaluated at runtime, which execute the
Python code they embed. These elements are useful when you need to
display complex controls that are not supported by default by WebSubmit,
or if you need to generate content dynamically. The returned output
(displayed on the submission form) of response elements is the one
defined at the end of the execution in the "``text``\ " variable.

For eg. to display a radio button one would write:

.. code-block:: python

    text = ""
    options = [1, 2, 3]
    for option in options:
        text += '<input type="radio" name="group1" id="%(opt)i" value="%(opt)i"><label for="%(opt)i">Option %(opt)i</label>' % {'opt': option}


which would display as:::

    Option 1 Option 2 Option 3

Upon submission of the form, a file named "``group1``" would be
created in that case with the chosen value in the submission directory.

Response elements have "magically" access to some global variables,
provided that they have been set at the moment of executing the element:

-  **``sysno``** the current record id
-  **``rn``** the current report number
-  **``act``** the current submission action (SBI, MBI, etc.)
-  **``curdir``** the path of the current submission directory
-  **``uid``** the user ID of the current submitter
-  **``uid_email``** the email of the current submitter

When defining a response element you should be aware of a few traps:

-  You must expect that the page can be reloaded. In that case possible
   actions performed by your element should not be done twice. You also
   have to take care of the displayed state of your element. For eg. a
   list generated by a response element should not reset to the default
   value when the page refreshes if the user has already chosen a custom
   value. You take care of this by reading the corresponding file in the
   submission directory.
-  When used in MBI (modify) actions with the
   "``Create_Modify_Interface``" function (which takes care of
   building the modification form by mirroring the page defined for the
   initial submission, SBI), you should read the initial state from the
   record (if defined in the record), or from the curdir if the page is
   refreshed.
-  You should never specify a response element as "mandatory" when
   including it on your page.

A possible skeleton for a response element could be: (FIXME: Check...)

.. code-block:: python

    import os
    from invenio.legacy.websubmit.functions.ParamFile import ParamFromFile
    from invenio.legacy.bibrecord import get_fieldvalues

    this_element_name = "DEMOART_TEST" # This would be your element name

    if act == "SBI" and not os.path.exists(os.path.join(curdir, this_element_name)):
        default_value = "A default value" # or any default value
    elif act == "MBI" and not os.path.exists(os.path.join(curdir, this_element_name)):
        default_value = get_fieldvalues(sysno, '245__a')
    else:
        default_value = ParamFromFile(os.path.join(curdir, this_element_name))

    text = '<input type="text" name="%s" value="%s"/>' % (this_element_name, default_value)


Since response element needs the submission context and can possibly
have side effects, they are never executed when previewing your
submission pages from the WebSubmit admin interface.

3.2.6 Select Box Elements
`````````````````````````

Select Box elements are used to display lists menus (either as dropdown
menu or multiple selection list). The element is not smart enough to
save you from specifying the HTML markup of the list, but will at least
set the right intial state when reloading the submission page or when
used in MBI actions.

You would for eg. define the following "description" for an element
displaying a list of languages:

.. code-block:: html

    <select name="DEMOART_LANG">
            <option>Select:</option>
            <option value="eng">English</option>
            <option value="fre">French</option>
            <option value="ger">German</option>
            <option value="dut">Dutch</option>
    </select>

In the above example a file named "DEMOART\_LANG" will be created with
the user chosen value (for eg. "ger") in the submission directory.

Note that if you set the element as being "mandatory" on your page, the
initial "Select:" value must be the first option of your list (you can
otherwise let specify the element as optional, and remove this item if
wanted).

3.3 Creating a new check
~~~~~~~~~~~~~~~~~~~~~~~~

When adding an existing element to your submission page you can
associate a Javacript check to the element. You can choose from the
existing one or define your own check from the `Available
Checks </admin/websubmit/websubmitadmin.py/jschecklist>`__
menu of the WebSubmit admin interface.

From the "Available Checks" page, select "Add check", give it a name and
a "description": the description corresponds to the Javascript code to
be executed to validate the form before submitting it. In this
description you should define a Javascript function named after your
check, that takes a string (the value to validate) as input. The
function must then return ``0`` if the check fails (the form cannot be
submitted) or ``1`` if the check passes. In addition you may want to
raise an alert notifying the user about the error.

For eg. to check if the given number of a field is smaller than 10, we
create a "check" named ``Smaller_Ten``:

.. code-block:: python

    def Smaller_Ten(txt) {
        /* Check if input is strictly smaller than 10 */

        if (parseInt(txt) < 10 && parseInt(txt).toString()==txt) {
            // Note that parseInt('9a') returns 9, hence the '.toString()==txt' test.
            return 1;
        } else {
            alert("The given number is not smaller than 10! Please fix it.");
            return 0;
        }
    }

4. WebSubmit Functions
----------------------

This section focuses on how to create new WebSubmit functions and use
existing ones. To learn more about the concept of WebSubmit functions,
read the `Overview <#shortIntro>`__ section of this guide.

4.1 Existing functions
~~~~~~~~~~~~~~~~~~~~~~

The list of existing functions can be found in the `"available
functions"
section </admin/websubmit/websubmitadmin.py/functionlist>`__
of the WebSubmit admin interface. Click on "Edit Details" links to read
more about the functions.

You add existing functions in the functions list of each action (SBI,
MBI, etc.) of your submission in order to post-process user-submitted
values and build your customized workflow. Some functions have some
prerequisites on the order they are run, and the functions that must
precede them. For eg. many functions expect the "``Get_Recid``\ "
function to run before them. You can check the workflows provided with
the Atlantis Demo installation

4.2 Creating a new function
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes the creation of a customized function. It does
not show how to add an already existing function to your submission.
Refer to the `Tutorial <#2>`__ to learn how to add an existing function
to your submission.

A WebSubmit function corresponds to a Python file, which must be named
after the function name (eg "``My_Function``\ " =>
"``My_Function.py``\ ") and placed into the
``/opt/invenio/lib/python/invenio/websubmit_functions/`` directory. The
file must also contain a Python function with the same
"``My_Function``\ " name. This function interface must be the following
one:

::

    def My_Function(parameters, curdir, form, user_info=None):

where

-  ``parameters``: a dictionary containing the parameters and values
   that can be configured in the submission web interface.
-  ``curdir``: the path to the current working directory.
-  ``form``: the form passed to the current web page for possible
   reference from inside the function.
-  ``user_info``: the user\_info objet reprenting the current user

The values returned by the function are printed on the last submission
page.

For the function to be available from the WebSubmit admin interface, it
must be specifically inserted from the `admin
interface </admin/websubmit/websubmitadmin.py/functionlist>`__.
Scroll down to the bottom of the list, and press "Add New Function".
Insert the function name, as well as all the wished parameters for the
function.

5. File Management with WebSubmit
---------------------------------

This chapters introduces different strategies to enable file upload in
WebSubmit submissions. You should already have a good understanding of
how WebSubmit works before reading further. Some practice in WebSubmit
submission implementation is also highly recommended in order to
understand the techniques introduced below. To some extent, you might
want to come back to this chapter only once you have already set up your
submission, and are about to implement file support, as the
documentation below is sometimes describing detailed implementation
steps.

Several techniques exists to handle files, to accommodate to various use
cases. Just read further below to choose the most appropriate technique
based on your needs.

5.1 File Input + FFT Technique
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most "basic" way of letting your users submit files is to add a
*File Input* element to your submission page(s), one for each possible
file to upload, in the same way as you add other input fields.

This technique is useful if you need to handle a well known number of files.

**Limitations:**

-  incompatible with function "``Move_to_Done``\ ", as the path in the
   FFT tag would be wrong.
-  revision of files requires well-defined filenames
-  cannot easily delete files
-  cannot easily support file attributes (description, restriction,
   name, etc.) modifications

**Procedure:**

**1)** You can reuse an already existing *File Input* element, or create
your own. If you want to reuse an existing one, jump straight to point 3
below. Otherwise, head to the WebSubmit admin interface, select "6.
Available Elements" in the menu, scroll down the opening page and hit
"Add New Element" button.

**2)** Choose a name for your new element (For e.g. "``DEMO_FILE``\ ").
Select the "*File Input*\ " item of the "Element Type" menu. Once done,
click on the "Save Detais" button.

**3)** Go to the main WebSubmit admin interface and select the
submission you want to edit (for e.g. "DEMOART"), then action (for e.g.
"SBI"), then the page. Scroll to the bottom of the page, and click on
the "Add a Field" button.

**4)** From the "Field Name" menu, select the desired input file element
(for e.g. "``DEMO_FILE``\ ", if you have created it in previous steps).
Fill in the other usual fields, and click "Add Field". Reorder the
elements on the page as needed.

At this step your users will be able to upload a file to the server
during the submission process. Indeed if you have a look at the
corresponding submission directory in
``/opt/invenio/var/data/submit/storage/`` you will see the uploaded file
in the ``/files/DEMO_FILE/`` directory, plus a standard ``DEMO_FILE``
file containing the path to the uploaded file. However the file is not
attached to the uploaded record: you must add a corresponding entry in
the BibConvert template, in a similar fashion as you would with other
input fields.

**5)** Open your BibConvert "target" template used by the
"``Make_Record``\ " or "``Make_Modify_Record``\ " in your preferred
editor. If you know where to find your BibConvert templates, jump to
point 6. Otherwise continue reading: the BibConvert templates are used
by the "``Make_Record``\ " and "``Make_Modify_Record``\ " to create a
MARCXML according to some specific rules. From your submission page,
click on "view functions" of the action you want to edit, then "view
parameters" of the ``Make_Record``/``Make_Modify_Record`` function. The
"create/modifyTemplate" and "sourceTemplate" are the names of the
BibConvert templates you can find in the
``/opt/invenio/etc/bibconvert/config/`` directory (Depending on the
authorization on disk, you might even be able to edit the files from the
web interface). Read more about BibConvert in the `BibConvert admin
guide </help/admin/bibconvert-admin-guide>`__.

**6)** Add an *FFT* tag to your target BibConvert template. FFT is a
special tag interpreted by BibUpload in order to handle files. You will
find an example below, but you can read more about the FFT syntax in the
`BibUpload admin
guide </help/admin/bibupload-admin-guide#3.5>`__

::

    FFT::REPL(EOL,)---<datafield tag="FFT" ind1=" " ind2=" "><subfield code="a"><:curdir::curdir:>/files/DEMO_FILE/<:DEMO_FILE::DEMO_FILE:></subfield><subfield code="n">My File</subfield><subfield code="t">Main</subfield></datafield>

The sample line above will rename the uploaded record to "My File", and
then attach it to the record (once the created MARCXML will be
BibUploaded). Note that you could keep the original name, or name the
file after the report number, specify a ``doctype`` such as "Main", or
"additional", include a comment specified in another field, etc. Simply
modify the FFT tag according to your needs. Note however that this
technique will allow to revise the file only if you can identify it
later by a well defined name. The above line is also uploading the file
in the category, or *doctype* "Main"

**7)** One last thing not to forget is to add ``DEMO_FILE`` to the
source BibConvert template, as you would for any other WebSubmit
element. Open the source BibConvert template (which is also given as
parameter to the ``Make_Record``/``Make_Modify_Record`` functions, and
can be found in the ``/opt/invenio/etc/bibconvert/config/`` directory),
and add for example:

::

    DEMO_FILE---<:DEMO_FILE:>

Repeat this procedure to add additional input file fields. It is
perfectly ok to have several FFT field instances in the templates.

Note that if one of the ``file input`` fields is left empty by the user,
no file is uploaded, no ``DEMO_FILE`` file is created in the submission
directory, but an erroneous FFT line is still inserted in the created
output. It is why you might want to make all the ``File Input`` fields
mandatory, or use the BibConvert ``MINLW(..)`` function to ensure that
the field is created only if the output line is at least a given number
of characters (to be computed based on the default length of an empty
line). This shows that this technique reaches its limits quite quickly
in terms of flexibility.

Revising/deleting files
^^^^^^^^^^^^^^^^^^^^^^^

To revise files you would create a BibConvert template with the adequate
FFT tag. We assume below that you set up the modification interface by
using the ``Create_Modify_Interface`` function/technique, so that we can
reuse the submission page set up for the "SBI" action. The key point is
that the ``Input File`` element name is well known ("``DEMO_FILE``\ " in
our case).

**1)** Open your BibConvert "target" template used by the
"``Make_Modify_Record``\ " function. Note that it should not be the same
one as used in the "SBI" action of your submission, as it must create
different outputs.

**2)** Add an FFT tag to revise your file:

::

            <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a"><:curdir::curdir:>/files/DEMO_FILE/<:DEMO_FILE::DEMO_FILE:></subfield>
            <subfield code="n">My File</subfield>
            <subfield code="d">KEEP-OLD-VALUE</subfield>
            <subfield code="z">KEEP-OLD-VALUE</subfield>
            <subfield code="r">KEEP-OLD-VALUE</subfield>
            </datafield>

**3)** The above FFT will be *bibuploaded* in ``--correct`` mode, hence
revising the file named "My File" with the new one. Note in this example
the use of the special keyword ``KEEP-OLD-VALUE`` to keep the previous
comment, description or restriction applied to the file, if any (so that
comment is not lost for e.g. if you don't ask a new one).

You will notice the following limitation: you must be able to map the
uploaded file to the target file to revise by its name. This means that
you should be able to initially control your filename(s), for e.g. by
having it fixed ("Main", "additional", "figure", etc) or guessable, for
e.g. using the report number
(``<:DEMOART_RN::DEMOART_RN:>-main, <:DEMOART_RN::DEMOART_RN:>-additional``).

To circumvent this limitation (as well as the impossibility to delete
files), you might combine this technique with one of the techniques
described below (For eg: with the ``Move_Revised_Files_To_Storage``
function detailed in the `Revising/deleting files <#2.2revise>`__
section of the `File Input element + Move\_Files\_To\_Storage
function <#2.2>`__ technique)

5.2 File Input element + Move\_Files\_To\_Storage function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This way of doing is similar to the `technique described
above <#2.1>`__. The main difference is that it leaves the job of
actually uploading/revisings the file(s) to a WebSubmit functions,
instead of the FFT in the uploaded MARCXML.

**Limitations:**

-  revision of files requires well-defined ``doctype``. The consequence
   is that you can have only one file per doctype (1 "Main", 1
   "Additionnal", etc.)
-  cannot easily delete files
-  does not support setting some additional file attributes
   (description, name, etc.)
-  uploaded doctypes must inherit the names of their ``File Input``
   elements. For eg. "DEMO\_FILE", instead of "Main", "Additional",
   "Figure", etc.

**1-4)** Add a file input field to your submission page as describe in
`previous technique <#2.1>`__.

As before, the file is uploaded to the server once the user ends the
submission, but it is not attached to the created record. The solution
is to rely on the "``Move_Files_To_Storage``\ " function:

**5)** Add the "``Move_Files_To_Storage``\ " function to your submission
functions. It is suggested to insert it after the function
"Insert\_Record".

**6)** Configure the ``Move_Files_To_Storage`` function. The key
parameter is ``paths_and_suffixes``, which must contain your
``File Input`` element names, and possibly map to some suffixes to be
added to the corresponding uploaded files.

For example, add ``{'DEMO_FILE':'', 'DEMO_FILE2':'_additional'}`` to
have the files uploaded with DEMO\_FILE and DEMO\_FILE2 elements
attached to the record (with the DEMO\_FILE2 filename suffixed with
"\_additional"). The ``paths_and_restriction`` works similarly to set
the files restrictions.

Each file is simply attached to the record, with its document type
(``doctype``) being the name of your input file element (for e.g. file
uploaded with the "``DEMO_FILE``\ " element is attached with document
type "``DEMO_FILE``\ "). The filenames are kept.

Revising/deleting files
^^^^^^^^^^^^^^^^^^^^^^^

The "``Move_Revised_Files_To_Storage``\ " must be added to your
modification workflow ("MBI"). It will use the file uploaded with your
"``DEMO_FILE``\ " input element to revise the file with ``doctype``
"``DEMO_FILE``\ ", the file from "``DEMO_FILE2``\ " input element to
revise file with ``doctype`` "``DEMO_FILE2``\ ", etc.

**1)** Go to your modification workflow (MBI), and add
``Move_Revised_Files_To_Storage`` to your submission functions (usually
after the "``Insert_Modify_Record``\ ").

**2)** Set up the ``elementNameToDoctype`` parameter of this function
so it maps your ``File Input`` field name to the doctype to revise. For
eg: "``DEMO_FILE=Main``\ " so that file uploaded using the ``DEMO_FILE``
input field will be used to replace the file with ``doctype`` "Main".
This makes the assumption that you indeed previously uploaded (for eg.
with an FFT during an SBI step) a file with this doctype.

You can define several mappings, by using character ``|`` as
separator. For eg: ``DEMO_FILE=Main|DEMO_FILE2=Additional``.

If you have initially uploaded your files with the
``Move_Files_To_Storage`` function, you will for eg. configure the
parameter with "``DEMO_FILE=DEMO_FILE``\ ", so that file uploaded with
``DEMO_FILE`` input field will replace the files that have been
previously uploaded with doctype "DEMO\_FILE".

Note that function ``Move_Revised_Files_To_Storage`` can be used in
combination with other techniques, as long as the mapping in
``elementNameToDoctype`` can be done unambiguously.

Check the ``Move_Revised_Files_To_Storage`` function documentation for
more detailed information.

5.3 Create\_Upload\_Files\_Interface + Move\_Uploaded\_Files\_To\_Storage functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option offers a full-featured file manager, that can be easily
configured to support file upload, revision, deletion, commenting,
restrictions, etc. It can handle an "unlimited" number of files.

The strategy consists in adding a WebSubmit function
("``Create_Upload_Files_Interface``\ ") to your submission functions
list, in order to display a file submission interface. The interface
will therefore only show up after all the submission pages have been
filled in and submitted. Once displayed, the interface lets the user
upload new/revised files: the function refreshes the interface for each
upload (runs through the functions list again and stops on the
``Create_Upload_Files_Interface``). When the user applies the
modifications, the submission "step" is incremented and executes the
submissions function of step 2, skipping the display of the interface.
In this step 2 you can perform the usual tasks of your submission. You
also must add an additional function
(``Move_Uploaded_Files_To_Storage``) to run at step 2 in order to attach
the files that have been submitted at step 1.

These functions are incompatible with function
"Create\_Modify\_Interface". It is therefore suggested to create a
dedicated submission action (in addition to "SBI" and "MBI") to let your
users edit the files independently of the bibliographic data. An example
of such setup can be found in DEMOPIC submission.

**Limitations:**

-  Use of a WebSubmit function to draw the interface, which prevents the
   interface to be used inside a submission form (is displayed at a
   later step). Not as integrated as a simple input file form element.
-  Requires Javascript to be enabled user-side (is applicable to all
   submissions anyway.

**1)** Go to your submission in WebSubmit admin, and add a new
submission action (for e.g. "[SRV] Submit New File"). If necessary,
create your own action in `WebSubmit admin "Available WebSubmit
Actions" </admin/websubmit/websubmitadmin.py/actionlist>`__
page. You can clone from another existing action (in that case move to
point 4 below), or simply create an empty action.

**2)** Go to the new SRV action interface ("View Interface"), add a
page, open it and add fields that will allow users to specify the record
to update. Typically you will add a "``DEMO_RN``\ " field to enter the
report number, and "``DEMO_CONTINUE``\ " button to submit the form.

**3)** Go the the new SRV action functions ("View" functions) and add
the necessary functions: for e.g. at step 1, "``Get_Report_Number``\ ",
"``Get_Recid``\ " and "``Create_Upload_Files_Interface``\ ". At step 2,
"``Get_Recid``\ ", "``Move_Uploaded_Files_to_Storage``\ " and
"``Print_Success``\ ".

**4)** Configure the ``Create_Upload_Files_Interface`` parameters. There
are many options available. Briefly, the most important one is the
"``doctype``\ " parameter, which lets you specify the document types
users are allowed to submit. Use "``|``\ " to separate doctypes, and
"``=``\ " to separate ``doctype`` and ``doctype`` description. For e.g.
input "``Main=Main File|Additional=Additional Document``\ " to let users
choose either Main or Additional types (which will show as "Main File"
and "Additional Document" to users). Other parameters will let you
define for which ``doctype`` users can revise or delete files (for e.g.
specify for ``canDeleteDoctypes`` "Additional" so that only these
documents can be deleted once they have been uploaded). Use "``*``\ " to
specify "any declared doctype", and "``|``\ " as separator (for all
``can_*_doctypes`` parameters).

To read more about the parameters available for this function, check the
```Create_Upload_Files_Interface`` function
documentation </admin/websubmit/websubmitadmin.py/functionedit?funcname=Create_Upload_Files_Interface>`__.

**5)** Configure the ``Move_Uploaded_Files_To_Storage``. There are less
options than in ``Create_Upload_Files_Interface`` function. Specify for
e.g. in ``createIconDoctypes`` for which doctypes icons will be created,
or in "``forceFileRevision``\ " if revisions of file attributes trigger
a new file revision. For an up-to-date documentation check the
```Move_Uploaded_Files_to_Storage`` function
documentation </admin/websubmit/websubmitadmin.py/functionedit?funcname=Move_Uploaded_Files_to_Storage>`__.

Revising/deleting files
^^^^^^^^^^^^^^^^^^^^^^^

File revisions and deletions comes for free with the functions. Simply
allow deletion or revision of files when configuring
``Create_Upload_Files_Interface``.

5.4 Upload\_File element instance + Move\_Uploaded\_Files\_To\_Storage function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is similar to `option 3 <#2.3>`__, except that instead of using a
WebSubmit function to build the interface, you use a regular WebSubmit
response element. The advantage is that you can plug the WebSubmit
element wherever you want on your submission page.

**Limitations:**

-  Requires Javascript enabled users-side + support for JQuery library
   (most "recent" browsers)

To set up a file upload interface using this technique:

**1)** Go to your submission page, and add an element: choose the
"``Upload_Files``\ " response element. **But wait!** Read further
before:

**2)** You most probably want to customize the upload interface (set
which types of files can be uploaded, how many, etc.). To do so, you
would have to edit the code of the ``Upload_Files`` response element and
change the parameters of the "``create_file_upload_interface(..)``\ "
function. However this would affect all submissions using this element.
The solution is to "clone" this element (by creating a new element:
"Available elements"-> scroll down -> "Add New Element". Choose for e.g.
name "``DEMO_UploadFiles``\ ", Element Type-> "Response" and paste the
code of the ``Upload_Files`` element in the "Element Description"
field). Once done, add the "``DEMO_UploadFiles``\ " element to your
page.

**3)** Go to your submission functions. Add the
``Move_Uploaded_Files_to_Storage`` function, and configure it in the
same way as it would be done with the `option 3 <#2.3>`__, step 5.

Revising/deleting files
^^^^^^^^^^^^^^^^^^^^^^^

File revisions and deletions comes for free with the this technique.
Simply allow deletion or revision of files when configuring
``Upload_Files`` element of the MBI or SRV steps.

5.5 FCKeditor element instance + Move\_FCKeditor\_Files\_To\_Storage function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This technique relies on the popular HTML rich text editor "FCKeditor",
which embeds an interface to upload files. As a consequence it only
makes sense to use this technique in the cases where you want files to
be uploaded as part of some HTML context. Typical use cases are
submissions for the WebJournal module, for which you want to upload
articles. The ``DEMOJRN`` submission is an example of submission using
this technique.

**Limitations:**

-  Requires Javascript enabled users-side + support for the FCKeditor
   (most "recent" browsers)
-  File revisions and deletions are not supported as such (must be done
   through other options).

Setting up a submission to use the FCKeditor is really similar to the
strategy described in `option 4 <#2.4>`__: the principle is to
instantiate a custom "Response Element" that will call a function taking
care of the interface, and then plug a WebSubmit function to take care
of attaching the files.

**1)** Go to your submission page, and add an element: choose the
"``DEMOJRN_ABSE``\ " response element. **But wait!** Read further
before:

**2)** You will want and need to customize the behaviour of the
FCKeditor, but you don't want to alter the behaviour of other
submissions using this element. The solution is to "clone" this element:
create a new element: "Available elements"-> scroll down -> "Add New
Element". Choose for e.g. name "``DEMO_FCKEDITOR``\ ", Element Type->
"Response" and paste the code of the ``DEMOJRN_ABSE`` element in the
"Element Description" field). Customize the element according to your
needs. This will need some development skills and good overview of your
metadata and submission in order to have the editor correctly
initialized. Additional information can be found in the `FCKeditor
Integration guide </help/hacking/fckeditor>`__.

**3)** Once done, add the "``DEMO_FCKEDITOR``\ " element to your page.

**4)** Go to your submission functions. Add the
``Move_FCKeditor_Files_To_Storage`` function, and configure it so that
the ``input_fields`` parameter list the name(s) (separated by comma if
several instances) given to the FCKeditor instance(s) created in by the
``DEMO_FCKEDITOR`` response element.

Revising/deleting files
^^^^^^^^^^^^^^^^^^^^^^^

The way this editor is currently used does not let you delete/revise
file right from the editor interface. To set up file deletion/revision,
combine this technique with `option 3 <#2.3>`__ for example.

5.6 Upload\_Photo\_interface element instance + Move\_Photos\_To\_Storage function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This interface is specifically dedicated to pictures: it enables the
selection of bunch of photos to upload, and let you preview and comment
them before submitting the record.

**Limitations:**

-  Requires Javascript enabled users-side + support for the Flash plugin
   (version >= 9.0.24)
-  Support for deletions, but not revisions

Setting up a submission to use this interface is really similar to the
strategy described in `option 4 <#2.4>`__: the principle is to
instantiate a custom "Response Element" that will call a function taking
care of the interface, and then plug a WebSubmit function to take care
of attaching the files.

**1)** Go to your submission page, and add an element: choose the
"``Upload_Photos``\ " response element. **But wait!** Read further
before:

**2)**\ As in other strategies that use a response element to layout the
interface, you might want to customize the behaviour of the photos
uploader, but you don't want to alter the behaviour of other submissions
using this element. If so (though it is not needed in the case of this
interface), the solution is to "clone" this element: create a new
element: "Available elements"-> scroll down -> "Add New Element". Choose
for e.g. name "``DEMO_UPLOADPHOTO``\ ", Element Type-> "Response" and
paste the code of the ``Upload_Photos`` element in the "Element
Description" field). Customize the element according to your needs. This
will need some development skills in order to have the interface
correctly customized..

**3)** Once done, add the "``DEMO_UPLOADPHOTO``\ " (or ``Upload_Photos``
if you kept the original file) element to your page.

**4)** Go to your submission functions. Add the
``Move_Photos_To_Storage`` function, and configure it according to your
needs.

Revising/deleting files
^^^^^^^^^^^^^^^^^^^^^^^

The interface lets user add or remove files, but cannot specifically
revise a file. If needed, it can be combined with another strategy such
as `option 3 <#2.3>`__.

5.7 Alternatives: BibDocFile CLI or BibDocFile Web Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These last techniques are not meant to be used in WebSubmit submissions,
but are admin tools that can be used to manage files, independently of
any submission. They are described here for the sake of completness.

The BibDocFile command line interface is describe in more details in
`How to manage your fulltext files through
BibDocFile </help/admin/howto-fulltext>`__.

The `BibDocFile admin interface </submit/managedocfiles>`__ gives access
to some of the functionalities offered by its command-line equivalent
through a graphical web interface. Its interface is similar to the one
offered by the ``Upload_File`` element or the
``Create_Upload_Files_Interface`` function, but is not tied to a
specific submission (and therefore won't automatically execute
post-processing steps such a stamping).

Access to the BibDocFile admin interface is restricted via the
WebAccess ``runbibdocfile`` action.

6. Access restrictions
----------------------

This section focuses on restricting the access to the submission
themselves, not to produce content (records, files, etc.) which are
restricted. Refer to the adequate document to restrict the collections
or files.

6.1 Admin-level
~~~~~~~~~~~~~~~

Access to the WebSubmit admin interface is controlled via the WebAccess
``cfgwebsubmit`` action.

6.2 User-level
~~~~~~~~~~~~~~

Access to the submissions is controlled via the WebAccess ``submit``
action. The action has the following parameters:

-  **``doctype``**: the submission code (eg. ``DEMOART``) for which you
   want to set restrictions.
-  **``act``**: the action (for eg. "SBI") for which you want to set the
   restriction. Can be **\*** to mean any action for the given
   submission.
-  **``categ``**: the category (for eg. "Article", "Preprint") for which
   you wan to set the restriction. Can be **\*** to mean any category
   for the given submission.

Connect for eg. a role to the ``submit`` action with parameters
``doctype=DEMOART, act=SBI, categ=*`` to let people of this role submit
new documents in the ``DEMOART`` submission, in any category.

**If you do not add an authorization for a given submission doctype and
action (even an empty role), the submission is open to anybody.** For
eg. in the above example, provided that an MBI action exists, even with
a restricted SBI action anybody will be able to modify existing
documents with MBI unless the MBI action is also connected to a role. To
make it short: a submission it not restricted until it is...

Note that it is your responsibility as WebSubmit admin to **ensure that
your workflow is not modifying records outside the desired scope**.
Given that records are independant of the submission that created them,
there is no mechanism in the WebSubmit engine that prevents the DEMOART
submission to modify records created with the DEMOBOOK submission. A
check must be added at the level of WebSubmit functions of your
submission to make sure that chosen submission and category well match
the record to be modified (for eg. retrieved via the
``Get_Report_Number`` function)

.

All the above checks also do not **prevent any authorized user to modify
documents submitted by others**. To enable finer-grained restrictions,
use the WebSubmit function "``Is_Original_Submitter``\ " or
"``User_is_Record_Owner_or_Curator``\ " in your MBI, SRV, etc.
submission workflow (for eg. just after the "Get\_Recid" function).
Check also the `Restricting the submission <#2.4>`__ how-to from this
guide.

7. Linking to submissions
-------------------------

7.1 Adding a link from the submissions page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please refer to the tutorial (`section 2.1.7 <#2.1.7>`__) to learn how
to populate the list of submissions on the main submission page (at
*/submit/*).

7.2 Linking to a submission with direct URL (in email, formats, etc.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It might be necessary to construct URL that lead to the submission, for
eg. when sending emails, or when displaying some actions from the
Detailed record view (formats).

7.2.1 URL to main submission page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A url to the main page of a submission can be built with this pattern:

::

    /submit?doctype=DEMOART

where ``DEMOART`` would be your submission code.

7.2.2 URL to jump straight into the submission
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One can directly move into the submission by building such a URL:

::

    /submit/direct?sub={action}(submission_code)

For eg: ``/submit/direct?sub=MBIDEMOART``

In that way one would skip the submission "splash" page (*Page "0"*) and
jump straight to the submission page 1. For an action that must deal
with a specific record (eg. MBI, APP) one can already pre-fill for eg.
the "report number" field:

::

    /submit/direct?sub=MBIDEMOART&DEMOART_RN=TESLA-FEL-99-07

Depending on the way your submission is built, you might **have** also
to specify the category of the document to modify (the category is
usually chosen on page "0" of the submission):

::

    /submit/direct?sub=MBIDEMOART&DEMOART_RN=TESLA-FEL-99-07&comboDEMOART=Article

(Note how the category field is constructed: ``combo{submission_code}``
)

You can add as many parameters as needed to ensure that the form is
filled with adequate values before being presented to the user. The
parameters names correspond to the fields names in WebSubmit. For eg:

::

    /submit/direct?sub=MBIDEMOART&DEMOART_RN=TESLA-FEL-99-07&comboDEMOART=Article&DEMOART_CHANGE=DEMOART_TITLE

The parameters that you have to specify will depend on the usage which
is made of them on the submission side.

For fields that can take several values as input (for eg. selection
lists, as in the ``DEMOART_CHANGE`` example above) and that translate
into a file in the submission direction with one value per line, you
would have to specify all the values in the same URL argument, separated
by ``"%0A"`` (newline ``"\n"`` encoded for URL):

::

    /submit/direct?sub=MBIDEMOART&DEMOART_RN=TESLA-FEL-99-07&comboDEMOART=Article&DEMOART_CHANGE=DEMOART_TITLE%0ADEMOART_ABS

Depending on how your submission is build, you can also move to another
page ("``curpage``\ " param) or another step of the
workflow("``step``\ " param):

::

    /submit/direct?sub=MBIDEMOART&DEMOART_RN=TESLA-FEL-99-07&comboDEMOART=Article&DEMOART_CHANGE=DEMOART_TITLE&step=1

(In the above example a logged in user would skip the submission splash
page AND the modificaton interface to select the document and fields to
update, to jump directly to the ``DEMOART_TITLE`` modification field)

In such cases you have to make sure that you provide all the information
requested by the submission at each of the steps/pages until the
provided step/page. Depending on how your submission is built it might
be simply not possible to do that. This would be especially true when
advancing steps, as functions netween the steps would not be run — most
probably advancing directly to step 1 will be a maximum one can easily
support — while controlling "``curpage``" parameter might be easier.

8. Terminology
--------------

8.1 The document type of a file (``doctype``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The document type is an attribute of a file. It can be seen as a
category which lets you organize your files: "Main" file, "Additional",
"Figures", "source", whatever you need. It is not so much used excepted
on ``record/XXX/files/`` pages to group files by category. It can
however come handy during file upload processes, to assign different
kinds of restrictions based on the document type, or simply to make the
configuration of the submission easier, depending on which technique you
use to manage files.

8.2 The submission directory (``curdir``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The WebSubmit workflow mainly splits in two parts: data gathering (user
interface side, with WebSubmit pages and elements) and data integration
part as a second step (with WebSubmit functions involved, plus
BibConvert templates). In the middle stands the submission directory
(also called "``curdir``\ "). Each submission session corresponds to a
unique submission directory, which stores the values collected from the
submission pages, in the form of a series of textual files, one for each
input field. These files are named after the submission WebSubmit
elements, and their content is the value input by the submitter. Note
that uploaded files are stored in a ``/files/`` subdirectory.

WebSubmit functions process the files in this directory. For example
"``Make_Record``\ " which creates the MARCXML (through BibConvert
templates), or the ``Stamp_Uploaded_Files``, which will stamp the
uploaded files in the ``/files/`` directory. If you happen to write a
customized WebSubmit response element that writes files to disk, or
implement a WebSubmit function that must retrieve submitted values, you
will certainly use the submission directory.

These submission directories are also helpful to debug submissions, and
can act as a backup when something goes wrong during a submission.

An example of submission directory could be found at this path
``/opt/invenio/var/data/submit/storage/running/DEMOART/1245135338_62620``,
where DEMOART is your submission code, and ``1245135338_62620`` is the
submission session ID, as found at the bottom of each WebSubmit web page
during the submission process. Just after the user has finished the
submission, this directory would contain all the collected values of the
form. But the life of the submission directory does not stop there.
Immediately after the user completed the submission, the WebSubmit
functions are executed: for e.g. (depending on how you have configured
your submission) creation of a report number (stored in the submission
directory too!) (Function ``Report_Number_Generation``), creation of the
MARCXML (usually named "``recmysql``\ ", in the submission directory
again!) (Function ``Make_Record``), upload of the MARCXML (Function
``Insert_Record``) and ``Move_To_Done``. This last function moves the
submission directory to a new place. It could be for e.g.:
``/opt/invenio/var/data/submit/storage/done/DEMOART/DEMO-ARTICLE-2010-001.tar.gz``,
supposedly that the report number of the submitted record is
``ARTICLE-2010-001``. Some other functions will move the submission
directory to other places, and some functions will even let you
configure where to move it.

9. Load/dump Submissions
------------------------

Use ``websubmitadmin`` to dump a given submission configuration from the
database to a file. For example:

::

    $ /opt/invenio/bin/websubmitadmin --dump=DEMOART > DEMOART_db_dump.sql

The submission dumper tool relies on the fact that submission-specific
elements and functions are prefixed with the submission doctype (for
example ``DEMOART``), and will only dump those. Functions, elements,
etc. without prefix are considered "shared", and not dumped by default,
in order to eliminate duplicates). See also option ``--method`` to
change that behaviour.

``websubmitadmin`` can also help you "diff" between different submission
versions (for eg. between a dump file and the database). This tool will
optionally hide differences solely due to ordering of statements in the
dump, or different modification dates. For example:

::

    $ /opt/invenio/bin/websubmitadmin --diff=DEMOART --ignore=d,o < DEMOART_db_dump.sql

Run ``/opt/invenio/bin/websubmitadmin --help`` for more info and more
examples.

Use ``dbexec`` to load a submission dumped with ``websubmitadmin``. For
example:

::

    $ /opt/invenio/bin/dbexec < DEMOART_db_dump.sql

``- End of new WebSubmit admin guide -``

--------------

+--------------------------------------------------------------------------+
| WARNING: OLD WEBSUBMIT ADMIN GUIDE FOLLOWS                               |
+==========================================================================+
| This WebSubmit Admin Guide was written for the previous PHP-based        |
| version of the admin tool. The submission concepts and pipeline          |
| description remain valid, but the interface snapshot examples would now  |
| differ. The guide is to be updated soon.                                 |
+--------------------------------------------------------------------------+

Table of Contents
-----------------

-  **Introduction**

   -  `General Overview of the Manager Tool <#introduction>`__
   -  `Using the manager through an example <#example>`__
   -  `Philosophy behind the document submission system <#philosophy>`__

-  **The Interface**

   -  `Description <#description>`__

-  **`Types of Document <#documents>`__**

   -  `Add a New Type of Document <#documentnew>`__
   -  `Remove a type of document <#documentremove>`__
   -  `Modify an Existing Type of Document <#documentmodify>`__

-  **`Actions <#actions>`__**

   -  `Add a New Action <#actionnew>`__
   -  `Remove an Action <#actionremove>`__
   -  `Modify an Existing Action <#actionmodify>`__
   -  `Implement an Action over a Document Type <#actionimplement>`__

      -  `Create and Maintain the Web Form <#implementwebform>`__
      -  `Create and Maintain the Data
         Treatment <#implementfunctions>`__

-  **`Functions <#functions>`__**

   -  `Create a New Function <#functionnew>`__
   -  `Remove a Function <#functiondelete>`__
   -  `Edit a Function <#functionedit>`__
   -  `All Functions Explained <#functiondescription>`__

-  **`Protection <#protection>`__**
-  **`Catalogues Organisation <#catalogues>`__**
-  **`BibConvert <#bibconvert>`__**
-  **Notes**

-  **`FAQ <#faq>`__**


General Overview of the Manager Tool
------------------------------------

Things to know before using the Manager:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This manager tool allows you to administrate all the WebSubmit
interface. With it, you will be able to create new actions, new
types of documents and edit the existing ones.

The main objects in webSubmit are the "action" (such as "Submit
New Record", "Submit New File", "Modify Record"...) and the "type of
document" (such as "preprint", "photo"...).

To one given type of document can be attached several actions.
An action is the addition of two processes:

-  The first one is the `data gathering <#implementwebform>`__. The
   manager will allow you to create new web forms corresponding to
   the fields the user will have to fill in when using webSubmit.
-  The second one is the `data treatement <#implementfunctions>`__.
   Basically, what the program will do with the data gathered during
   the first phase. The treatment appears in this tool as a sequence
   of functions. This manager will allow you to add functions to an
   action, edit the existing functions, and reorder the functions.

See also:
~~~~~~~~~

    `using the manager through an example <#example>`__
    `interface description <#description>`__
    `actions <#actions>`__
    `document types <#documents>`__


Using the manager through an example
------------------------------------

what is this?
~~~~~~~~~~~~~

The user reaches WebSubmit main page.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|main_menu|  To add a document type to WebSubmit, you should go to the
`main page </admin/websubmit/index.php>`__ and
click on "New Doctype" in the left blue panel.

Even once created, a document type will not appear automatically on
this page. To configure the list of catalogues and document types
displayed on this page, the administrator shall go to the `edit
catalogues </admin/websubmit/editCatalogues.php>`__
page. (see the `guide section <#catalogues>`__)

The user can then click on the document type he is interested in.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|menu_doc|  The text appearing under the header containing
the name of the document can be configured by going to the `main
page <websubmit-admin>`__, click on the title of the document type then
on the "Edit Document Types Details" button.

You can associate several categories to a document type which can be
defined by going to the `main page <websubmit-admin>`__, click on the
title of the document type then on the "View Categories" button. The
selected category will be saved in a file named "comboXXX" (where XXX is
the short name of the document type) in the submission directory.

To add an action button to this page, first implement this action by
going to the `main page <websubmit-admin>`__, click on the title of the
document type then on the "Add a new submission" button. If the action
is already implemented and the button still does not appear on the
submision page, then you should edit the details of this implementation:
go to the `main page <websubmit-admin>`__, click on the title of the
document type then on the icon in the "Edit Submission" column and in
the line of the desired action. There you should set the "Displayed"
form field to "YES".

You can also change the order of the buttons, by going to the `main
page <websubmit-admin>`__, click on the title of the document type then
on the icon in the "Edit Submission" column and in the line of the
desired action. There you can set the "buttonorder" form field.

The user now may choose a category, then click on the action button he wishes.

The submission starts, the first page of the web form appears.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|form|  This web form is composed of several pages, on
each of these pages form fields can be found. To modify the number of
pages, add or withdraw form fields and modify the texts before each form
field, you shall go to the `main page <websubmit-admin>`__, click on the
title of the document type then on the icon in the "Edit Submission
Pages" column and in the line of the desired action. (see the `guide
section <#actionimplement>`__)

On the last page of the submission, there should be a button like in the following image which will trigger the end script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

|end_action|  This button is defined like any other form
field. Its definition should include a *onclick="finish();"* javascript
attribute.

After clicking this button, WebSubmit will apply the end script
functions to the gathered data. To modify the end script, you shall go
to the `main page <websubmit-admin>`__, click on the title of the
document type then on the icon in the "Edit Functions" column and in the
line of the desired action. (see the `guide
section <#implementfunctions>`__)

See also:
~~~~~~~~~

- `interface description <#description>`__
- `actions <#actions>`__
- `document types <#documents>`__
 

Philosophy behind the document submission system
------------------------------------------------

This page will explain some philosophical issues behind the document
submission system.

On the relation between a search collection and a submission doctype:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Interface Description
---------------------

Welcome to webSubmit Management tool:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

on the websubmit admin `main page <websubmit-admin>`__ you will find:
|image13|

-  The list of all existing document type in the middle of the page.
   Click on one line in the list to have access to the main document
   modification panel
-  The right menu panel with the following links inside:

   -  "**webSubmit Admin**\ ": This links leads you back to the main
      page of the manager.
   -  "**New Doctype**\ ": Click here if you wish to create a new
      document type.
   -  "**Remove Doctype**\ ": Click here if you want to remove an
      existing document type.
   -  "**Available Actions**\ ": Lists all existing actions
   -  "**Available Javascript Checks**\ ": Lists all existing
      Javascript checking functions.
   -  "**Available Element Description**\ ": Lists all existing html
      form element descriptions.
   -  "**Available Functions**\ ": Lists all existing functions in
      CDS Submit.
   -  "**Organise Main Page**\ ": Allows you to manage the
      appearance and order of the list of document types on CDS
      Submit User main page.

See also:
~~~~~~~~~

- `interface description <#description>`__
- `actions <#actions>`__
- `document types <#documents>`__
 

Document Types
--------------

See also:
~~~~~~~~~

- `add a new type of document <#documentnew>`__
- `remove a type of document <#documentremove>`__
- `modify a type of document <#documentmodify>`__
- `implement an action over a type of document <#actionimplement>`__


Ading new type of document
--------------------------

How to get there?
~~~~~~~~~~~~~~~~~

Click on the "New Doctype" link in the webSubmit right menu.

How to do this?
~~~~~~~~~~~~~~~

A new document type is defined by 6 fields:

-  **Creation Date** and **Modification Dates** are generated and
   modified automatically.
-  **Document Type ID**: This is the acronym for your new document
   type. We usually use a 3 letters acronym.
-  **Document Type Name**: This is the full name of your new
   document. This is the text which will appear on the list of
   available documents and catalogues on webSubmit main page.
-  **Document Type Description**: This is the text which will appear
   on the document type submission page. This can be pure text or
   html.
-  **Doctype to clone**: Here you can choose to create your document
   type as a clone of another existing document type. If so, the new
   document type will implement all actions implemented by the
   chosen one. The web forms will be the same, and the functions
   also, as well as the values of the parameters for these
   functions. Of course once cloned, you will be able to modify the
   implemented actions.

See also:
~~~~~~~~~

- `remove a type of document <#documentremove>`__
- `modify a type of document <#documentmodify>`__
- `implement an action over a type of document <#actionimplement>`__


Removing a Document Type
------------------------

How to get there?
~~~~~~~~~~~~~~~~~

Click on the "Remove Doctype" link in the webSubmit admin right menu.

How to do this?
~~~~~~~~~~~~~~~

Select the document type to delete then click on the "Remove
Doctype" button. Remember by doing this, you will delete this
document type as well as all the implementation of actions for this
document type!

See also:
~~~~~~~~~

- `create a type of document <#documentnew>`__
- `modify a type of document <#documentmodify>`__
- `implement an action over a type of document <#actionimplement>`__


Modifying a Document Type
-------------------------

What is it?
~~~~~~~~~~~

     Modifying a document type in webSubmit - this will modify its
    general data description, not the implementations of the actions on
    this document type. For the later, please see `implement an action
    over a type of document <#actionimplement>`__.

How to get there?
~~~~~~~~~~~~~~~~~

     From the main page of the manager, click on the title of the
    document type you want to modify, then click on the "Edit Document
    Type Details".

How to do this?
~~~~~~~~~~~~~~~

     Once here, you can modify 2 fields:
    **Document Type Name**: This is the full name of your new document.
    This is the text which will appear on the list of available
    documents and catalogues on webSubmit main page.
    **Document Type Description**: This is the text which will appear on
    the right of the screen when the user moves the mouse over the
    document type title and on the document type submission page. This
    can be pure text or html.

See also:
~~~~~~~~~

- `remove a type of document <#documentremove>`__
- `create a type of document <#documentnew>`__
- `implement an action over a type of document <#actionimplement>`__

 

 

Actions
-------

In webSubmit you can create several actions (for example "Submit
New Record", "Submit a New File", "Send to a Distribution List",
etc. in fact any action you can imagine to perform on a document
stored in your database). The creation of an action is very simple
and consists in filling in a name, description and associating a
directory to this action. The directory parameter indicates where
the collected data will be stored when the action is carried on.

Once an action is created, you have to implement it over a
document type. Implementing an action means defining the web form
which will be displayed to a user, and defining the treatment (set
of functions) applied to the data which have been gathered. The
implementation of the same action over two document types can be
very different. The fields in the web form can be different as well
as the functions applied at the end of this action.


See also:
~~~~~~~~~

- `create a new action <#actionnew>`__
- `remove an action <#actionremove>`__
- `modify an action <#actionmodify>`__
- `implement an action over a type of document <#actionimplement>`__


Adding a New Action
-------------------

How to get there?
~~~~~~~~~~~~~~~~~

Click on the "Available Actions" link in the websubmit right menu,
then on the "Add an Action" button.

How to do this?
~~~~~~~~~~~~~~~

A new action is defined by 6 fields:

-  **Creation Date** and **Modification Dates** are generated and
   modified automatically.
-  **Action Code**: This is the acronym for your new action. We
   usually use a 3 letters acronym.
-  **Action Description**: This is a short description of the new
   action.
-  **dir**: This is the name of the directory in which the
   submission data will be stored temporarily. If the dir value is
   "running" as for the "Submit New Record" action (SBI), then the
   submission data for a Text Document (document acronym "TEXT")
   will be stored in the
   /opt/invenio/var/data/submit/storage/running/TEXT/9089760\_90540
   directory (where 9089760\_90540 is what we call the submission
   number. It is a string automatically generated at the beginning
   of each submission). Once finished, the submission data will be
   moved to the
   /opt/invenio/var/data/submit/storage/done/running/TEXT/ directory
   by the "Move\_to\_Done" function.
-  **statustext**: text displayed in the status bar of the browser
   when the user moves his mouse upon the action button.


See also:
~~~~~~~~~

- `remove an action <#actionremove>`__
- `modify an action <#actionmodify>`__
- `implement an action over a type of document <#actionimplement>`__


Removing an Action
------------------

What is it?
~~~~~~~~~~~

Removing the implementation of an action over a document type -
Please note the removal of the action itself is not allowed with
this tool.

How to get there?
~~~~~~~~~~~~~~~~~

From the websubmit admin main page, click on the title of the
relevant document type. Then click on the red cross corresponding to
the line of the action you want to remove.

See also:
~~~~~~~~~

- `create an action <#actionnew>`__
- `modify an action <#actionmodify>`__
- `implement an action over a type of document <#actionimplement>`__


Modifying an Action
-------------------

What is it?
~~~~~~~~~~~

This page is about how to modify the general data about an action -
for modifying the implementation of an action over a document type,
see `implement an action over a type of document <#actionimplement>`__

How to get there?
~~~~~~~~~~~~~~~~~

Click on the "View Actions" link in the right menu of the websubmit
admin, then on the title of the action you want to modify...

How to do this?
~~~~~~~~~~~~~~~

You may modify 3 fields:

-  **Action Description**: This is a short description of the new
   action.
-  **dir**: This is the name of the directory in which the
   submission data will be stored temporarily. See the meaning of
   this parameter in `create an action <#actionnew>`__.
-  **statustext**: text displayed in the status bar of the browser
   when the user moves his mouse upon the action button.

See also:
~~~~~~~~~

- `remove an action <#actionremove>`__
- `create an action <#actionnew>`__
- `implement an action over a type of document <#actionimplement>`__


Implement an action over a document type
----------------------------------------

What is it?
~~~~~~~~~~~

Implement an action over a document type. Create the web forms and
the treatment process.

How to get there?
~~~~~~~~~~~~~~~~~

From the main page of the manager, click on the title of the
relevant document type. Then click on the "Add a New Submission" button.

How to do this?
~~~~~~~~~~~~~~~

Just select the name of the action you want to implement. When
you select an action, the list of document which already implement
this action appears. Then you can select from this list the document
from which you want to clone the implementation, or just choose "No
Clone" if you want to build this implementation from scratch.

After selecting the correct fields, click on the "Add
Submission" button.

You then go back to the document type manager page where you can
see that in the bottom array your newly implemented action appears
(check the acronym in the first column).
|image14|

- Clicking on the action acronym will allow you to modify the general
  data about the action (remember in this case that all the other
  implementations of this particular action will also be changed).  -  The
  second column indicates whether the button representing this action will
  appear on the submission page.  -  The third column shows you the number
  of pages composing the web form for this implementation. (see `create
  and maintain the web form <#implementwebform>`__).  -  The 4th and 5th
  columns indicate the creation and last modification dates for this
  implementation.  -  In the 6th column, you can find the order in which
  the button will be displayed on the submission page of this document
  type.  -  The following 4 columns (level, score, stpage, endtxt) deal
  with the insertion of this action in an action set.

.. note:: An action set is a succession of actions which should be done in a
   given order when a user starts.
   For example the submission of a document is usually composed of two
   actions: Submission of Bibliographic Information (SBI) and Fulltext
   Transfer (FTT) which should be done one after the other.
   When the user starts the submission, we want CDS Submit to get him
   first in SBI and when he finishes SBI to carry him to FTT.
   SBI and FTT are in this case in the same action set.
   They will both have a level of 1 ("level" is a bad name, it should
   be "action set number"), SBI will have a score of 1, and FTT a score of
   2 (which means it will be started after SBI). If you set the stpage of
   FTT to 2, the user will be directly carried to the 2nd page of the FTT
   web form. This value is usually set to 1.   | |  The endtxt field
   contains the text which will be display to the user at the end of the
   first action (here it could be "you now have to transfer your files")
   A single action like "Modify Bibliographic Information" should have
   the 3 columns to 0,0 and 1.

-  Click on the icon in the 12th column ("Edit Submission Pages") to
   `create or edit the web form <#implementwebform>`__.
-  Click on the icon in the 13th column ("Edit Functions") to
   `create or edit the function list <#implementfunctions>`__.
-  The "Edit Submission" column allows you to modify the data
   (level, status text...) for this implementation.
-  Finally the last column allows you to delete this implementation.
    
If you chose to clone the implementation from an existing one,
the web form as well as the functions list will already be defined.
Else you will have to create them from scratch.

See also:
~~~~~~~~~

- `create and maintain the web form <#implementwebform>`__
- `create and maintain the data treatment <#implementfunctions>`__
 

Create and maintain the web form
--------------------------------

What is it?
~~~~~~~~~~~

Create and define the web form used during an action.

How to get there?
~~~~~~~~~~~~~~~~~

From the main page of the manager, click on the title of the
relevant document type. Then click on the icon in the "Edit
Submission Pages" column of the relevant line.

List of the form pages
~~~~~~~~~~~~~~~~~~~~~~

A web form can be split over several pages. This is a matter of
easiness for the user: he will have an overview of all form fields
present on the page without having to scroll it. Moreover, each time
the user goes from one page to the other, all entered data are
saved. If he wants to stop then come back later (or if the browser
crashes!) he will be able to get back to the submission at the exact
moment he left it.

Once here:
|image15|

you can see the ordered list of already existing pages in the web
form. In this example there are 4 pages. You can then:

-  Move one page from one place to an other, using the small blue
   arrows under each page number.
-  Suppress one page by clicking on the relevant red cross.
-  Add a page, by clicking the "ADD A PAGE" button!
-  `Edit the content of one page <#onepage>`__ by clicking on the
   page number.
-  Go back to the document main page.

Edit one form page
~~~~~~~~~~~~~~~~~~

Click on a page number, you then arrive to a place where you can
edit this form page.

A form page is composed of a list of form elements. Each of
these form elements is roughly made of an html template and a text
displayed before the form field.

In the first part of the page, you have a preview of what the
form will look like to the user:
|image16|

Then the second table shows you the list of the form elements
present on the page:
|image17|

You can then:

-  Move one element from one place to another using the drop-down
   menus in the first column ("Item No") of the table, or the little
   blue arrows in the second column.
-  `Edit the html template of one form element <#edittemplate>`__ by
   clicking on the name of the template in the 3rd column ("Name").
-  `Edit one of the form elements <#editelement>`__ by clicking on
   the icon in the 10th column.
-  delete one form element by clicking on the relevant red cross.
-  `Add an element to the page <#addelement>`__ by clicking the "ADD
   ELEMENT TO PAGE" button.

Edit the html template of one form element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

     In the html template edition page, you can modify the following
    values:

    -  **Element type**: indicates which html form element to create
    -  **Aleph code**: Aleph users only! - This indicates in which field
       of the Aleph document database to retrieve the original value
       when modifying this information (function
       Create\_Modify\_Interface of action MBI).
    -  **Marc Code**: MySQL users only! - This indicates in which field
       of the MySQL document database to retrieve the original value
       when modifying this information (function
       Create\_Modify\_Interface of action MBI).
    -  **Cookies**: indicates whether WebSubmit will set a cookie on the
       value filled in by the user. If yes, next time the user will come
       to this submission, the value he has entered last time will be
       filled in automatically. Note: This feature has been REMOVED.
    -  **other fields**: The other fields help defining the html form
       element.

    Important warning! Please remember this is a template! This means it
    can be used in many different web forms/implementations. When you
    modify this template the modification will take place in each of the
    implementations this template has been used.

Edit one form element
~~~~~~~~~~~~~~~~~~~~~

In the form element edition page, you may modify the following
values:

-  **element label**: This is the text displayed before the actual
   form field.
-  **level**: can be one of "mandatory" or "optional". If mandatory,
   the user won't be able to leave this page before filling this
   field in.
-  **short desc**: This is the text displayed in the summary window
   when it is opened.
-  **Check**: Select here the `javascript checking
   function <#addcheck>`__ to be applied to the submitted value of
   this field
-  **Modify Text**: This text will be displayed before the form
   field when modifying the value (action "Modify Record", function
   "Create\_Modify\_Interface")

Add one form element
~~~~~~~~~~~~~~~~~~~~

Click on the "ADD ELEMENT TO PAGE" button. There you will have to
decide which `html template field <#addtemplate>`__ to use ("Element
Description code"), and also the field mentioned
`above <#editelement>`__.

Create a new html template
~~~~~~~~~~~~~~~~~~~~~~~~~~

You have access to the list of all existing html templates by
clicking on the "View element descriptions" link in the websubmit
admin right menu.

By clicking on one of them, you will have access to its
description.

If no template corresponds to the one you seek, click on the "ADD
NEW ELEMENT DESCRIPTION" button to create one.
The fields you have to enter in the creation form are the one
described in the `Edit the html template of one form
element <#edittemplate>`__ section.

You also have to choose a name for this new element.
IMPORTANT! The name you choose for your html element is also the
name of the file in which webSubmit will save the value entered in
this field. This is also the one you will use in your
`BibConvert <#bibconvert>`__ configuration. Bibconvert is the
program which will convert the data gathered in webSubmit in a
formatted XML file for insertion in the documents database.

.. note:: Elements of type "select box" which are used as a mandatory field in
          a form must start with "<option>Select:</option>"

Create and edit a checking function.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Click on the "View Checks" link in the websubmit admin right menu.
You then have access to a list of all the defined javascript
functions.

You can then click on the name of the function you want to modify,
or click on the "ADD NEW CHECK" button to create a new javascript
function.

These functions are inserted in the web page when the user is doing
his submission. When he clicks on "next page", this function will be
called with the value entered by the user as a parameter. If the
function returns false, the page does not change and an error
message should be output. If the function returns true, everything
is correct, so page can be changed.

See also:
~~~~~~~~~

- `create and maintain the data treatment <#implementfunctions>`__


Setup the Data Treatment
------------------------

What is it?
~~~~~~~~~~~

At the end of a submission, we have to tell webSubmit what to do
with the data it has gathered. This is expressed through one or
several lists of functions (we call this the "end script").

How to get there?
~~~~~~~~~~~~~~~~~

From the main page of the manager, click on the title of the
relevant document type.
Then click on the icon in the "Edit Functions" column of the
relevant line.

List of functions
~~~~~~~~~~~~~~~~~

Here is what you may see then (this is the end script list of
functions for a document type named "TEST" and action "FTT" -
Fulltext Transfer):
|image18|

You can see the ordered list of all the functions in the end
script. This end script is composed of 2 steps (see the "step"
column). The functions composing the first step are called, then
there should be action from the user which would trigger step 2 - in
the present case the `Upload\_Files <#Upload_Files>`__ function
(last of step 1) allows the user to upload additional files by
creating a web form, then when the user finishes, he presses another
button created by the function, which ends the process. Functions of
step 2 are then called.

Why implement multiple steps? The reason can vary with the task
you want to accomplish. For example with the example above (Fulltext
Transfer), we use the first step to allow the upload of multiple
additional files (dynamic action) which could not be done in the
`static web form <#implementwebform>`__. In the case of the "Modify
Bibliographic Information" action, the first step is used to display
the fields the user wants to modify, prefilled with the existing
values. The reason is once again that the task we want to realise is
dynamic.

The "score" column is used to order the functions. The function
which has the smallest score will be called first, and the largest
score will be called last.

You can then:

-  View and edit the parameters of each function by clicking on the
   name of the function.
-  Move one function up and down, by using the small blue arrows.
-  Suppress one function by clicking on the relevant red cross.
-  Add a function to the list by clicking the "ADD FUNCTION" button.
-  Go back to the document main page ("FINISHED" button).

Please note: To pass one function from one step to another, you
have to delete it then add it again in the proper step.

See also:
~~~~~~~~~

- `all about functions <#functions>`__


Functions
---------

Description:
~~~~~~~~~~~~

In webSubmit, each action process is divided into two phases: the
gathering of data (through a web form) and the treatment of the
data.

The treatment is organised in a succession of functions, each of
which has its own input and output.
The functions themselves are stored in separate files (one per
function) in the
``/opt/invenio/lib/python/invenio/websubmit\_functions`` directory. A
file containing a function MUST be named after the function name
itself. For example, a function called "Move\_to\_Done" MUST be
stored in a file called Move\_to\_Done.py. The case is important
here.

For a description of what should be inside the file, have a look
to the "create a new function" page of this guide.
To each function you can associate one or several parameters,
which may have different values according to the document type the
function is used for. One parameter may be used for different
functions. For example one standard parameter used in several
functions is called "edsrn". It contains the name of the file in
which the reference of the document is stored.

See also:
~~~~~~~~~

- `create a new function <#functionnew>`__
- `delete a function <#functiondelete>`__
- `edit a function <#functionedit>`__


Creating a New Function
-----------------------

How to get there?
~~~~~~~~~~~~~~~~~

     Click on the "Available Functions" link in the websubmit admin
    right menu. Then click on the "Add New Function" button.

How to do this?
~~~~~~~~~~~~~~~

Enter the name of the new function as well as a text description if you wish.
You will then reach a page where you can add parameters to your new function.

Don't forget to add the function file inside the
``/opt/invenio/lib/python/invenio/websubmit\_functions`` directory and
to name the file after the function. Functions must be written in
Python. Here is an example implementation of a function:

``/opt/invenio/lib/python/invenio/websubmit\_functions/Get\_Report\_Number.py``:

::

    def Get_Report_Number (parameters,curdir,form):
        global rn

        if os.path.exists("%s/%s" % (curdir,parameters['edsrn'])):
            fp = open("%s/%s" % (curdir,parameters['edsrn']),"r")
            rn = fp.read()
            rn = rn.replace("/","_")
            rn = re.sub("[\n\r ]+","",rn)
        else:
            rn = ""
        return ""


The function parameters are passed to the function through the parameters dictionary.
The curdir parameter contains the current submission directory path.
The form parameter contains the form passed to the current web page for possible reference from inside the
function.


See also:
~~~~~~~~~

- edit a function
- delete a function


 

        Removing a Function

                Note

                     There are currently no way of deleting a function through this
                    interface. Use the direct MySQL command line interface for this.


                See also:

                        edit a function
                        create a function




         
         

        Editing a Function

                What is it?

                     Edit a function, add parameters to it...


                How to get there?

                     Click on the "Available Functions" link in the websubmit admin
                    right menu.


                How to do this?

                     On this page appears a list of all functions defined into the system.
                    Two columns give you access to some features:

                        View function usage Click here to have access to the list of all document
                        types and all actions in which this function is used. Then by clicking on one of the items, you will be given a
                        chance to modify the parameters value for the given document type.
                        View/Edit function details There you will be able to modify the function
                        description, as well as add/withdraw parameters for this function.




                See also:

                        create a new function
                        delete a function





         
         

        All functions explained

                Description:

                     This page lists and explains all the functions used in the demo
                    provided with the Invenio package. This list is not exhaustive since you can add any new function you need.
                     Click on one function name to get its description.
                     Please note in this page when we refer to [param] this means the
                    value of the parameter 'param' for a given document type.


                        CaseEDS
                        Create_Modify_Interface
                        Create_Recid
                        Finish_Submission
                        Get_Info
                        Get_Recid
                        Get_Report_Number
                        Get_Sysno
                        Get_TFU_Files
                        Insert_Modify_Record
                        Insert_Record


                        Is_Original_Submitter
                        Is_Referee
                        Mail_Submitter
                        Make_Modify_Record
                        Make_Record
                        Move_From_Pending
                        Move_to_Done
                        Move_to_Pending
                        Print_Success
                        Print_Success_APP
                        Print_Success_MBI


                        Print_Success_SRV
                        Report_Number_Generation
                        Send_Approval_Request
                        Send_APP_Mail
                        Send_Modify_Mail
                        Send_SRV_Mail
                        Test_Status
                        Update_Approval_DB
                        Upload_Files






                CaseEDS
                description



                        This function may be used if the treatment to be done after a submission depends on a field entered by
                        the user. Typically this is used in an approval interface. If the referee approves then we do this. If he rejects,
                        then we do other thing.
                        More specifically, the function gets the value from the file named [casevariable] and compares it with the
                        values stored in [casevalues]. If a value matches, the function directly goes to the corresponding step stored
                        in [casesteps]. If no value is matched, it goes to step [casedefault].



                parameters

                    casevariable

                        This parameters contains the name of the file in which the function will get the chosen value.
                        Eg: "decision"



                    casevalues

                        Contains the list of recognized values to match with the chosen value. Should be a comma separated list of words.
                        Eg: "approve,reject"



                    casesteps

                        Contains the list of steps corresponding to the values matched in [casevalue]. It should be a comma
                        separated list of numbers
                        Eg: "2,3"
                        In this example, if the value stored in the file named "decision" is "approved", then the function launches
                        step 2 of this action. If it is "reject", then step 3 is launched.



                    casedefault

                        Contains the step number to go by default if no match is found.
                        Eg: "4"
                        In this example, if the value stored in the file named "decision" is not "approved" nor "reject", then
                        step 4 is launched.







                Create_Modify_Interface
                description



                        To be used in the MBI-Modify Record action.
                        It displays a web form allowing the user to modify the fields he chose. The fields are prefilled with the existing
                        values extracted from the documents database.
                        This functions takes the values stored in the [fieldnameMBI] file. This file contains a list of field name separated
                        with "+" (it is usually generated from a multiple select form field). Then the function retrieves the corresponding
                        tag name (marc-21) stored in the element definition. Finally it displays the web form and fills it with the existing
                        values found in the documents database.



                parameters

                    fieldnameMBI

                        Contains the name of the file in which the function will find the list of fields the user wants to modify. Depends
                        on the web form configuration.








                Create_Recid
                description



                        This function retrieves a new record id from the records database. This record id will then be used to create the
                        XML record afterwards, or to link with the fulltext files. The created id is stored in a file named "SN".



                parameters

                    none








                Finish_Submission
                description



                        This function stops the data treatment process even if further steps exist. This is used for example in the
                        approval action. In the first step, the program determines whether the user approved or rejected the
                        document (see CaseEDS function description). Then depending on  the result, it
                        executes step 2 or step 3. If it executes step 2, then it should continue with step 3 if nothing stopped it. The
                        Finish_Submission function plays this role.



                parameters

                    none








                Get_Info
                description



                        This function tries to retrieve in the "pending" directory or directly in the documents database, some information
                        about the document: title, original submitter's email and author(s).
                        If found, this information is stored in 3 global variables: $emailvalue, $titlevalue, $authorvalue to be used
                        in other functions.
                        If not found, an error message is displayed.



                parameters

                    authorFile

                        Name of the file in which the author may be found if the document has not yet been integrated (in this case
                        it is still in the "pending" directory).



                    emailFile

                        Name of the file in which the email of the original submitter may be found if the document has not yet been
                        integrated (in this case it is still in the "pending" directory).



                    titleFile

                        Name of the file in which the title may be found if the document has not yet been integrated (in this case it is
                        still in the "pending" directory).










                Get_Recid
                description



                        This function searches for the document in the database and stores the recid of this document in the "SN" file and in a global variable "sysno".
                        The function conducts the search based upon the document's report-number (and relies upon the global variable "rn") so the "Get_Report_Number" function should be called before this one.
                        This function replaces the older function "Get_Sysno".



                parameters

                    none









                Get_Report_Number
                description



                        This function gets the value contained in the [edsrn] file and stores it in the reference global variable.



                parameters

                    edsrn

                        Name of the file which stores the reference.
                        This value depends on the web form configuration you did. It should contain the name of the form element used for storing the reference of the document.










                Get_Sysno
                description



                        This function searches for the document in the database and stores the system number of this document in the "SN" file and in a global variable.
                        "Get_Report_Number" should be called before.
                        Deprecated: Use Get_Recid instead.



                parameters

                    none







                Insert_Modify_Record
                description



                        This function gets the output of bibconvert and uploads it into the MySQL bibliographical database.



                parameters

                    none







                Insert_Record
                description



                        This function gets the output of bibFormat and uploads it into the MySQL bibliographical database.



                parameters

                    none








                Is_Original_Submitter
                description



                        If the authentication module (login) is active in webSubmit, this function compares the current login with the email of the original submitter. If it is the same (or if the current user has superuser rights), we go on. If it differs, an error message is issued.



                parameters

                    none






                Is_Referee
                description



                        This function checks whether the currently logged user is a referee for this document.



                parameters

                    none









                Mail_Submitter
                description



                        This function send an email to the submitter to warn him the document he has just submitted has been
                        correctly received.



                parameters

                    authorfile

                        Name of the file containing the authors of the document



                    titleFile

                        Name of the file containing the title of the document



                    emailFile

                        Name of the file containing the email of the submitter of the document



                    status

                        Depending on the value of this parameter, the function adds an additional text to the email.
                        This parameter can be one of:
                        ADDED: The file has been integrated in the database.
                        APPROVAL: The file has been sent for approval to a referee.
                        or can stay empty.



                    edsrn

                        Name of the file containing the reference of the document



                    newrnin

                        Name of the file containing the 2nd reference of the document (if any)









                Make_Modify_Record
                description



                        This function creates the record file formatted for a direct insertion in the documents database. It uses the
                        BibConvert tool.
                        The main difference between all the Make\_...\_Record functions are the parameters.
                        As its name says, this particular function should be used for the modification of a record. (MBI- Modify
                        Record action).



                parameters

                    modifyTemplate

                        Name of bibconvert's configuration file used for creating the mysql record.



                    sourceTemplate

                        Name of bibconvert's source file.











                Make_Record
                description



                        This function creates the record file formatted for a direct insertion in the documents database. It uses the
                        BibConvert tool.
                        The main difference between all the Make\_...\_Record functions are the parameters.
                        As its name does not say :), this particular function should be used for the submission of a document.



                parameters

                    createTemplate

                        Name of bibconvert's configuration file used for creating the mysql record.



                    sourceTemplate

                        Name of bibconvert's source file.









                Move_From_Pending
                description



                        This function retrieves the data of a submission which was temporarily stored in the "pending" directory
                        (waiting for an approval for example), and moves it to the current action directory.



                parameters

                    none








                Move_to_Done
                description



                        This function moves the existing submission directory to the /opt/invenio/var/data/submit/storage/done directory. If the
                        Then it tars and gzips the directory.



                parameters

                    none









                Move_to_Pending
                description



                        This function moves the existing submission directory to the /opt/invenio/var/data/submit/storage/pending directory. It is
                        used to store temporarily this data until it is approved or...



                parameters

                    none









                Print_Success
                description



                        This function simply displays a text on the screen, telling the user the submission went fine. To be used in
                        the "Submit New Record" action.



                parameters

                    status

                        Depending on the value of this parameter, the function adds an additional text to the email.
                        This parameter can be one of:
                        ADDED: The file has been integrated in the database.
                        APPROVAL: The file has been sent for approval to a referee.
                        or can stay empty.



                    edsrn

                        Name of the file containing the reference of the document



                    newrnin

                        Name of the file containing the 2nd reference of the document (if any)











                Print_Success_APP
                description



                        This function simply displays a text on the screen, telling the referee his decision has been taken into account.
                        To be used in the Approve (APP) action.



                parameters

                    none











                Print_Success_MBI
                description



                        This function simply displays a text on the screen, telling the user the modification went fine. To be used in
                        the Modify Record (MBI) action.



                parameters

                    none










                Print_Success_SRV
                description



                        This function simply displays a text on the screen, telling the user the revision went fine. To be used in the
                        Submit New File (SRV) action.



                parameters

                    none








                Report_Number_Generation
                description



                        This function is used to automatically generate a reference number.
                        After generating the reference, the function saves it into the [newrnin] file and sets the global variable
                        containing this reference.



                parameters

                    autorngen

                        If set to "Y": The reference number is generated.
                        If set to "N": The reference number is read from a file ([newrnin])
                        If set to "A": The reference number will be the access number of the submission.



                    counterpath

                        indicates the file in which the program will find the counter for this reference generation.
                        The value of this parameter may contain one of:
                        "<PA>categ</PA>": in this case this string is replaced with the content of the file [altrnin]
                        "<PA>yy</PA>": in this case this string is replaced by the current year (4 digits) if [altyeargen]
                        is set to "AUTO", or by the content of the [altyeargen] file in any other case. (this content should be formatted
                        as a date (dd/mm/yyyy).
                        "<PA>file:name_of_file</PA>": in this case, this string is replaced by the first line of the given file
                        "<PA>file*:name_of_file</PA>": in this case, this string is replaced by all the lines of the given file, separated by a dash ('-') character.




                    rnformat

                        This is the format used by the program to create the reference. The program computes the value of the
                        parameter and appends a "-" followed by the current value of the counter increased by 1.
                        The value of this parameter may contain one of:
                        "<PA>categ</PA>": in this case this string is replaced with the content of the file [altrnin]
                        "<PA>yy</PA>": in this case this string is replaced by the current year (4 digits) if [altyeargen]
                        is set to "AUTO", or by the content of the [altyeargen] file in any other case. (this content should be formatted
                        as a date (dd/mm/yyyy).

                        "<PA>file:name_of_file</PA>": in this case, this string is replaced by the first line of the given file
                        "<PA>file*:name_of_file</PA>": in this case, this string is replaced by all the lines of the given file, separated by a dash ('-') character.




                    rnin

                        This parameter contains the name of the file in which the program will find the category if needed. The content
                        of thif file will then replace the string <PA>categ</PA> in the reference format or in the counter
                        path.



                    yeargen

                        This parameter can be one of:
                        "AUTO": in this case the program takes the current 4 digit year.
                        "<filename>": in this case the program extract the year from the file which name is
                        <filename>. This file should contain a date (dd/mm/yyyy).



                    edsrn

                        Name of the file in which the created reference will be stored.











                Send_Approval_Request
                description



                        This function sends an email to the referee in order to start the simple approval process.
                        This function is very CERN-specific and should be changed in case of external use.
                        Must be called after the Get_Report_Number function.



                parameters

                    addressesDAM

                        email addresses of the people who will receive this email (comma separated list). this parameter may contain the <CATEG> string. In which case the variable computed from the [categformatDAM] parameter replaces this string.
                        eg.: "<CATEG>-email@cern.ch"



                    categformatDAM

                        contains a regular expression used to compute the category of the document given the reference of the document.
                        eg.: if [categformatAFP]="TEST-<CATEG>-.*" and the reference of the document is "TEST-CATEGORY1-2001-001", then the computed category equals "CATEGORY1"



                    authorfile

                        name of the file in which the authors are stored



                    titlefile

                        name of the file in which the title is stored.



                    directory

                        parameter used to create the URL to access the files.











                Send_APP_Mail
                description



                        Sends an email to warn people that a document has been approved.



                parameters

                    addressesAPP

                        email addresses of the people who will receive this email (comma separated list). this parameter may contain
                        the <CATEG> string. In which case the variable computed from the [categformatAFP] parameter
                        replaces this string.
                        eg.: "<CATEG>-email@cern.ch"



                    categformatAPP

                        contains a regular expression used to compute the category of the document given the reference of the
                        document.
                        eg.: if [categformatAFP]="TEST-<CATEG>-.*" and the reference of the document is
                        "TEST-CATEGORY1-2001-001", then the computed category equals "CATEGORY1"



                    newrnin

                        Name of the file containing the 2nd reference of the approved document (if any).



                    edsrn

                        Name of the file containing the reference of the approved document.











                Send_Modify_Mail
                description



                        This function sends an email to warn people a document has been modified and the user his modifications
                        have been taken into account..



                parameters

                    addressesMBI

                        email addresses of the people who will receive this email (comma separated list).



                    fieldnameMBI

                        name of the file containing the modified fields.



                    sourceDoc

                        Long name for the type of document. This name will be displayed in the mail.



                    emailfile

                        name of the file in which the email of the modifier will be found.











                Send_SRV_Mail
                description



                        This function sends an email to warn people a revision has been carried out.



                parameters

                    notefile

                        name of the file in which the note can be found



                    emailfile

                        name of the file containing the submitter's email



                    addressesSRV

                        email addresses of the people who will receive this email (comma separated list). this parameter may contain the <CATEG> string. In which case the variable computed from the [categformatDAM] parameter replaces this string.
                        eg.: "<CATEG>-email@cern.ch"



                    categformatDAM

                        contains a regular expression used to compute the category of the document given the reference of the
                        document.
                        eg.: if [categformatAFP]="TEST-<CATEG>-.*" and the reference of the document is
                        "TEST-CATEGORY1-2001-001", then the computed category equals "CATEGORY1"















                Test_Status
                description



                        This function checks whether the considered document has been requested for approval and is still waiting
                        for approval. It also checks whether the password stored in file "password" of the submission directory
                        corresponds to the password associated with the document..



                parameters

                    none












                Update_Approval_DB
                description



                        This function updates the approval database when a document has just been approved or rejected. It uses
                        the [categformatDAM] parameter to compute the category of the document.
                        Must be called after the Get_Report_Number function.



                parameters

                    categformatDAM

                        It contains the regular expression which allows the retrieval of the category from the reference number.
                        Eg: if [categformatDAM]="TEST-<CATEG>-.*" and the reference is "TEST-CATEG1-2001-001" then the
                        category will be recognized as "CATEG1".












                Upload_Files
                description



                        This function displays the list of already transfered files (main and additional ones), and also outputs an html
                        form for uploading other files (pictures or fulltexts).



                parameters

                    maxsize

                        Maximum allowed size for the transfered files (size in bits)



                    minsize

                        Minimum allowed size for the transfered files (size in bits)



                    iconsize

                        In case the transfered files are pictures (jpg, gif or pdf), the function will automatically try to create icons from them.
                        This parameter indicates the size in pixel of the created icon.



                    type

                        This can be one of "fulltext" or "picture". If the type is set to "picture" then the function will try to create icons
                        (uses the ImageMagick's "convert" tool)





                See also:

                        create a new function
                        delete a function
                        edit a function





         
         

        Protection and Restriction


                Description:

                     In webSubmit, you can restrict the use of some actions on a given
                    document type to a list of users. You can use the webAccess
                    manager for this.
                     Let's say you want to restrict the submission of new TEXT documents
                    to a given user. You should then create a role in webAccess which will authorize the action "submit" over doctype
                    "TEXT" and act "SBI" (Submit new record). You can call this role "submitter_TEXT_SBI" for example.
                    Then link the role to the proper users.
                     Another example: if you wish to authorize a user to Modify the
                    bibliographic data of PICT documents, you have to create a role which authorize the action "submit" over doctype
                    "PICT" and act "MBI". This role can be called "submitter_PICT_MBI" or whatever you want.
                     If no role is defined for a given action and a given document type,
                    then all users will be allowed to use it.





         
         

        Submission Catalogue Organisation

                What is it?

                    This feature allows you to organise the way webSubmit main page
                    will look like. You will be able to group document types inside catalogues and order the catalogues the way you
                    wish.


                How to get there?

                     Click on the "Organisation" link in the websubmit admin right menu.


                How to do this?

                    Once on the "Edit Catalogues page", you will find the currently
                    defined organisation chart in the middle of the page. To the right, one form allows you to create a new catalogue
                    ("Add a Catalogue") and one to add a document type to an existing catalogue ("Add a document type").
                     

                        To add a catalogue: Enter the name of your new catalogue in the
                        "Catalogue Name" free text field then choose to which existing catalogue this one will be attached to. If you
                        attach the new one to an already existing catalogue, you can create a sub-catalogue. To actually create it,
                        click on "ADD".
                        To add a document type to a catalogue: Choose in the list of existing
                        "Document type names" the one you want to add to the chart. Then choose to which catalogue the document
                        type will be associated. Click on "ADD" to finalise this action.
                        To withdraw a document type or a catalogue from the chart: Click on the
                        red cross next to the item you want to withdraw. If you withdraw a catalogue all document types attached to
                        it will be withdrawn also (of course the actual document types in webSubmit won't be destroyed!).
                        To move a document type or a catalogue in the chart: Use the small up
                        and down arrows next to the document type/catalogue title.




                See also:

                        Create a New Document Type
                        document types




         
         

        BibConvert

                What is it?

                     WebSubmit stores the data gathered during a submission in a
                    directory. In this directory each file corresponds to a field saved during the submission.
                     BibConvert is used to create a formatted file which will be easy to
                    upload in the bibliographical database from this directory.
                     This BibConvert program is called from the
                    Make_Record and
                    Make_Modify_Record functions
                    from the end script system of webSubmit.
                     The BibConvert configuration files used by webSubmit are in the
                    /bibconvert/config directory.
                     For more info about bibconvert, please see the dedicated
                    guide.




         
         

        FAQ


             Q1. I'd like to be warned each time there is an error, or an important
            action is made through the manager. Is this possible?

             Q2. Where are all the files stored in this system?

             Q3. How is the documents archive organised?




             Q1. I'd like to be warned each time there is an error, or an important
            action is made through the manager. Is this possible?


                Yes, it is. Edit the invenio-local.conf file, the "CFG_SITE_ADMIN_EMAIL" definition and set it to your email
                address. You will then receive all the warning emails issued by the manager.


             Q2. Where are all the files stored in this system?


                the counter files are here: /opt/invenio/var/data/submit/counters. There are used by the
                Report_Number_Generation
                function.
                all running and completed submissions are stored here: /opt/invenio/var/data/submit/storage.
                all the document files attached to records are stored here: /opt/invenio/var/data/files.
                all python functions used by webSubmit are stored here: /opt/invenio/lib/python/invenio/websubmit_functions


             Q3. How is the documents archive organised?


                First of all, the documents files attached to records are stored here: /opt/invenio/var/data/files.
                The Upload_Files webSubmit function is used
                to link a document with a record.
                All documents get an id from the system and are stored in the "bibdoc" table in the database. The link between a
                document and a record is stored using the "bibdoc_bibrec" table.
                The document id is used to determine where the files are stored. For example the files of document #14 will be
                stored here: /opt/invenio/var/data/files/g0/14
                The subdirectory g0 is used to split the documents accross the filesystem.  The CFG_FILE_DIR_SIZE variable from
                invenio.conf determines how many documents will be stored under one subdirectory.
                Several files may be stored under the same document directory: they are the different formats and versions of the
                same document. Versions are indicated by a string of the form ";1.0" concatenated to the name of the file.
                Please see the HOWTO Manage Fulltext Files for more information on the administrative command line tools available to manipulate fulltext files.



            See also:

                    notes



.. |image0| image:: /_static/admin/websubmit-admin-guide-workflow1.png
.. |image1| image:: /_static/admin/websubmit-admin-guide-workflow2.png
.. |image2| image:: /_static/admin/websubmit-admin-guide-workflow3.png
.. |image3| image:: /_static/admin/websubmit-admin-guide-screenshot1-small.png
.. |image4| image:: /_static/admin/websubmit-admin-guide-screenshot2-small.png
.. |image5| image:: /_static/admin/websubmit-admin-guide-screenshot3-small.png
.. |image6| image:: /_static/admin/websubmit-admin-guide-screenshot4-small.png
.. |image7| image:: /_static/admin/websubmit-admin-guide-workflow4b.png
.. |image8| image:: /_static/admin/websubmit-admin-guide-page0.jpg
.. |main_menu| image:: /_static/admin/websubmit-admin-guide-main_menu.png
.. |menu_doc| image:: /_static/admin/websubmit-admin-guide-menu_doc.png
.. |form| image:: /_static/admin/websubmit-admin-guide-form.png
.. |end_action| image:: /_static/admin/websubmit-admin-guide-end_action.png
.. |image13| image:: /_static/admin/websubmit-admin-guide-main_page.png
.. |image14| image:: /_static/admin/websubmit-admin-guide-implement.png
.. |image15| image:: /_static/admin/websubmit-admin-guide-menu_page.png
.. |image16| image:: /_static/admin/websubmit-admin-guide-preview.png
.. |image17| image:: /_static/admin/websubmit-admin-guide-elements.png
.. |image18| image:: /_static/admin/websubmit-admin-guide-list_functions.png
