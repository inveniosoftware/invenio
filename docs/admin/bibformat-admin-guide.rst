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

.. _bibformat-admin-guide:

BibFormat Admin Guide
=====================

Contents
--------

-  **1. `Overview <#shortIntro>`__**

   -  1.1  \ `How BibFormat works <#philosophy>`__
   -  1.2  \ `Short Tutorial <#tutorial>`__
   -  1.3  \ `Administer Through the Web Interface or Through the
      Configuration files <#administerWebFile>`__

-  **2. `Configure Output Formats <#outputFormats>`__**

   -  2.1  \ `Add an Output Format <#addOutputFormat>`__
   -  2.2  \ `Remove an Output Format <#removeOutputFormat>`__
   -  2.3  \ `Edit the Rules of an Output Format <#rulesOutputFormat>`__
   -  2.4  \ `Edit the Attributes of an Output
      Format <#attrsOutputFormat>`__
   -  2.5  \ `Check the Dependencies an Output
      Format <#dependenciesOutputFormat>`__
   -  2.6  \ `Check the Validity an Output
      Format <#validityOutputFormat>`__

-  **3. `Configure Format Templates <#formatTemplates>`__**

   -  3.1  \ `Add a Format Template <#addFormatTemplate>`__
   -  3.2  \ `Remove a Format Template <#removeFormatTemplate>`__
   -  3.3  \ `Edit the Code of a Format
      Template <#codeFormatTemplate>`__
   -  3.4  \ `Basic Editing <#editFormatTemplate>`__
   -  3.5  \ `Use Format Elements <#elementsInFormatTemplate>`__
   -  3.6  \ `Preview a Format Template <#previewFormatTemplate>`__
   -  3.7  \ `Internationalization
      (i18n) <#internationalizationTemplate>`__
   -  3.8  \ `Escaping special HTML/XML
      characters <#escapeFormatTemplate>`__
   -  3.9  \ `Edit the Attributes of a Format
      Template <#attrsFormatTemplate>`__
   -  3.10 \ `Check the Dependencies of a Format
      Template <#dependenciesFormatTemplate>`__
   -  3.11 \ `Check the Validity a Format
      Template <#validityFormatTemplate>`__
   -  3.12 \ `XSL Format Templates <#xslFormatTemplate>`__

-  **4. `Configure Format Elements <#FormatElements>`__**

   -  4.1  \ `Add a Format Element <#addFormatElement>`__
   -  4.2  \ `Remove a Format Element <#removeFormatElement>`__
   -  4.3  \ `Edit the Code of a Format Element <#codeFormatElement>`__
   -  4.4  \ `Preview a Format Element <#previewFormatElement>`__
   -  4.5  \ `Internationalization
      (i18n) <#internationalizationFormatElement>`__
   -  4.6  \ `Escaping special HTML/XML
      characters <#escapeFormatElement>`__
   -  4.7  \ `Edit the Attributes of a Format
      Element <#attrsFormatElement>`__
   -  4.8  \ `Check the Dependencies of a Format
      Element <#dependenciesFormatElement>`__
   -  4.9  \ `Check the Validity of a Format
      Element <#validityFormatElement>`__
   -  4.10 \ `Browse the Format Elements
      Documentation <#browseDocFormatElement>`__

-  **5. `Run BibReformat <#BibReformat>`__**

   -  5.1  \ `Run BibReformat <#runBibReformat>`__

-  **6. `Appendix <#Appendix>`__**

   -  6.1  \ `MARC Notation in Formats <#marcNotation>`__
   -  6.2  \ `Migrating from Previous BibFormat <#migration>`__
   -  6.3  \ `Integrating BibFormat into Dreamweaver
      MX <#integrationDreamweaver>`__
   -  6.4  \ `FAQ <#faq>`__

1. Overview
-----------

1.1 How BibFormat Works
~~~~~~~~~~~~~~~~~~~~~~~

BibFormat is in charge of formatting the bibliographic records that are
displayed to your users. It is called by the search engine when it has
to format a record.

As you might need different kind of formatting depending on the type
of record, but potentially have a huge amount of records in your
database, you cannot specify for each of them how they should look.
Instead BibFormat uses a rule-based decision process to decide how to
format a record.

The best way to understand how BibFormat works is to have a look at a
typical workflow:

Step 1:

|Use output format HD|

When Invenio has to display a record, it asks BibFormat to format the
record with the given output format and language. For example here the
requested output format is hd, which is a short code for "HTML
Detailed". This means that somehow a user arrived on the page of the
record and asked for a detailed view of the record.

--------------

Step 2:

1. Use Template [Picture HTML Detailed] if tag [980\_\_a] is equal to [PICTURE]
2. Use Template [Thesis HTML detailed] if tag [980\_\_a] is equal to [THESIS]
3. By default use [Default HTML Detailed]|

|BibFormat Guide BFO HD rules|

Beside is a screenshot of the "hd" or "HTML Detailed" output format.
You can see that the output format does not specify how to format the
record, but contains a set of rules which define which template must be
used.

The rules are evaluated from top to bottom. Each rule defines a
condition on a field of the record, and a format template to use to
format the record if the condition matches. Let's say that the field
980\_\_a of the record is equal to "Picture". Then first rules matches,
and format template Picture HTML Detailed is used for formatting by
BibFormat.

You can add, remove or edit output formats
`here </admin/bibformat/bibformatadmin.py/output_formats_manage>`__

--------------

Step 3:

::

    <h1 align="center"><BFE_MAIN_TITLE/></h1>
    <p align="center">
        <BFE_AUTHORS separator="; "  link="yes"/><br/>
        <BFE_DATE format="%d %B %Y"> .- <BFE_NB_PAGES suffix="p">
    </p>

We see an extract of the Picture HTML Detailed format on the right, as
it is shown in the template editor. As you can see it is mainly written
using HTML. There are however some tags that are not part of standard
HTML. Those tags that starts with *<BFE\_* are placeholders for the
record values. For example <BFE\_MAIN\_TITLE/> tells BibFormat to write
the title of the record. We call these tags "elements". Some elements
have parameters. This is the case of the <BFE\_AUTHORS> element, which
can take *separator* and *link* as parameters. The value of separator
will be used to separate authors' names and the link parameter tells if
links to authors' websites have to be created. All elements are
described in the `elements
documentation </admin/bibformat/bibformatadmin.py/format_elements_doc>`__.

You can add, remove or edit format templates
`here </admin/bibformat/bibformatadmin.py/format_templates_manage>`__.

In addition to this modified HTML language, BibFormat also supports XSL
stylesheets as format templates. Read the `XSL Format
Templates <#xslFormatTemplate>`__ section to learn more about XSLT
support for your format templates.

--------------

Step 4:

::

    def format_element(bfo, separator='; ', link='no'):
        """Prints the list of authors for the record

        @param separator a character to separate the authors
        @param link if 'yes' print HTML links to authors          
        """          
        authors = bfo.fields("100__a")          
        if link == 'yes':             
        authors = map(lambda x: '<a href="'+CFG_SITE_URL+'/search?f=author&p='
                      + quote(x) +'">' + x + '</a>', authors)          
        return authors.split(separator)


A format element is written in Python. It acts as a bridge between the
record in the database and the format template. Typically you will not
have to write or read format elements, just call them from the
templates. Each element outputs some text that is written in the
template where it is called.

