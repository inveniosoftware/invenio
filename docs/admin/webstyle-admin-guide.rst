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

.. _webstyle-admin-guide:

WebStyle Admin Guide
====================

Contents
--------

-  **1. `Overview <#overview_page_layout>`__**

   -  1.1  \ `CSS Style Sheet and Images <#overview_css>`__
   -  1.2  \ `HTML Page Layout <#overview_page_layout>`__

      -  1.2.1    \ `Layout of HTML Static
         Pages <#overview_page_layout_stat>`__
      -  1.2.2    \ `Layout of Python Dynamic
         Pages <#overview_page_layout_dyn>`__

   -  1.3  \ `Look of Bibliographic References <#overview_bib>`__
   -  1.4  \ `Specific Configurations <#overview_spec_conf>`__

-  **2. `Detailed Record Pages <#det_page>`__**

   -  2.1  \ `Available tabs <#det_page>`__
   -  2.2  \ `Showing/Hiding tabs <#det_show_hide_tabs>`__
   -  2.3  \ `Customizing content of tabs <#det_page_cust_cont_tabs>`__
   -  2.4  \ `Customizing look of tabs <#det_page_cust_look_tabs>`__

-  **3. `Custom Redirections <#red>`__**

   -  3.1  \ `Command Line Interface <#red_cli>`__

1. Overview
-----------

This document describes how to change the look and feel of your CDS
Invenio installation.

1.1 CSS Style Sheet and Images
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most obvious modification you may want to do is the modification of
`CSS style sheet </img/invenio.css>`__. You may
also customize default `images </img/>`__.

1.2 HTML Page Layout
~~~~~~~~~~~~~~~~~~~~

The customization of the general page look and feel is currently
different depending on whether you customize HTML-like static pages or
dynamic Python pages.

Dynamic HTML pages are used to build the 'interactive' parts of the
website, such as the search and browse pages, as well as the admin
pages. The content of these pages is defined at run time, depending on
the users parameters. You can modify them to provide a totally different
experience to your users when browsing Atlantis Institute of Fictive
Science. Most probably, you will only want to customize
'webstyle\_templates.py', which define the headers and footer of a page.

Static HTML pages are used for basic pages that do not embed dynamic
content, such as this guide. They help reducing the load of the server
and speed up pages serving. As you will see, even HTML static pages can
still contain some values defined at run time, but these are reduced to
the minimum compared to dynamic pages. Most probably you will not want
to modify these pages, since the small amount of dynamic content they
have allow these pages to inherit from the customizations you have made
elsewhere, such as in the CSS, and the page header and footer.