Developers can add new elements by creating a new file, naming it
with the name of element, and write a Python ``format_element`` function
that takes as parameters the parameters of the elements plus a special
one ``bfo``. Regular Python code can be used, including import of other
modules.

In summary BibFormat is called by specifying a record and an output
format, which relies on different templates to do the formatting, and
which themselves rely on different format elements. Only developers need
to modify the format elements layer.

Output Format

Template

Template

Format Element

Format Element

Format Element

Format Element

You should now understand the philosophy behind BibFormat.

1.2 Short Tutorial
~~~~~~~~~~~~~~~~~~

Let's try to create our own format. This format will just print the
title of a record.

First go to the main `BibFormat admin
page </admin/bibformat/bibformatadmin.py>`__. Then
click on the "Manage Ouput Format" links. You will see the list of all
output formats:

|Output formats management page|

This is were you can delete, create or check output formats. The menu
at the top of the page let you go to other admininistration pages.

Click on the "Add New Output Format" button at the bottom of the
page. You can then fill in some attributes for the output format. Choose
"title" as code, "Only Title" as name and "Prints only title" as
description:

|Screenshot of the Update Output Format Attributes page|

Leave other fields blank, and click on the button "Update Output
format Attributes".

You are then redirected to the rules editor. Notice the menu at the
top which let you close the editor, change the attributes again and
check the output format. However do not click on these links before
saving your modification of rules!

|Output format menu|

As our format does not need to have a different behaviour depending on
the record, we do not need to add new rules to the format. You just need
to select a format template in the "By default use" list. However we
first have to create our special format template that only print titles.
So close the editor using the menu at the top of the page, and in the
menu that just appeared instead, click on "Manage Format Templates". In
a similar way to output formats, you see the list of format templates.

|Format template management page|

Click on the "Add New Format Template" button at the bottom of the page.
As for the output format, fill in the attributes of the template with
name "Title" and any relevant description.

|update format template attributes|

Click on the "Update Output Format Attributes" button. You are
redirected to the template editor. The editor is divided in three parts.
The upper left part contains the code of the template. The bottom part
is a preview of the template. The part on the right side is a short
remainder of the format elements you can use in you template. You can
hide this documentation by clicking on "Hide Documentation".

|Format template editor|

The above screenshot shows the template code already filled in. It calls
the ``BFE_TITLE`` element. If you do not know the name of the element
you want to call, you can search for it using the embedded documentation
search. You can try to add other elements into your template, or write
some HTML formatting.

When you are satisfied with your template, click on the save button,
close the editor and go back to the "Only titles" output format rules
editor. There select the template you have just created in the "Use by
default" menu and save the ouput format and you are done.

This tutorial does not cover all aspects of the management of formats.
It also does not show all the power of output formats, as the one we
have created simply call a template. However you have seen enough to
configure BibFormat trough the web interface. Read the sections below to
learn more about it.

1.3 Administer Through the Web Interface or Through the Configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BibFormat can be administered in two ways. The first way is to use the
provided web interface. It should be the most convenient way of doing
for most users. The web interface is simple to use and provides great
tools to manage your formats. Its only limitation concerns the format
elements, which cannot be modified using it (But the web interface
provide a dynamically generated documentation of your elements).

The other way to administer BibFormat is to directly modify the
configuration files using your preferred text editor. This way of doing
can bring much power to advanced users, but requires an access to the
server's files. It also requires that the user double-check his
modifications, or use the web interface to ensure the validity and
correctness of his formats.

In this manual we will show both ways of doing. For each explication we
show first how to do it through the web interface, then how to do it by
manipulating the configuration files. Non-power users can stop reading
as soon as they encounter the text "For developers and adventurers
only".

We generally recommend to use the web interface, excepted for writing
format elements.

2. Output Formats
-----------------

As you potentially have a huge amount of bibliographic records, you
cannot specify manually for each of them how it should be formatted.
This is why you can define rules that will allow BibFormat to understand
which kind of formatting to apply to a given record. You define this set
of rules in what is called an "output format".

You can have different output formats, each with its own
characteristics. For example you certainly want that when multiple
bibliographic records are displayed at the same time (as it happens in
search results), only short versions are shown to the user , while a
detailed record is preferable when a single record is displayed,
whatever the type of the record.

You might also want to let your users decide which kind of output
they want. For example you might need to display HTML for regular web
browsing, but would also give a BibTeX version of the bibliographic
reference for direct inclusion in a LaTeX document.

To summarize, an output format groups similar kind of formats,
specifying which kind of formatting has to be done, but not how it has
to be done.

2.1 Add an Output Format
~~~~~~~~~~~~~~~~~~~~~~~~

To add a new output format, go to the `Manage Output
Formats </admin/bibformat/bibformatadmin.py/output_formats_manage>`__
page and click on the "Add New Output Format" button at the bottom of
the page. The format has been created. You can then specify the
attributes of the output format. See `Edit the Attributes of an Output
Format <#attrsOutputFormat>`__ to learn more about it.

**For developers and adventurers only:**

Alternatively you can directly add a new output format file into the
/etc/bibformat/outputs/ directory of your Invenio installation, if you
have access to the server's files. Use the format extension .bfo for
your file.

You should also check that user ``www-data`` has read/write access to
the file, if you want to be able to modify the rules through the web
interface.

2.2 Remove an Output Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove an output format, go to the `Manage Output
Formats </admin/bibformat/bibformatadmin.py/output_formats_manage>`__
page and click on the "Delete" button facing the output format you want
to delete. If you cannot click on the button (the button is not
enabled), this means that you do not have sufficent priviledge to do so
(Format is protected. Contact the administrator of the system).

**For developers and adventurers only:**

You can directly remove an output format from the
/etc/bibformat/outputs/ directory of your Invenio installation. However
you must make sure that it is removed from the tables ``format`` and
``formatname`` in the database, so that other modules know that it is
not longer available.

2.3 Edit the Rules of an Output Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you create a new output format, you can at first only specify the
default template, that is the one which is used when all rules fail. In
the case of a basic output format, this is enough. You can however add
other rules, by clicking on the "Add New Rule" button.

Once you have added a rule, you can fill it with a condition, and a
template that should be used if the condition is true. For example the
rule

|Rule: Use template Picture HTML Detailed if field 980__a is equal to PICTURE|

will use template named "Picture HTML Detailed" if the field
``980__a`` of the record to format is equal to "Picture". Note that text
"PICTURE" will match any letter case like "picture" or "Picture".
Leading and trailing spaces are ignored too (" Picture " will match
"PICTURE").

**Tips:** you can use a regular expression as text. For example
"PICT.\*" will match "pictures" and "PICTURE".

|Reorder rules using arrows|

The above configuration will use format template "Default HTML Detailed"
if all above rules fail (in that case if field 980\_\_a is different
from "PICTURE"). If you have more rules, you decide in which order the
conditions are evaluated. You can reorder rules by clicking on the small
arrows on the left of the rules.

Note that when you are migrating your output formats from the old PHP
BibFormat, you might not have translated all the formats to which your
output formats refers. In that case you should use
``defined in old BibFormat`` option in the format templates menu, to
make BibFormat understand that a match for this rule must trigger a call
to the *Behaviour* of the old BibFormat. See section on `Run old and new
formats side by side <#runSideBySide>`__ for more details on this.

**For developers and adventurers only:**

To write an output format, use the following syntax:

First you define which field code you put as the conditon for the
rule. You suffix it with a column. Then on next lines, define the values
of the condition, followed by --- and then the filename of the template
to use:

::

      tag 980__a:
      PICTURE --- PICTURE_HTML_BRIEF.bft
      PREPRINT --- PREPRINT_HTML_BRIEF.bft
      PUBLICATION --- PUBLICATION_HTML_BRIEF.bft

This means that if value of field 980\_\_a is equal to PICTURE, then we
will use format template PICTURE\_HTML\_BRIEF.bft. Note that you must
use the filename of the template, not the name. Also note that spaces at
the end or beginning are not considered. On the following lines, you can
either put other conditions on tag 980\_\_a, or add another tag on which
you want to put conditions.

At the end you can add a default condition:

::

       default: PREPRINT_HTML_BRIEF.bft

which means that if no condition is matched, a format suitable for
Preprints will be used to format the current record.

The output format file could then look like this:

::

      tag 980__a:
      PICTURE --- PICTURE_HTML_BRIEF.bft
      PREPRINT --- PREPRINT_HTML_BRIEF.bft
      PUBLICATION --- PUBLICATION_HTML_BRIEF.bft

      tag 8560_f:
      .*@cern.ch --- SPECIAL_MEMBER_FORMATTING.bft

      default: PREPRINT_HTML_BRIEF.bft

You can add as many rules as you want. Keep in mind that they are read
in the order they are defined, and that only first rule that matches
will be used. Notice the condition on tag 8560\_f: it uses a regular
expression to match any email address that ends with @cern.ch (the
regular expression must be understandable by Python)

2.4 Edit the Attributes of an Output Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An output format has the following attributes:

-  ``code``: a short identifier that is used to identify the output
   format. It must be unique and contain a maximum of 6 letters. Note
   that the **code is not case sensitive** ("HB" is equal to "hb").
-  ``content type``: this is the content type of the format, specified
   in Mime. For example if you were to produce an Excel output, you
   could use ``application/ms-excel`` as content type. If a content type
   is specified, Invenio will not print the usual header and footerfor
   the page, but will trigger a download in the client's browser when
   viewing the page (Unless the browser handles this content type).
-  ``name``: a generic name to display in the interface for this output
   format.
-  (\*) ``name``: internationalized names for the output format, used
   for displaying localized name in the search interface.
-  ``description``: an optional description for the output format.

**Please read this information regarding output format codes:** There
are some reserved codes that you should not use, or at least be aware of
when choosing a code for your output format. The table below summarizes
these special words:

+--------------------------------------+--------------------------------------+
| Code Purpose                         |                                      |
+======================================+======================================+
| HB                                   | HD                                   |
| Used for displaying list of results  | Used when no format is specified     |
| of a search.                         | when viewing a record.               |
+--------------------------------------+--------------------------------------+

**For developers and adventurers only:**

Excepted for the code, output format attributes cannot be changed in the
output format file. These attributes are saved in the database. As for
the ``code``, it is the name of the output format file, without its
``.bfo`` extension. If you change this name, do not forget to propagate
the modification in the database.

2.5 Check the Dependencies an Output Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check the dependencies of an output format on format templates,
format elements and tags, go to the `Manage Output
Formats </admin/bibformat/bibformatadmin.py/output_formats_manage>`__
page, click on the output format you want to check, and then in the menu
click on "Check Dependencies".

|Check Dependencies menu|

The next page shows you:

- the format templates which might be called by the rules of the output format
- the elements used in each of these templates
- the Marc tags involved in these elements

Note that some Marc tags might be omitted.

2.6 Check the Validity an Output Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check the validity of an output format, simply go to the `Manage Output
Formats </admin/bibformat/bibformatadmin.py/output_formats_manage>`__
page, and look at the column 'status' for the output format you want to
check. If message "Ok" is there, then no problem was found with the
output format. If message 'Not Ok' is in the column, click on it to see
the problems that have been found for the output format.

3. Format Templates
-------------------

A format template defines how a record should be formatted. For example
it specifies which fields of the record are to be displayed, in which
order and with which visual attributes. Basically the format template is
written in HTML, so that it is easy for anyone to edit it. BibFormat
also has support for XSLT for formatting. Read more `about XSL format
templates here <#xslFormatTemplate>`__.

3.1 Add a Format Template
~~~~~~~~~~~~~~~~~~~~~~~~~

To add a new format template, go to the `Manage Format
Templates </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page and click on the "Add New Format Template" button at the bottom of
the page. The format has been created. You can then specify the
attributes of the format template, or ask to make a copy of an existing
format. See `Edit the Attributes of a Format
Template <#attrsFormatTemplate>`__ to learn more about editing the
attributes.

**For developers and adventurers only:**

Alternatively you can directly add a new format template file into the
/etc/bibformat/format\_templates/ directory of your Invenio
installation, if you have access to the server's files. Use the format
extension .bft for your file.

You should also check that user ``www-data`` has read/write access to
the file, if you want to be able to modify the code and the attributes
of the template through the web interface.

3.2 Remove a Format Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove a format template, go to the `Manage Format
Templates </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page and click on the "Delete" button facing the format template you
want to delete. If you cannot click on the button (the button is not
enabled), this means that you do not have sufficent priviledge to do so
(Format is protected. Contact the administrator of the system).

**For developers and adventurers only:**

You can directly remove the format template from the
/etc/bibformat/format\_templates/ directory of your Invenio
installation.

3.3 Edit the Code of a Format Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can change the formatting of records by modifying the code of a
template.

To edit the code of a format template go to the `Manage Format
Templates </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page. Click on the format template you want to edit to load the template
editor.

The format template editor contains three panels. The left upper panel
is the code editor. This is were you write the code that specifies the
formatting of a template. The right-most panel is a short documentation
on the "bricks" you can use in your format template code. The panel at
the bottom of the page allows you to preview the template.

|Template Editor Page|

The following sections explain how to write the code that specifies the
formatting.

3.4 Basic Editing
^^^^^^^^^^^^^^^^^

The first thing you have to know before editing the code is that
everything you write in the code editor is printed as such by BibFormat.
Well almost everything (as you will discover later).

For example if you write "My Text", then for every record the output
will be "My Text". Now let's say you write "<b>My Text</b>": the output
will still be "<b>My Text</b>", but as we display in a web browser, it
will look like "**My Text**\ " (The browser interprets the text inside
tags <b></b> as "bold". Also note that the look may depend on the CSS
style of your page).

Basically it means that you can write HTML to do the formatting. If you
are not experienced with HTML you can use an HTML editor to create your
layout, and the copy-paste the HTML code inside the template.

Do not forget to save your work by clicking on the save button before
you leave the editor!

**For developers and adventurers only:**

You can edit the code of a template using exactly the same syntax as in
the web interface. The code of the template is in the template file
located in the /etc/bibformat/format\_templates/ directory of your
Invenio installation. You just have to take care of the attributes of
the template, which are saved in the same file as the code. See `Edit
the Attributes of a Format Template <#attrsFormatTemplate>`__ to learn
more about it.

3.5 Use Format Elements
^^^^^^^^^^^^^^^^^^^^^^^

To add a dynamic behaviour to your format templates, that is display for
example a different title for each record or a different background
color depending on the type of record, you can use the format elements.