1.2.1 Layout of HTML Static Pages
`````````````````````````````````

Static HTML pages are all located in the /opt/invenio/lib/webdoc/
installation directory. These files are organized in 3 directories:

-  **help:** Help pages available to users of your website
-  **admin:** Mostly guides for admin users
-  **hacking:** Mostly guides for administrators and developers

These directories do not contain the ``.html`` files, but ``.webdoc``
files. These '*WebDoc*\ ' files are basically HTML with the following
main differences:

-  They only contain the body of your page (only content of the
   ``<body>`` tag)
-  You can make use of special tags such as ``<CFG_SITE_URL>`` and
   ``<CFG_SITE_SUPPORT_EMAIL>``, that will be replaced by
   http://localhost:4000 and info@invenio-software.org, the values that
   you should have configured in your ``config.py`` file.
-  You can internationalize the content. For example:

   ::

       <lang>
           <en>Book</en>
           <fr>Livre</fr>
           <de>Buch</de>
       </lang>

   will be replaced by "Book" if the user has chosen to display the
   English version of your site, "Livre" in French or "Buch" in German.

Read the `WebDoc syntax
guide </help/hacking/webstyle-webdoc-syntax>`__ to
learn more about details of the WebDoc syntax.

The advantage of not using raw HTML for these static pages is that they
can for example reuse the header and footer that you have defined for
dynamic pages, and make use of the variables you have defined in your
invenio.conf file. In that way you should not need to adapt them to your
needs: **they** will adapt themselves to your needs.

Any modification should be immediatly visible when looking at the pages
from the web: the pages are built "dynamically" and then cached. If you
want to force the cache of the pages, use the WebDoc CLI (type
``/opt/invenio/bin/webdoc --help`` to learn more about it).

1.2.2 Layout of Python Dynamic Pages
````````````````````````````````````

The dynamic Python-powered pages can be customized by making use of
Invenio templating system that uses a notion of a template skin. How
this works?

When you edit ``invenio-local.conf`` during installation or later during
runtime (when during runtime, you have to run
``inveniocfg --update-config-py`` after editing the conf file), you may
choose to use your own templates instead of the provided default ones by
editing ``CFG_WEBSTYLE_TEMPLATE_SKIN`` variable. Let us say you put
``ithaca`` there in order to use your own ``ithaca`` style. Now, when
you start Apache, then instead of Invenio's usual template files such as
``webbasket_templates.py`` the system will look for file named
``webbasket_templates_ithaca.py`` and will load the template functions
from there instead, provided that they exist. (Otherwise it would fall
back to the default ones.)

How do you create such an ``ithaca`` style templates file? We do not use
one of many existing templating frameworks in Python but a very simple
programmer-friendly templating system that enables you to use the full
power of Python to inherit from the default templates the output
generating functions you want to reuse and to write anew only the
functions you would like to modify.

Let's show an example of how to modify the page footer. Create a file
named ``webstyle_templates_ithaca.py`` with the following content:

    ::

        from invenio.config import CFG_SITE_LANG
        from invenio.legacy.webstyle.templates import Template as DefaultTemplate

        class Template(DefaultTemplate):
            """Ithaca style templates."""

            def tmpl_pagefooter(self, req=None, ln=CFG_SITE_LANG, lastupdated=None,
                                pagefooteradd=""):
                """
                Ithaca style page footer.  See the default function for
                the meaning of parameters.
                """
                out = ""
                out += """<hr>This site has no footer.
                          </body>
                          </html>"""
                return out

After the file was created, restart Apache and lo, your new ithaca style
footer will be seen in action.

(A side comment: note that ``tmpl_page_footer()`` is an ideal place to
put any local code you may want to execute at the end of web request
processing when the main page content was just served to the user. As an
example, if you are using Google Analytics, you may want to put just
after the above ``out = ""`` statement your GA script code:

::

            [...]
            out += """
    <script type="text/javascript">

      var _gaq = _gaq || [];
      _gaq.push(['_setAccount', 'UA-XXXXX-X']);
      _gaq.push(['_trackPageview']);

      (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
      })();

    </script>
    """

End of the side comment.)

Some further remarks on this templating system:

-  We have observed that in practice the HTML page designers were ofter
   Python programmers, therefore we have adopted a programmer-friendly
   templating system.
-  You have to know a bit of Python in order to use it. If you don't
   know Python, do not worry, because you can basically copy and paste
   the original ``tmpl_foo()`` function definition "as is" into the
   above-cited example and then you would only modify its HTML snippets.
   The important thing is to preserve the imports
   (``from invenio.config import CFG_SITE_LANG``) as in the original
   ``webstyle_templates.py`` file and to preserve the leading whitespace
   Pythonic indentation.
-  You do not have to learn "yet another templating language", you can
   use the full power of Python. The ``tmpl_foo()`` functions do not
   contain any business logic in them, their only purpose is to make the
   HTML presentation of data supplied to them. But, should you need to
   carry out a little data transformation, you can do it within the
   ``tmpl_foo()`` function itself, thanks to the full Python power.
-  If you feel like doing so, you can modify all the ``tmpl_foo()``
   functions across all Invenio modules in a way that will completely
   change the presentation of elements including their content, position
   and order on the screen.
-  In practice, it is sufficient to modify the CSS and the
   webstyle\_templates\_ithaca.py (and possibly
   websearch\_templates\_ithaca.py) files to achieve most important
   customizations.
-  If you would like to discover which method of which template generate
   which region on the web page, you can switch on the
   ``CFG_WEBSTYLE_INSPECT_TEMPLATES`` configuration variable in your
   ``invenio-local.conf`` file and rerun
   ``sudo -u     apache /opt/invenio/bin/inveniocfg     --update-config-py``.
   Then, after optionally running ``bibreformat -a`` and ``webcoll -f``
   (if you want to debug search pages) and after having restarted your
   Apache server (in every case), you will find in your browser that a
   place-mark has been put next to every region of every page, and that
   you can hover your mouse pointer over any region of the page in order
   to discover which module/method/parameters have been used to generate
   it. This is useful for debugging Python templates and/or for
   understanding which part of code generates which HTML snippet in the
   output.
-  We expect to provide possibly more than one skin with the default
   distribution, so if you have modified Invenio look and feel in an
   interesting way, please consider donating us your templates.
-  When upgrading from one Invenio release to another, you may find out
   that the default templates have changed in a way that requires
   changes to your templates (such as an addition of parameters to cover
   the new functionality). This is inevitable in any templating system;
   unless you introduce new parameters, you would not see them being
   printed. Therefore, if you have modified ``tmpl_foo()`` and
   ``tmpl_bar()``, and you are ugrading to a new release, you may at
   least briefly check whether the function arguments are the same. A
   quick check of the body would be helpful too, in case the new release
   fixed some display-related problems in these functions.
   In order to help you in this task, we provide a tool to check
   incompatibilities between your customized templates and the default
   templates.
   This tool can be run before doing a ``'make install'``, therefore
   giving you a chance to fix your templates before upgrading. Just run
   ``'make check-custom-templates'`` to get the list of problems found
   with your templates.
   You can also run this tool any time after the new default templates
   have been installed, in order to ensure that modifications you have
   done to your templates are valid. To do so move to your Invenio
   installation directory, and run:::

    $ python /opt/invenio/lib/python/invenio/template.py --check-custom-templates

1.3 Look of Bibliographic References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bibliographic metadata is formatted using
`BibFormat <bibformat-admin>`__. Read the `BibFormat
documentation <bibformat-admin-guide>`__ for more information.

1.4 Specific Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that the search interface pages may be modified to a large extent
in the `WebSearch Admin Interface <websearch-admin>`__ by adding HTML
portalboxes on various places on the page (right top, before/after page
title, before/after narrow by collection boxes, etc).

2. Detailed Record Pages
------------------------

The web pages displaying the details of a record (such as
/record/1) do not only show metadata, but also
users' comments and reviews, statistics, etc. This information is
organized into tabs.

The content of these tabs can be customized on a collection basis. It is
also possible to show/hide tabs depending on the displayed collection.

The detailed record pages also feature a mini panel at the bottom of the
page that links to popular functions (The mini panel is only displayed
when *Information* tab is selected).

::


      +--------------Detailed record page-------------+
      |                    header                     |
      |nav. breadcrumb                                |
      |                                               |
      |   .--------------------------------------.    |
      | .-|Info.|Ref.|Comm.|Review.|Stats.|Files |-.  |
      | | '--------------------------------------' |  |
      | |                                          |  |
      | |                  content                 |  |
      | |                                          |  |
      | '------------------------------------------'  |
      |                                               |
      | .---------------(Mini Panel)---------------.  |
      | |   Mini    |      Mini     |    Mini      |  |
      | |   File    |     Review    |   Actions    |  |
      | '------------------------------------------'  |
      +-----------------------------------------------+

2.1 Available tabs
~~~~~~~~~~~~~~~~~~

The following tabs are available:

+-------------------------+--------------------------+-----------------------+
| Name                    |                          |                       |
| Description             |                          |                       |
| URL (eg. for record     |                          |                       |
| '10')                   |                          |                       |
+=========================+==========================+=======================+
| Information             | References               | Comments              |
| Show the formatted      | Displays the references  | Displays the users'   |
| metadata of the record  | (bibliography) of the    | comments              |
| /re | record            | http://localhost:4000/re |                       |
| cord/10                 | /re \| cord/10/comments  |                       |
|                         | cord/10/references       |                       |
+-------------------------+--------------------------+-----------------------+

The mini panel is only displayed when the *Information* tab is selected.
It is divided into the following sections:

-  Files: quick access to full-text file(s)
-  Review: quick access to reviewing feature
-  Actions: quick access to several other features

2.2 Showing/Hiding tabs
~~~~~~~~~~~~~~~~~~~~~~~

The `WebSearch admin web interface <websearch-admin>`__ lets you decide
for each collection which tabs are to be displayed. Choose a collection
to edit in the collection tree and go to its *detailed record page
options*. From there you can select which tabs to show for that
collection.

If you want to apply these settings to the subcollections, select *Also
apply to subcollections* before you click on the button.

Note that these settings only affect the tabs, not the content of the
tabs: even if a tab is not displayed, it is still possible to access its
content using its usual url. This is useful if you decide to completely
change the detailed record pages, dropping the tab-metaphor (eg. for a
side bar) but still want to access the comments, reviews, etc pages.

Here are some behaviours you should expect when changing the tabs
configuration:

-  Given that search results pages always link to
   /record/10, and given the above comment about
   accessibility of tabs when they are not displayed, the content of the
   *Information* will always be show when clicking on `detailed
   record <#>`__ link in search results, even if the *Information* tab
   is set not to be displayed.