Format elements are the smart bricks you can copy-paste in your code to
get the attributes of template that change depending on the record. A
format element looks like a regular HTML tag.

For example, to print the title of a record, you can write
``<BFE_TITLE />`` in your template code where you want to diplay the
title

Format elements can take values as parameters. This allows to customize
the behaviour of an element. For example you can write
``<BFE_TITLE prefix="Title: " />``, and BibFormat will take care of
printing the title for you, with prefix "Title: ". The difference
between ``Title: <BFE_TITLE />`` and ``<BFE_TITLE prefix="Title: " />``
is that the first option will always write "Title: " while the second
one will only print "Title: " if there exist a title for the record in
the database. Of course there are chances that there is always a title
for each record, but this can be useful for less common fields.

Some parameters are available for all elements. This is the case for the
following ones:

-  ``prefix``: a prefix printed only if the record has a value for the
   element.
-  ``suffix``: a suffix printed only if the record has a value for the
   element.
-  ``default``: a default value printed if the record has no value for
   the element. In that case ``prefix`` and ``suffix`` are not printed.

Some parameters are specific to elements. To get information on all
available format elements you can read the `Format Elements
Documentation </admin/bibformat/bibformatadmin.py/format_elements_doc>`__,
which is generated dynamically for all existing elements. it will show
you what the element do and what parameters it can take.

While format elements looks like HTML tags, they differ in the
followings ways from traditional ones:

-  A format element is a single tag: you cannot have
   ``<BFE_TITLE >some text<BFE_TITLE />`` but only ``<BFE_TITLE />``.
-  The values of the parameters accept any characters, including < and
   >. The only limitation is that you cannot use the type of quotes that
   delimit that value: you can have for example
   ``<BFE_TITLE someParam="a lot of single quotes ' ' ' ' "/>`` or
   ``<BFE_TITLE someParam='a lot of double quotes " " " '/>``, but not
   ``<BFE_TITLE someParam="a lot of same quotes as delimiter " " " "/>``.
-  Format elements names always start with ``BFE_``.
-  Format element can expand on multiple lines.

**Tips:** you can use the special element ``<BFE_FIELD tag="" />`` to
print the value of any field of a record in your templates. This
practice is however not recommended because it would necessitate to
revise all format templates if you did change the meaning of the MARC
code schema.

3.6 Preview a Format Template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To preview a format template go to the `Manage Format
Templates </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page and click on the format template you want to preview to open the
template editor. The editor contains a preview panel at the bottom of
the page.

|Preview Panel|

Simply click on " Reload Preview" button to preview the template (you
do not need to save the code before previewing).

Use the "Language" menu to preview the template in a given language

You can fill in the "Search Pattern" field to preview a specific record.
The search pattern uses exactly the same syntax as the one used in the
web interface. The only difference with the regular search engine is
that only the first matching record is shown.

**For developers and adventurers only:**

If you do not want to use the web interface to edit the templates but
still would like to get previews, you can open the preview frame of any
format in a new window/tab. In this mode you get a preview of the
template (if it is placed in the /etc/bibformat/format\_templates/
directory of your Invenio installation). The parameters of the preview
are specified in the url:

-  ``bft``: the filename of the format template to preview
-  ``ln``: the language to use for the preview
-  ``pattern_for_preview``: the search pattern to use for the preview

3.7 Internationalization (i18n)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add translations to your format templates. To do so enclose the
text you want to localize with tags corresponding to the two letters of
the language. For example if we want to localize "title", write
``<en>Title</en>``. Repeat this for each language in which you want to
make "title" available: ``<en>Title</en><fr>Titre</fr><de>Titel</de>``.
Finally enclose everything with ``<lang> </lang>`` tags:
``<lang><en>Title</en><fr>Titre</fr><de>Titel</de></lang>``

For each <lang> group only the text in the user's language is displayed.
If user's language is not available in the <lang> group, your default
Invenio language is used.

3.8 Escaping special HTML/XML characters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, BibFormat escapes all values returned by format elements. As
a format template designer, you can assume in almost all cases that the
values you get from a format element will be escaped for you. For
special cases, you can set the parameter ``escape`` of the element to
'0' when calling it, to make BibFormat understand that it must not
escape the values of the element, or to '1' to force the escaping.

See the `complete list of escaping modes <#listofescapingmodes>`__.

For example ``<bfe_abstract />`` will return:

::

    [...]We find that for spatially-flat cosmologies, background lensing
    clusters with reasonable mass-to-light ratios lying in the
    redshift range 0&lt;1 are strongly excluded, [...]

while ``<bfe_abstract escape="0"/>`` will return:

::

    [...]We find that for spatially-flat cosmologies, background lensing
    clusters with reasonable mass-to-light ratios lying in the
    redshift range 0<1 are strongly excluded, [...]

In most cases, you will not set ``escape`` to 1, nor 0, but just let the
developer of the element take care of that for you.

Please note that values given in special parameters ``prefix``,
``suffix``, ``default`` and ``nbMax`` are never escaped, whatever the
value of ``escape`` is (but other parameters will). You have to take
care of that in your format template, as well as of all other values
that are not returned by the format elements.

3.9 Edit the Attributes of a Format Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To edit the attributes of a format template go to the `Manage Format
Templates </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page, click on the format template you want to edit, and then in the
menu click on "Modify Template Attributes".

A format template contains two attributes:

-  ``Name``: the name of the template
-  ``Description``: a short description of the template

Note that changing these parameters has no impact on the formatting.
Their purpose in only to document the template.

If the name you have chosen already exists for another template, you
name will be suffixed with an integer so that the name is unique.

You should also be aware that if you change the name of a format
template, all output formats that were linking to this template will be
changed to match the new name.

**For developers and adventurers only:**

You can change the attributes of a template by editing its file in the
/etc/bibformat/format\_templates/ directory of your Invenio
installation. The attributes must be enclosed with tags
``<name> </name>`` and ``<description> </description>`` and should
ideally be placed at the beginning of the file.

Also note that the admin web interface tries to keep the name of the
template in sync with the filename of the template. If the name is
changed through the web interface, the filename of the template is
changed, and all output formats that use this template are updated. You
have to do update output formats manually if you change the filename of
the template without the web interface.

3.10 Check the Dependencies of a Format Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check the dependencies of a format template go to the `Manage Format
Template </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page, click on the format template you want to check, and then in the
menu click on "Check Dependencies".

|Check Dependencies menu|

The next page shows you:

-  The output formats that use this format template
-  the elements used in the template (and Marc tags use in these
   elements in parentheses)
-  A summary of all the Marc tags involved in the elements of the
   template

Note that some Marc tags might be omitted.

3.11 Check the Validity a Format Template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check the validity of a format template, simply go to the `Manage
Format
Templates </admin/bibformat/bibformatadmin.py/format_templates_manage>`__
page, and look at the column 'status' for the format template you want
to check. If message "Ok" is there, then no problem was found with the
template. If message 'Not Ok' is in the column, click on it to see the
problems that have been found for the template.

3.12 XSL Format Templates
~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the HTML-like syntax introduced in previous sections,
BibFormat also has support for server-side XSL transformation. Although
you can do all the formatting using this custom HTML syntax, there are
cases where an XSL stylesheet might be preferred. XSLT is for example a
natural choice when you need to output complex XML, especially when your
XML has a deep tree structure. You might also prefer using XSLT if you
already feel comfortable with XSL syntax.