-  If you select only 1 tab, none of the tabs will be displayed at the
   top of the page. This also means that whatever tabs you have
   selected, you users will always see the content of the 'Information'
   tabs (see above behaviour).
-  If you select 0 tab, only the content of *Information* tab is shown.
   None of the tabs, nor the border that usually surrounds the content
   of the tabs, nor the minipanel are shown. You should choose this
   option if you decide to drop the tabs metaphor for the detailed
   record pages. You can then build your own user interface on this
   almost blank page (See `Customizing content of
   tabs <#det_page_cust_cont_tabs>`__).
-  Note that *Comments* and *Reviews* tabs will not be shown if you have
   disabled commenting and reviewing features in your installation,
   respectively. (``CFG_WEBCOMMENT_ALLOW_COMMENTS`` and
   ``CFG_WEBCOMMENT_ALLOW_REVIEWS`` variable in your config file)

2.3 Customizing content of tabs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The contents of tabs are defined in the following ways:

***Information* tab**
    The content of this tab is defined by function
    ``tmpl_detailed_record_metadata(..)`` in ``websearch_templates.py``.
    By default ``tmpl_detailed_record_metadata`` simply returns the
    result of the formatting of the metadata by BibFormat using the "HD"
    output format. It can therefore be collection-specific.
***References* tab**
    The content of this tab is defined by function
    ``tmpl_detailed_record_references(..)`` in
    ``websearch_templates.py``. By default
    ``tmpl_detailed_record_metadata`` simply returns the result of the
    formatting of the metadata by BibFormat using the "HDREF" output
    format. If the result returned by BibFormat is empty, the tab is
    disabled (visible, but not clickable). It can therefore be
    collection-specific.