XSL format templates are written using regular XSL. The template file
has to be placed in the same folder as regular format template files,
and its file extension must be ``.xsl``. The XSL template are also
visible through the web interface, as any regular format template file.
However, some functions like the "Dependencies checker" or the
possibility to create a template or edit its attributes are not
available for the XSL templates.

In BibFormat XSL you have access to the following functions, provided
you have declared ``xmlns:fn="http://cdsweb.cern.ch/bibformat/fn"`` in
your stylesheet:

**``fn:modification_date(recID)``**
    Returns the record modification date. Eg:
    ``<xsl:value-of select="fn:modification_date(445)"/>`` returns
    modification date of record 445

**``fn:creation_date(recID)``**
    Returns the record creation date. Eg:
    ``<xsl:value-of select="fn:creation_date(445)"/>`` returns creation
    date of record 445

**``fn:eval_bibformat(recID, bibformat_template_code)``**
    Returns the results of the evaluation of the format template code.
    Eg:
    ``<xsl:value-of select="fn:eval_bibformat(marc:controlfield[@tag='001'],'&lt;BFE_SERVER_INFO var=&quot;recurl&quot;>')" />``
    returns the url of the current record. The parameter
    ``bibformat_template_code`` is regular code used inside BibFormat
    format templates, with ``<`` escaped as ``&lt;`` and ``"``\ (quotes)
    escaped as ``&quot;``

Finally, please note that you will need to install a supported XSLT
parser in order to format using XSL stylesheets.

4. Format Elements
------------------

Format elements are the bricks used in format templates to provide
dynamic content to the formatting process. Their purpose is to allow non
computer literate persons to easily integrate data from the records in
the database into their templates.

Format elements are typically written in Python (there is an exception
to that point which is dicussed in `Add a Format
Element <#addFormatElement>`__). This brings great flexibily and power
to the formatting process. This however restricts the creation of format
elements to developers.

4.1 Add a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~

The most typical way of adding a format element is to drop a ``.py``
file in the lib/python/invenio/bibformat\_elements directory of your
Invenio installation. See `Edit the Code of a Format
Element <#codeFormatElement>`__ to learn how to implement an element.

The most simple way to add a format element is to add a en entry in the
"`Logical
Fields </admin/bibindex/bibindexadmin.py/field>`__\ "
management interface of the BibIndex module. When BibFormat cannot find
the Python format element corresponding to a given name, it looks into
this table for the name and prints the value of the field declared for
this name. This lightweight way of doing is straightforward but does not
allow complex handling of the data (it limits to printing the value of
the field, or the values of the fields if multiple fields are declared
under the same label).

4.2 Remove a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove a Python format element simply remove the corresponding file
from the lib/python/invenio/bibformat\_elements directory of your
Invenio installation.

To remove a format element declared in the "`Logical
Fields </admin/bibindex/bibindexadmin.py/field>`__\ "
management interface of the BibIndex module simply remove the entry from
the table.

4.3 Edit the Code of a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section only applies to Python format elements. Basic format
elements declared in "`Logical
Fields </admin/bibindex/bibindexadmin.py/field>`__\ "
have non configurable behaviour.

A format element file is like any regular Python program. It has to
implement a ``format_element`` function, which returns a ``string`` and
takes at least ``bfo`` as first parameter (but can take as many others
as needed).

Here is for example the code of the "bfe\_title.py" element:

::

    def format_element(bfo, separator=" "):
        """
        Prints the title of a record.

        @param separator separator between the different titles
        """
        titles = []

        title = bfo.field('245__a')
        title_remainder = bfo.field('245__b')

        titles.append( title + title_remainder )

        title = bfo.field('246__a')
        if len(title) > 0:
            titles.append( title )

        title = bfo.field('246_1a')
        if len(title) > 0:
            titles.append( title )

        return separator.join(titles)

In format templates this element can be called like a function, using
HTML syntax: ``<BFE_TITLE separator="; "/>``

Notice that the call uses (almost) the filename of your element. To
find out which element to use, BibFormat tries different filenames until
the element is found: it tries to

#. ignore the letter case
#. replace underscore with spaces
#. remove the BFE\_ from the name

This means that even if the filename of your element is "my element.py",
BibFormat can resolve the call <BFE\_MY\_ELEMENT /> in a format
template. This also means that you must take care no to have two format
elements filenames that only differ in term of the above parameters.

The ``string`` returned by the ``format_element`` function corresponds
to the value that is printed instead of the format element name in the
format template.

The ``bfo`` object taken as parameter by ``format_element`` function
stands for BibFormatObject: it is an object that represents the context
in which the formatting takes place. For example it allows to retrieve
the value of a given field for the record that is being formatted, or
the language of the user. We see the details of the BibFormatObject
further below.

The ``format_element`` function of an element can take other parameters,
as well as default values for these parameters. The idea is that these
parameters are accessible from the format template when calling the
elements, and allow to parametrize the behaviour of the format element.

It is very important to document your element: this allows to generate a
documentation for the elements accessible to people writing format
templates. It is the only way for them to know what your element do. The
key points are:

- Provide a docstring for the ``format_element`` function
- For each of the parameters of the ``format_element`` function (except
  for ``bfo``) as provide a description using a Java-like doc syntax in
  the doc string: ``@param my_param: description for my param`` (one line per
  parameter)
- You can use one ``@see`` followed by a comma separated list of
  elements filenames to provide a reference to other elements of
  interests related to this one: ``@see my_element1.py, my element2.py``

Typically you will need to get access to some fields of a record to
display as output. There are two ways to this: you can access the
``bfo`` object given as parameter and use the provided (basic)
accessors, or import a dedicated module and use its advanced
functionalities.

**Method 1: Use accessors of ``bfo``**:

``bfo`` is an instance of the ``BibFormatObject`` class. The
following methods are available:

-  ``get_record()``: Returns the record of this BibFormatObject instance
   as a BibRecord structure. Allows advanced access on the structure
   using ``BibRecord``.
-  ``control_field(tag)``: Returns the value of control field given by
   MARC ``tag``.
-  ``field(tag)``:Returns the value of the field corresponding to MARC
   ``tag``. If the value does not exist, return empty string.
-  ``fields(tag)``: Returns the list of values corresonding to MARC
   ``tag``.If tag has an undefined subcode (such as 999C5), the function
   returns a list of dictionaries, whoose keys are the subcodes and the
   values are the values of tag.subcode. If the tag has a subcode,
   simply returns list of values corresponding to tag.
-  ``kb(kb, string, default="")``: Returns the value of the ``string``
   in the knowledge base ``kb``. If kb does not exist or string does not
   exist in kb, returns ``default`` string.

You can also get access to other information through ``bfo``, such as
the language in which the formatting should occur with ``bfo.lang``. To
learn more about the possibilities offered by the ``bfo``, read the
`BibFormat APIs </help/hacking/bibformat-api>`__

**Method 2: Use module ``BibRecord``**:

BibRecord is a module that provides advanced functionalities
regarding access to the field of a record ``bfo.get_record()`` returns a
structure that can be understood by BibRecord's functions. Therefore you
can import the module's functions to get access to the fields you want.

4.4 Preview a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can play with a format element parameters and see the result of the
element directly in the `format elements
documentation </admin/bibformat/bibformatadmin.py/format_elements_doc>`__:
for each element, under the section "See also", click on "Test this
element". You are redirected to a page where you can enter a value for
the parameters. A description is associated with each parameter as well
as an indication of the default value of the parameter if you do not
provide a custom value. Click on the "Test!" button to see the result of
the element with your parameters.

4.5 Internationalization (i18n)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can follow the standard internationalization procedure in use
accross Invenio sources. For example the following code will get you the
translation for "Welcome" (assuming "Welcome" has been translated):

::

    from invenio.base.i18n import gettext_set_language

    ln = bfo.ln
    _ = gettext_set_language(ln)

    translated_welcome =  _("Welcome")

Notice the access to ``bfo.ln`` to get access to the current language of
the user. For simpler translations or behaviour depending on the
language you can simply check the value ``bfo.ln`` to return your custom
text.

4.6 Escaping special HTML/XML characters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In most cases, that is cases where your element does not return HTML
output, you do not have to take any particular action in order to escape
values that you output: the BibFormat engine will take care of escaping
the returned value of the element for you. In cases where you want to
return text that should not be escaped (for example when you return HTML
links), you can make the formatting engine know that it should not
escape your value. This is done by implementing the
``escape_values(bfo)`` function in your element, that will return (int)
0 when escape should not be done (or 1 when escaping should be done):

::

    def escape_values(bfo):
        """
        Called by BibFormat in order to check if output of this element
        should be escaped.
        """
        return 0

Note that the function is given a ``bfo`` object as parameter, such
that you can do additional testing if your element should really return
1 or 0 (for very special cases).

Also note that the behavior defined by the ``escape_values()``
function will be overriden by the ``escape`` parameter used in the
format template if it is specified.

Finally, be cautious when you disable escaping: you will have to take
care of escaping values "manually" in your format element code, in order
to avoid non valid outputs or XSS vulnerabilities. This can be done
easily when using the ``field``, ``fields`` and ``controlfield``
functions of bfo with ``escape`` parameter:

::

        title = bfo.field('245__a', escape="1")
        abstract = bfo.field('520__a', escape="2")

The ``escape`` parameter can be one of the following values:

-  0 - no escaping
-  1 - escape all HTML characters (escaped chars are shown as escaped)
-  2 - remove unsafe HTML tags to avoid XSS, but keep basic one (such as
   <br />) This is particularly useful if you want to store HTML text in
   your metadata but still want to escape some tags to prevent XSS
   vulnerabilities. Note that this method is slower than basic escaping
   of mode 1.
   Escaped tags are removed.
-  3 - mix of mode 1 and mode 2. If field\_value starts with
   <!--HTML-->, then use mode 2. Else use mode 1.
-  4 - remove all HTML/XML tags
-  5 - same as 2, but allows more tags, like <img>
-  6 - same as 3, but allows more tags, like <img>
-  7 - mix of mode 0 and mode 1. If field\_value starts with
   <!--HTML-->, then use mode mode 0. Else use mode 1.
-  8 - same as mode 1, but also escape double-quotes
-  9 - same as mode 4, but also escape double-quotes

These modes are the same for ``escape_values(bfo)`` function.

You can also decide not to use the ``escape`` parameter and escape
values using any other Python function/library you want to use (such as
``cgi.escape()``).

As a BibFormat element developer you can also override the default
``escape`` parameter of your format elements: that is especially useful
if you want to provide a way for format templates editors to call your
element with a custom escaping mode that should not escape the whole
output of your element. The ``bfe_abstract.py`` element is an example of
code that overrides the ``escape`` parameter.

4.7 Edit the Attributes of a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A format element has mainly four kinds of attributes:

-  Name: it corresponds to the filename of the element.
-  Description: the description is in the ``docstring`` of the
   ``format_element`` function (excepted lines prefixed with ``@param``
   and ``@see``).
-  Parameters descriptions: for each parameter of the ``format_element``
   function, a line beginning with ``@param`` *parameter\_name* and
   followed by the description of the parameter is present in the
   ``docstring`` of the ``format_element`` function.
-  Reference to other elements: one line beginning with ``@see`` and
   followed by a list of comma-separated format elements filenames in
   the in the ``docstring`` of the ``format_element`` function provides
   a link to related elements.

4.8 Check the Dependencies of a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to check the dependencies of a format element. The
simplest way is to go to the `format elements
documentation </admin/bibformat/bibformatadmin.py/format_elements_doc>`__
and click on "Dependencies of this element" for the element you want to
check.

The second method to check the dependencies of an element is through
regular unix tools: for example
``$ grep -r -i 'bfe_your_element_name' .`` inside the format templates
directory will tell you which templates call your element.

4.9 Check the Validity of a Format Element
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two ways to check the validity of an element. The simplest one
is to go to the `format elements
documentation </admin/bibformat/bibformatadmin.py/format_elements_doc>`__
and click on "Correctness of this element" for the element you want to
check.

The second method to check the validity of an element is through regular
Python methods: you can for example import the element in the
interactive interpreter and feed it with test parameters. Notice that
you will need to build a BibFormatObject instance to pass as ``bfo``
parameter to the ``format_element`` function of your element.

4.10 Browse the Format Elements Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to the `format elements
documentation </admin/bibformat/bibformatadmin.py/format_elements_doc>`__.
There is a summary of all available format elements at the top of the
page. You can click on an element to go to its detailed description in
the second part of the page.

Each detailed documentation shows you:

-  A description of what the element does.
-  A list of all parameters you can use for this element.
-  For each parameter, a description and the default value when
   parameter is ommitted.
-  A link to a tool to track the dependencies of your element.
-  A link to a tool to check the correctness of your element.
-  A link to a tool to test your element with custom parameters.

5. Run BibReformat
------------------

While records can be formatted on-the-fly using BibFormat, it is usually
necessary to preformat the records in order to decrease the load of your
server. To do so, use the ``bibreformat`` command line tool.

5.1 Run BibReformat
~~~~~~~~~~~~~~~~~~~

The following options are available for running ``bibreformat``:

::

     Usage: bibreformat [options]
     -u, --user=USER         User name to submit the task as, password needed.
     -h, --help              Print this help.
     -V, --version           Print version information.
     -v, --verbose=LEVEL     Verbose level (0=min,1=normal,9=max).
     -s, --sleeptime=SLEEP   Time after which to repeat tasks (no)
     -t, --time=DATE         Moment for the task to be active (now).
     -a, --all               All records
     -c, --collection        Select records by collection
     -f, --field             Select records by field.
     -p, --pattern           Select records by pattern.
     -o, --format            Specify output format to be (re-)created. (default HB)
     -n, --noprocess         Count records to be processed only (no processing done)
     Example: bibreformat -n Show how many records are to be bibreformated.

For example, to reformat all records in HB (=HTML brief) format, you'd
launch:

::

    $ bibreformat -a -oHB

and you watch the progress of the process via ``bibsched``.

Note that BibReformat understands ``-p``, ``-f``, and ``-c`` arguments
that enable you to easily reformat only the records you need. For
example, to reformat the Pictures collection, launch:

::

    $ bibreformat -cPictures -oHB

or to reformat HD (=HTML detailed) format for records #10 to #20, you
launch:

::

    $ bibreformat -p"recid:10->20" -oHD

Last but not least, if you launch bibreformat without arguments:

::

    $ bibreformat

it will process all the records that have been modified since the last
run of BibReformat, as well as all newly inputted records. This is
suitable for running BibReformat in a periodical daemon mode via
BibSched. See our `HOWTO Run Your Invenio
Installation </help/admin/howto-run>`__ guide for
more information.

6. Appendix
-----------

6.1 MARC Notation in Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The notation for accessing fields of a record are quite flexible. You
can use a syntax strict regarding MARC 21, but also a shortcut syntax,
or a syntax that can have a special meaning.

The MARC syntax is the following one:
``tag[indicator1][indicator2] [$ subfield]`` where ``tag`` is 3 digits,
``indicator1`` and ``indicator2`` are 1 character each, and ``subfield``
is 1 letter.

For example to get access to an abstract you can use the MARC notation
``520 $a``. You can use this syntax in BibFormat. However you can also:

-  Omit any whitespace character (or use as many as you want)
-  Omit the ``$`` character (or use as many as you want)
-  Omit or use both indicators. You cannot specify only one indicator.
   If you need to use only one, use underscore ``_`` character for the
   other indicator.
-  Use percent '``%``\ ' instead of any character to specify all ("don't
   care" or wildcard character) for that character.

6.2 Migrating from Previous BibFormat
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The new Python BibFormat formats are not backward compatible with the
previous formats. New concepts and capabilities have been introduced and
some have been dropped. If you have not modified the "Formats" or
modified only a little bit the "Behaviours" (or modified "Knowledge
Bases"), then the transition will be painless and automatic. Otherwise
you will have to manually rewrite some of the formats. This should
however not be a big problem.

The first thing you should do is to read the `Five Minutes Introduction
to BibFormat <#shortIntro>`__ to understand how the new BibFormat works.
We also assume that you are familiar with the concepts of the old
BibFormat. As the new formats separate the presentation from the
business logic (i.e. the bindings to the database), it is not possible
to automatically handle the translation. This is why you should at least
be able to read and understand the formats that you want to migrate.