***Comments* and *Reviews* tabs**
    The content of these tabs is mainly defined by function
    ``tmpl_get_comments(..)`` in ``webcomment_templates.py``. Other
    functions in this file are also involved in the display.
***Usage Statistics* tab**
    The content of this tab is defined by function
    ``tmpl_detailed_record_statistics(..)`` in
    ``websearch_templates.py``. If the returned content is empty, then
    the tabs will be disabled (visible, but cannot be clicked).
***Files* tab**
    The content of this tab is defined by function ``tmpl_filelist(..)``
    in ``websubmit_templates.py``.


The content of the mini panel is defined in the following ways:

***Files***
    The content of this section is defined by the output format
    'HDFILE'. It can therefore be collection-specific.
***Review***
    The content of this section is defined by function
    ``tmpl_mini_review(..)`` inside ``webcomment_templates.py``
***Actions***
    The content of this section is defined by the output format
    ``HDACT``. It can therefore be collection-specific.

2.4 Customizing look of tabs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can customize how tabs look like, as well change the look of the
border that surrounds the content of tabs. The mini panel can similarly
be customized.

Have a look at the following classes in the CDS css stylesheet:

-  ``detailedrecordtabs``
-  ``detailedrecordbox``
-  ``detailedrecordminipanel``
-  ``top-left, top-right, bottom-left, bottom-right``
-  ``detailedrecordminipanel{actions,review,file}, detailedrecordshortreminder``

Note that a tab might be greyed out (disabled) when its content is
empty. This is the case for the *References* tab (see `Customizing
content of tabs <#det_page_cust_cont_tabs>`__ -> 'References tab') and
the *Files* tab (if no file could be found for the record).

For more advanced modifications (like changing the HTML code of the
tabs), you can modify the ``detailed_record_container(..)`` and
``detailed_record_mini_panel(..)`` functions inside your
``webstyle_templates.py`` file.

Custom Redirections
~~~~~~~~~~~~~~~~~~~

It is possible to create custom redirections to URLs within Invenio, by
registering a given *unique label* to be used after path **/goto/**.

FIXME

Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~

::

    Usage: gotoadmin [options]

    Options:
      -h, --help            show this help message and exit

      Plugin Administration Options:
        --list-plugins      List available GOTO plugins and their documentation
        --list-broken-plugins
                            List broken GOTO plugins

      Redirection Manipultation Options:
        -r LABEL, --register-redirection=LABEL
                            Register a redirection with the provided LABEL
        -u LABEL, --update-redirection=LABEL
                            Update the redirection specified by the provided LABEL
        -g LABEL, --get-redirection=LABEL
                            Get all information about a redirection specified by
                            LABEL
        -d LABEL, --drop-redirection=LABEL
                            Drop an existing redirection specified by LABEL

      Specific Options:
        -P PLUGIN, --plugin=PLUGIN
                            Specify the plugin to use when registering or updating
                            a redirection
        -j PARAMETERS, --json-parameters=PARAMETERS
                            Specify the parameters to provide to the plugin
                            (serialized in JSON)
        -p PARAM=VALUE, --parameter=PARAM=VALUE
                            Specify a single PARAM=VALUE parameter to be provided
                            to the plugin (alternative to the JSON serialization)