Differences between old and new BibFormat
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The most noticeable differences are:

  a) "Behaviours" have been renamed "Output formats".
  b) "Formats" have been renamed "Format templates". They are now written in HTML.
  c) "User defined functions" have been dropped.
  d) "Extraction rules" have been dropped.
  e) "Link rules" have been dropped.
  f) "File formats" have been dropped.
  g) "Format elements" have been introduced. They are written in
     Python, and can simulate c), d) and e).
  h) Formats can be managed through web interface or through
     human-readable config files.
  i) Introduction of tools like validator and dependencies checker.
  j) Better support for multi-language formatting.

Some of the advantages are:
  + Management of formats is much clearer and easier (less concepts, more tools).
  + Writing formats is easier to learn : less concepts to learn,
    redesigned work-flow, use of existing well known and well documented
    languages.
  + Editing formats is easier: You can use your preferred HTML editor
    such as Emacs, Dreamweaver or Frontpage to modify templates, or any text
    editor for output formats and format elements. You can also use the
    simplified web administration interface.
  + Faster and more powerful templating system.
  + Separation of business logic (output formats, format elements) and
    presentation layer (format templates). This makes the management of
    formats simpler.

The disadvantages are:
  - No backward compatibility with old formats.
  - Stricter separation of business logic and presentation layer:
    no more use of statements such as if(), forall() inside templates,
    and this requires more work to put logic inside format elements.

Migrating *behaviours* to *output formats*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Behaviours were previously stored in the database and did require to use
the evaluation language to provide the logic that choose which format to
use for a record. They also let you enrich records with some custom
data. Now their use has been simplified and rectricted to equivalence
tests on the value of a field of the record to define the format
template to use.

For example, the following behaviour:

**CONDITIONS**

**0**

**$980.a="PICTURE"**

**Action (0)**

| "<record>
|  <controlfield tag=\\"001\\">" $001 "</controlfield>
|  <datafield tag=\\"FMT\\" ind1=\\"\\" ind2=\\"\\"> 
|  <subfield code=\\"f\\">hb</subfield> 
|  <subfield code=\\"g\\">" 
| xml\_text(format("PICTURE\_HTML\_BRIEF"))
| " </subfield> 
|  </datafield>
| </record>"

 

**100**

**""=""**

**Action (0)**

| "<record>
|  <controlfield tag=\\"001\\">" $001 "</controlfield>
|  <datafield tag=\\"FMT\\" ind1=\\"\\" ind2=\\"\\"> 
|  <subfield code=\\"f\\">hb</subfield> 
|  <subfield code=\\"g\\">" 
| xml\_text(format("DEFAULT\_HTML\_BRIEF"))
| " </subfield> 
|  </datafield>
| </record>"

 

translates to the following output format (in textual configuration
file):

`` tag 980__a: PICTURE --- Picture_HTML_brief.bft default: Default_HTML_brief.bft``

| or visual representation through web interface:
|  |Image representation of HB output format|

Migrating *formats* to *format templates* and *format elements*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The migration of formats is the most difficult part of the migration.
You will need to separate the presentation code (HTML) from the business
code (iterations, tests and calls to the database). Here are some tips
on how you can do this:

-  If you want to save the time of unescaping all HTML characters and
   understanding how the layout should look like, just go with your web
   browser to a formatted version of the format in your Invenio
   installation, and copy the source of the web page. Identify the parts
   of the HTML code which are specific to the current record, and
   replace them with a call to the corresponding format element.
-  If you have made small modifications to the old default provided
   formats, we suggest that you use the new provided ones and modify
   them according to your needs.

Migrating *UDFs* and *Link rules*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*User Defined Functions* and *Link rules* have been dropped in the new
BibFormat. These concepts have no reasons to be as they can be fully
implemented in the *format elements*. For example the ``AUTHOR_SEARCH``
link rule can directly be implemented in the ``Authors.bfe`` element.

As for the UDFs, most of them are directly built-in functions of Python.
Whenever a special function as to be implemented, it can be defined in a
regular Python file and used in any element.

The Migration Kit
^^^^^^^^^^^^^^^^^

The migration kit is only available in older versions of Invenio.

To enable the migration kit in this release, you need to copy the
required files from an older release.

Run old and new formats side by side
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This was possible by default only in older versions of Invenio.

To enable this functionality in this release, you need to copy the
required files from an older release.

6.3 Integrating BibFormat into Dreamweaver MX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BibFormat templates have been thought to be editable in custom HTML
editors. We propose in this section a way to extend one particular
editor, Dreamweaver.

Make Dreamweaver Recognize Format Elements in Layout View
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To make Dreamweaver understand the format elements and display an icon
for each of them in the layout editor, you must edit a Dreamweaver
configuration file named ``Tags.xml`` located inside
/Configuration/ThirdPartyTags directory of your Dreamweaver installation
folder. At the end of this file, copy-paste the following lines:

::

      <!-- BibFormat (Invenio) -->
      <tagspec tag_name="BIBFORMAT" start_string="<BFE_" end_string="/>" parse_attributes="false" detect_in_attribute="true" icon="bibformat.gif" icon_width="25" icon_height="16"></tagspec >
      <tagspec tag_name="BIBFORMAT" start_string="<bfe_" end_string="/>" parse_attributes="false" detect_in_attribute="true" icon="bibformat.gif" icon_width="25" icon_height="16"></tagspec >

Also copy this icon |bibformat.gif| in the same directory as
``Tags.xml`` (right-click on icon, or ctrl-click on one-button mouse,
and "Save Image As..."). Make sure the downloaded image is named
"``bibformat.gif``\ ".

Note that Dreamweaver might not recognize Format Elements when complex
formatting is involved due to these elements.

Add a Format Elements Floating Panel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add a floating panel that will you to insert Format Elements in
your document and read the documentation of all available Format
Elements.

The first step is to declare in which menu of Dreamweaver this floating
panel is going to be available. To do so, edit file "``Menu.xml``\ "
located inside /Configuration/Menus of your Dreamweaver application
directory and copy-paste the following line in the menu you want
(typically inside tag ``'menu'`` with attribute
``id='DWMenu_Window_Others')``:

::

       <menuitem name="BibFormat Elements" enabled="true" command="dw.toggleFloater('BibFormat_floater.html')" checked="dw.getFloaterVisibility('BibFormat_floater.html')" />

Once this is done, you can `download the floating
palette </admin/bibformat/bibformatadmin.py/download_dreamweaver_floater>`__
(if file opens in your browser instead of downloading, right-click on
icon, or ctrl-click on one-button mouse, and "Save Target As...") and
move the dowloaded file "``BibFormat_floater.html``\ " (do not rename
it) into /Configuration/Floaters directory of your Dreamweaver
application folder.

To use the BibFormat floating panel, open Dreamweaver, and choose
``Window > Others > BibFormat Elements``.

Whenever a new version of the palette is available, you can skip the
edition of file "``Menu.xml``\ " and just replace the old
"``BibFormat_floater``\ " file with the new one.

6.4 FAQ
~~~~~~~

Why do we need output formats? Wouldn't format templates be sufficient?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As you potentially have a lot of records, it is not conceivable to
specify for each of them which format template they should use. This is
why this rule-based decision layer has been introduced.

How can I protect a format?
^^^^^^^^^^^^^^^^^^^^^^^^^^^

As a web user, you cannot protect a format. If you are administrator of
the system and have access to the format files, you can simply use the
permission rights of your system, as BibFormat is aware of it.

Why cannot I edit/delete a format?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The format file has certainly been protected by the administrator of the
server. You must ask the administrator to unprotect the file if you want
to edit it.

How can I add a format element from the web interface?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Format elements cannot be added, removed or edited through the web
interface. This limitation has been introduced to limit the security
risks caused by the upload of Pythonic files on the server. The only
possibility to add a basic format element from the web interface is to
add a en entry in the "`Logical
Fields </admin/bibindex/bibindexadmin.py/field>`__\ "
management interface of the BibIndex module (see `Add a Format
Element <#addFormatElement>`__)

Why are some Marc codes omitted in the "Check Dependencies" pages?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you check the dependencies of a format, the page reminds you that
some use of Marc codes might not be indicated. This is because it is not
possible (or at least not trivial) to guess that the call to
``field(str(5+4)+"80"+"__a")`` is equal to a call to
``field("980__a")``. You should then not completely rely on this
indication.

How are displayed deleted record?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Invenio displays a standard "The record has been deleted."
message for all output formats with a 'text/html' content type. Your
output format, format templates and format elements are bypassed by the
engine. However, for more advanced output formats, Invenio goes through
the regular formatting process and let your formats do the job. This
allows you to customize how a record should be displayed once it has
been deleted.

Why are some format elements omitted in the "Knowledge Base Dependencies" page?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you check the dependencies of a knowledge base, the page reminds
you that format elements using this knowledge base might not be
indicated. This is because it is not possible (or at least not trivial)
to guess that the call to ``kb(e.upper()+"journal"+"s")`` in a format
element is equal to a call to ``kb("Ejournals")``. You should then not
completely rely on this indication.

Why are some format elements defined in field table omitted in the format element documentation?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some format elements defined in the "Logical Fields" management
interface of the BibIndex module (the basic format elements) are not
shown in the format elements documentation pages. We do not show such an
element if its name starts with a number. This is to reduce the number
of elements shown in the documentation as the logical fields table
contains a lot of not so useful fields to be used in templates.

How can I get access to repeatable subfields from inside a format element?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given that repeatable subfields are not frequent, the ``bfo.fields(..)``
function has been implemented to return the most convenient structure
for most cases, that is a '*list of strings*\ ' (**Case 1** below) or
'*list of dict of strings*\ ' (**Case 2** below). For eg. with the
following metadata:

::

        999C5 $a value_1a $b value_1b
        999C5 $b value_2b
        999C5 $b value_3b $b value_3b_bis

        >> bfo.fields('999C5b')                                   (1)
        >> ['value_1b', 'value_2b', 'value_3b', 'value_3b_bis']
        >> bfo.fields('999C5')                                    (2)
        >> [{'a':'value_1a', 'b':'value_1b'},
            {'b':'value_2b'},
            {'b':'value_3b'}]

In this example ``value3b_bis`` is not shown for
``bfo.fields('999C5')`` (**Case 2**). If it were to be taken into
account, the returned structure would have to be a '*list of dict of
list of strings*\ ', thus making for most cases the access to the data a
bit more complex.

In order to consider the repeatable subfields, use the additional
``repeatable_subfields_p`` parameter:

::

        >> bfo.fields('999C5b', repeatable_subfields_p=True)      (1 bis)
        >> ['value_1b', 'value_2b', 'value_3b']
        >> bfo.fields('999C5', repeatable_subfields_p=True)       (2 bis)
        >> [{'a':['value_1a'], 'b':['value_1b']},
            {'b':['value_2b']},
            {'b':['value_3b', 'value3b_bis']}]

Another solution would be to access the BibRecord structure with
``bfo.getRecord()`` and use the lower-level BibRecord module with this
structure.

.. |Use output format HD| image:: /_static/admin/bibformat-guide-url_bar.png
.. |BibFormat Guide BFO HD rules| image:: /_static/admin/bibformat-guide-bfo_hd_rules.png
.. |Output formats management page| image:: /_static/admin/bibformat-guide-bfo_manage.png
.. |Screenshot of the Update Output Format Attributes page| image:: /_static/admin/bibformat-guide-bfo_attributes.png
.. |Output format menu| image:: /_static/admin/bibformat-guide-bfo_rules.png
.. |Format template management page| image:: /_static/admin/bibformat-guide-bft_manage.png
.. |update format template attributes| image:: /_static/admin/bibformat-guide-bft_attributes.png
.. |Format template editor| image:: /_static/admin/bibformat-guide-bft_editor2.png
.. |Rule: Use template Picture HTML Detailed if field 980__a is equal to PICTURE| image:: /_static/admin/bibformat-guide-bfo_edit_rule.png
.. |Reorder rules using arrows| image:: /_static/admin/bibformat-guide-bfo_edit_rule2.png
.. |Check Dependencies menu| image:: /_static/admin/bibformat-guide-bfo_check_deps.png
.. |Template Editor Page| image:: /_static/admin/bibformat-guide-bft_editor.png
.. |Preview Panel| image:: /_static/admin/bibformat-guide-bft_preview.png
.. |Image representation of HB output format| image:: /_static/admin/bibformat-guide-bfo_hb_migrate.png
.. |bibformat.gif| image:: /_static/admin/bibformat-guide-bfe.gif
