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

.. _websearch-admin-guide:

WebSearch Admin Guide
=====================

+---------------------------------------------------------------------------+
| WARNING: THIS ADMIN GUIDE IS NOT FULLY COMPLETED                          |
+===========================================================================+
| This Admin Guide is not yet completed. Moreover, some admin-level         |
| functionality for this module exists only in the form of manual recipes.  |
| We are in the process of developing both the guide as well as the web     |
| admin interface. If you are interested in seeing some specific things     |
| implemented with high priority, please contact us at                      |
| info@invenio-software.org. Thanks for your interest!                      |
+---------------------------------------------------------------------------+

1. Overview
-----------

WebSearch Admin interface will help you to configure the search
collections that the end-users see. The WebSearch Admin functionality
can be basically separated into several parts: (i) how to organize
collections into `collection tree <#2>`__; (ii) how to define and edit
`collection parameters <#3>`__; (iii) how to update collection cache via
the `webcoll daemon <#4>`__; and (iv) how to influence the search engine
behaviour and set various `search engine parameters <#5>`__. These
issues will be subsequently described in the rest of this guide.

2. Edit Collection Tree
-----------------------

Metadata corpus in Invenio is organized into collections. The
collections are organized in a tree. The collection tree is what the
end-users see when they start to navigate at `Atlantis Institute of
Fictive Science <http://localhost:4000>`__. The collection tree is
similar to what other sites call Web Directories that organize Web into
topical categories, such as `Google
Directory <http://www.google.com/dirhp>`__.

Note that Invenio permits every collection in the tree to have either
"regular" or "virtual" sons. In other words, every node in the
collection tree may see either regular or virtual branches growing out
of it. This permits to create a tree with very complex, multi-level,
nested structures of regular and virtual branches, if needed, with the
aim to ease navigation to end-users from one branch to another. The
difference between a regular and a virtual branch will be explained in
detail further below in the `section 2.2 <#2.2>`__.

2.1 Add new collection
~~~~~~~~~~~~~~~~~~~~~~

To add a new collection, enter its default name in the default language
of the installation and click on the ADD button to add it. There are two
important actions that you have to perform after adding a collection:

-  You have to define the set of records that belong to this collection.
   This is done by defining a search engine query that would return all
   records belonging to this collection. See hints on `modify collection
   query <#3.1>`__ below.
-  In order for the collection to appear in the collection navigation
   tree, you will have to attach it to some existing collection in the
   tree. See hints on `add collection to tree <#2.2>`__ below.

After you edit these two things, the collection is fully usable for the
search interface. It will appear in the search interface after the next
run of the `WebColl Daemon <#4>`__.

However, you will probably want to customize further things, like define
collection name translation in various languages, define collection web
page portalboxes, define search options, etc, as explained in this guide
under the section `Edit Collection Parameters <#3>`__.

2.2 Add collection to tree
~~~~~~~~~~~~~~~~~~~~~~~~~~

To attach a collection to the tree, choose first which collection do you
want to attach, then choose the father collection to attach to, and then
choose the fathership relation type between them (regular, virtual).

The difference between the regular and the virtual relationship goes as
follows:

-  **regular relationship**: If collection A is composed of B and C, in
   a way that every document belonging to A is either B or C, then this
   schema corresponds to the regular type of relationship. For example,
   let A equals to "Multimedia" and B and C to "Photos" and "Videos",
   respectively. The latter collections would then be declared as
   regular sons of "Multimedia" and they would appear in the
   left-hand-side regular navigation tree entitled "Narrow by
   Collection" in the collection tree.
-  **virtual relationship**: In addition to the regular decomposition of
   "Multimedia" into "Photos" and "Videos", it may be advantageous to
   present a different, orthogonal point of view on "Multimedia", based
   not on the document type as seen above, but rather on the document
   creator information. Let us consider that some (large) part of the
   multimedia material was created by the "University Multimedia
   Service" and some (small) part by an external TV company such as BBC.
   It may be advantageous to advertize this point of view to the end
   users too, so they they would be able to easily navigate down to the
   kind of multimedia material they are looking for. We can create two
   more collections named "University Multimedia Service" and "BBC
   Pictures and Videos" and declare them as virtual sons of the
   "Multimedia" collection. These collections would then appear in the
   right-hand-side virtual navigation tree entitled "Focus on" in the
   collection tree.

The example presented above would then give us the following picture:

    ::

                M u l t i m e d i a

                Narrow by Collection:        Focus on:
                --------------------         ---------
                [ ] Photos                   University Multimedia Service
                [ ] Videos                   BBC Pictures and Videos

It is important to note that if a collection A is composed of B and C as
its regular sons, and offers X and Y as its virtual sons, then every
document belonging to A must also belong to either B or C. This
requirement does not apply for X and Y, because X and Y offer only a
"focus-on" orthogonal view on a (possibly small) part of the document
corpus of A. If end-users search the collection A, then they are
actually searching inside B and C, not X and Y. If they want to search
inside X or Y, they have to click upon X or Y first. One can consider
virtual branches as a sort of non-essential searching aid to the
end-user that is activated only when users are interested in a
particular "focus-on" relationship, provided that this "virtual" point
of view on A interests her.

2.3 Modify existing tree
~~~~~~~~~~~~~~~~~~~~~~~~

To modify existing tree by WebSearch Admin Interface, click on icons
displayed next to collections. The meaning of icons is as follows:

+--------------------------------------+--------------------------------------+
| |image0|                             | |image1|   |image2|                  |
| Remove chosen collection with its    | Move chosen collection up or down    |
| subcollections from the collection   | among its brothers and sisters, i.e. |
| tree, but do not delete the          | change the order of collections      |
| collection itself. (For full         | inside the same level of the tree.   |
| deletion of a collection, see        |                                      |
| `section 3.4 <#3.4>`__.)             |                                      |
+--------------------------------------+--------------------------------------+

3. Edit Collection Parameters
-----------------------------

To finalize setting up of a collection, you could and should edit many
parameters, such as define list of records belonging to a collection,
define search fields, define search interface page portalboxes, etc. In
this section we will subsequently describe all the various possibilities
as they are presented in the `Edit
Collection </admin/websearch/websearchadmin.py/editcollection?colID=1>`__
pages of the WebSearch Admin Interface.

3.1 Modify collection query
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *collection query* defines which documents belong to the given
collection. It is equal to the search term that retrieves all documents
belonging to the given collection, exactly as you would have typed it
into the search interface. For example, to define a collection of all
papers written by Ellis, you could set up your collection query to be
``author:Ellis``.

Usually, the collection query is chosen on the basis of the collection
identifier that we store in MARC tag 980. This tag is indexed in a
logical field called ``collection`` so that a collection of Theses could
be defined via ``collection:THESIS``, supposing that every thesis
metadata record has got the text ``THESIS`` in MARC tag 980. (Nitpick:
we use the term \`collection' in two contexts here: once as a collection
of metadata documents, but also and as a logical field name. We should
have probably called the latter ``collectionidentifier`` or somesuch
instead, but we hope the difference is clear from... the context.)

If a collection does not have any collection query defined, then its
content is defined by means of the content of its descendants
(subcollections). This is the case for composed collections. For
example, the composed collection *Articles & Preprints* (no query
defined) will be defined as a father of *Articles* (query:
``collection:ARTICLE``) and *Preprints* (query:
``collection:PREPRINT``). In this case the collection query for
*Articles & Preprints* can stay empty.

Note that you should avoid defining non-empty collection query in cases
the collection has descendants, since it will prevail and the
descendants may not be taken into account. In the same way, if a
collection doesn't have any query nor any descendants defined, then its
contents will be empty.

To define an external hosted collection set up the query to begin with
``hostedcollection:`` (for more detailed information see `section
4 <#4>`__)

To remove the collection query, set the parameter empty.

3.2 Modify access restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Until *Invenio-0.92.1* there was the possibility to directly restrict a
collection by specifying an Apache group. Users who had an Apache user
and password belonging to the given group would have been able to access
the restricted collection.

Collection restriction managament is now integrated with the wider `Role
Based Access Control <webaccess-admin-guide>`__ facility of Invenio.

In order to restrict access to a collection you just have to create at
least an authorization for the action ``viewrestrcoll`` specifying the
name of the collection as the parameter

3.3 Modify translations
~~~~~~~~~~~~~~~~~~~~~~~

You may define translations of collection names into the languages of
your Invenio installation. Moreover, a collection name may be different
in different contexts (e.g. long name, short name, etc), so that prior
to modifying translations you will be asked to select which name type
you want to change.

The translations aren't mandatory to define. If a translation does not
exist in a language chosen by the end user, the end user will be shown
the collection name in the default language of this installation.

Note also that the list of available languages depends on the
compile-time configuration (see the general ``invenio.conf`` file).

3.4 Delete collection
~~~~~~~~~~~~~~~~~~~~~

The collection to be deleted must be first removed from the collection
tree. Any metametadata associated with the collection (such as
association to portalboxes, association to records belonging to this
collection, etc) will be lost, but the metadata itself will be preserved
(such as portalboxes themselves, records themselves, etc). In total,
association to records, output formats, translations, search options,
sort options, search fields, ranking method, and access restriction will
be lost. Use with care!

It may be a good idea only to remove the collection from the end users
interface, but to keep it "hidden" in a corner they don't see and that
they can't search when they search from Home. To achieve this, do not
delete the collection but simply remove it from the collection tree so
that it won't be attached to any father collection. In this case the
search interface page for this collection will stay updated, but won't
be neither shown in the tree nor searchable from Home page. It will only
be accessible via bookmarked URL, for example.

3.5 Modify portalboxes
~~~~~~~~~~~~~~~~~~~~~~

The search interface HTML page for a given collection may be customized
by what we call *portalboxes*. Portalboxes are used to show various
kinds of information to the end user, such as a text box with some
inline help information about the given collection, an illustrative
picture, etc.

To create a new portalbox, a title and a body must be given, where the
body can contain HTML if necessary.

To add a portalbox to the collection, you must choose an existing
portalbox, the language for which the portalbox should be shown, the
position of the portalbox on the screen, and the ordering score of
portalboxes.

-  The *language* could be chosen depending on the language used in the
   portalbox body. Since a portalbox is not necessarily bound to one
   particular language, one portalbox may be reused for several
   languages, which is particularly suitable for portalboxes containing
   language-independent content such as images.
-  The *position* of the portalbox on the screen is chosen from several
   predefined positions, such as right-top, before-title, after-title,
   before-narrow-by-collection-box, etc. You may present several
   portalboxes on the same position in the same language, in which case
   they will be shown by the order of decreasing score.
-  The *score* defines the order of portalboxes that are to be presented
   in the same position and in the same language context.

3.6 Modify search fields
~~~~~~~~~~~~~~~~~~~~~~~~

The *search field* is a logical field (such as author, title, etc) that
will be proposed to the end users in Simple and Advanced Search
interface pages. If you do not set any search fields for a collection,
then a default list (author, title, year, etc) will be shown.

Note that if you want to add a new logical field or modify existing
physical MARC tags for a logical field, you have to use the `BibIndex
Admin </admin/bibindex/bibindexadmin.py>`__
interface.

3.7 Modify search options
~~~~~~~~~~~~~~~~~~~~~~~~~

The *search option* is like `search field <#3.6>`__ in a way that it
permits the end user to narrow down his search to some logical field
such as "subject", but unlike with the search field the user is not
required to type his query in a free text form; rather, the search
interface proposes to the end user several interesting predefined values
prepared by the administrators that the end user may choose from. For
example, an "author search" concept is a good example of search field
usage, since there is plenty of author names to be matched, so that the
end users would usually type the name they wish to find in free text
form; while a "subject search" concept is a good example for search
option usage, since usually there is a limited number of subjects in the
system given by local subject classification scheme, that the end users
do not necessarily know about and that they are free to choose from a
list. As a rule of thumb, the search field concept denotes the case of
unlimited number possibilites of distinct values to be matched in a
given field (e.g. author, title, keyword); while the search option
concept denotes the case of only a handful or so distinct values to be
matched in a given field (e.g. subject, division, year).

Search options are shown in the "Advanced Search" interfaces only, while
search fields are shown both in "Simple Search" and "Advanced Search"
interface. (Although if you want to add a search option to the "Simple
Search" interface, you can achieve it by creating appropriate HTML code
in a `portalbox <#3.5>`__.) The search options order, as well as the
order of search option values, may be defined by means of 'move' arrows
in the WebSearch Admin interface.

To add a new search option, a field name must first be chosen (for
example "subject") and then a list of possible field values must be
entered (for example "Mathematics", "Physics", "Chemistry", "Biology",
etc). Note that if you want to add a new logical field or modify
existing physical MARC tags for a logical field, you have to use the
`BibIndex
Admin </admin/bibindex/bibindexadmin.py>`__
interface.

3.8 Modify sort options
~~~~~~~~~~~~~~~~~~~~~~~

You may define a list of logical fields that the end users will be able
to choose for the sorting purposes. For example, "first author" or
"year". If you don't select anything, a default list (author, title,
year, etc) will be shown.

Note that if you want to add a new logical field or modify existing
physical MARC tags for a logical field, you have to use the `BibIndex
Admin </admin/bibindex/bibindexadmin.py>`__
interface.

3.9 Modify rank options
~~~~~~~~~~~~~~~~~~~~~~~

To enable a certain rank method for a collection, select the method from
the "enable rank method" box and add it. The documents in this
collection will then be included in the ranking sets the next time the
BibRank daemon will run. To disable a method the process is the same,
but select the method from the 'disable rank method' box.

Note that if you want to add new ranking method or modify existing
ranking method, you have to use the `BibRank
Admin </admin/bibrank/bibrankadmin.py>`__
interface.

3.10 Modify output formats
~~~~~~~~~~~~~~~~~~~~~~~~~~

Each collection may have several output formats defined. The end users
will be able to choose a format they want to see their search results
list in. Most formats like HTML brief or XML Dublin Core are interesting
for each collection, but some formats like HTML portfolio are only
interesting for Photographs collection, not for Articles collection. The
interface will permit you to choose the formats appropriate for a given
collection. The order of formats can be changed using the 'move' arrows.

Note that if you want to add new output format ('behaviour') or modify
existing output format, you have to use the `BibFormat
Admin </admin/bibformat/bibformatadmin.py>`__
interface.

3.11 Configuration of related external collections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can customize each collection to provide your users an additional
source of information external to your repository: in a *book*
collection you might want for example to provide a link to *Amazon*
items corresponding to the user's query. Futhermore, for some external
services only, you can set the collection to display the results
directly in Invenio search results page.

The following settings are available:

Disabled

The external collection is not shown to the user.

See also

A link to the external collection listing the items corresponding to
user's query is displayed (only once a query has been performed).

External search

User can ask to perform a search in parallel on your repository and on
the external collection. Results are shown in the Invenio search results
page. Not available for all external collections.

External search checked

Same as above, but the external collection is searched by default. Not
available for all external collections.

You can also apply the settings to sub-collections, by checking the
"*Apply also to daughter collections*\ " checkboxes when you apply your
modifications.

Note that in case you have defined an external hosted collection and you
are in fact configuring its related external collections there is no
restriction on setting even itself as "*See also*\ ", "*External
search*\ " or "*External search checked*\ "; directly or recursively via
the "*Apply also to daughter collections*\ " option. It is up entirely
to the admin to keep a clean and consistent installation (for more
detailed information see `section 4 <#4>`__).

3.12 Detailed record page options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These settings let you define how the detailed view (such as
/record/1) of records in this collection will look
like. More details are available in the `WebStyle admin
guide </help/admin/webstyle-admin-guide#det_page>`__.

Please note that since a record might belong to several collections,
conflicts between collection settings might occur. This is especially
true in the case of *virtual* collections. It is therefore the settings
of the *primary collection* of the record which are applied.

4. External and Hosted Collections
----------------------------------

External and hosted collections are a way to provide your users with
additional sources of information. The simplest option is the "*See
also*\ " one: it provides a link to the external collection listing the
items corresponding to the user's query. Another option is to set up the
external collection an "*External search [checked]*\ ". This option
implies a parser implemented for that external collection and allows the
user to perform a parallel search on your repository and on that of the
external collection. Read more on how to set up the above options in
section `section 3.11 <#3.11>`__. Also please note that some external
resourses might be under copyright restrictions.

Another, more advanced option, are the external hosted collections. The
purpose of these collections is to behave just as if they were local
ones. That means the admin should set them up as local collections and
attach them to the tree. These collections however are not meant to
store their records locally but rather to produce them on the fly when
asked to. Once attached to the tree an external hosted collection
appears in the search home page along with its number of records and a
small graphic (arrow in this case) to indicate their being external.

The admin should define a new external collection (any of the above
options) starting with the ``websearch_external_collections_config.py``
file, which consists basically of a python dictionary. Let us go through
the process of defining a new external collection, starting from the
dictionary:

- add a new ``key:value`` pair to the dictionary. The key is the name
  of the external collection (eg. Amazon Books). The value is another
  python dictionary with the parameters of the external collection.
  Let's go through these parameters in ``key:value`` pairs:

- ``'engine':the_name_of_engine``
  The name of the search engine (no spaces or special characters
  allowed and its implemented python class (eg. for the
  'AmazonBooks' engine the corresponding class should be named
  AmazonBooksSearchEngine). If not defined the default
  ExternalSearchEngine class will be used.

- ``'base_url':the_base_url_of_the_external_collection``
  The base url of the external collection, used to create actual
  hyper references to the external collection (eg.
  'http://books.amazon.com/' , 'http://www.amazon.com/books/').

- ``'search_url':the_search_url_of_the_external_collection``
  The search url of the external collection, to which the search
  terms will be later appended and therefore looked up (eg.
  'http://books.amazon.com/search.php?title=' ,
  'http://www.amazon.com/books/lookup.asp?book=').

- ``'parser_params':dictionary_of_the_parameters_of_the_parser``
  The parameters to be passed to the parser. This way a parser can
  be dynamically reused for different external collections upon
  defining different settings. Let's go through the various
  parameters:

- ``'host':the_host_of_the_external_collection``
  The host of the external collection is used to correct the
  urls when printing out its results (eg. 'books.amazon.com',
  'www.amazon.com').

- ``'path':the_path_on_the_host_of_the_external_collection``
  The path, along with the host of the external collection, is
  used to correct the urls when printing out its results (eg. '',
  'books/').

- ``'parser':the_actual_parser_class``
  The actual parser class to be used by the external collection
  engine. It should be imported at the beggining of this
  configuration file (eg.
  AmazonBooksExternalCollectionResultsParser,
  AmazonExternalCollectionResultsParser).

- ``'fetch_format':the_format_to_be_used_to_fetch_data``
  Usually an abbreviated string that defines the format in which
  the data should be fetched. The parser must be able to parse
  this format (eg. 'hb', 'xm').

- ``'num_results_regex_str':the_regular_expression_for_the_number_of_results``
  The regular expression used to calculate the returned number
  of results when the external collection is queried (eg.
  r'\ **([0-9,]+?)** records found'). Should preferably be a
  python raw string.

- ``'num_results_regex_str':the_regular_expression_for_the_total_number_of_records``
  The regular expression used to calculate the total number of
  records of an external collection (eg. r'Searching
  **([0-9,]+?)** records in total'). This is to be used by
  external hosted collections that present their total number of
  records in the search home page. Should preferably be a python
  raw string.

- ``'nbrecs_url':the_url_that_provides_the_total_number_of_records``
  The url that provides information on the total number of
  records of an external collection (eg.
  'http://books.amazon.com/search.php?show\_all=yes'). The
  regular expression defined above will be used on the contents
  of this url. Again, this is to be used by external hosted
  collections that present their total number of records in the
  search home page.

Once the dictionary ``key:value`` pair has been added for the new
external collection the admin should implement (or simply use if already
implemented) the search engine python class defined for this external
collection. For the "*See also*\ " option the above steps are
sufficient. If the admin wants to enable the "*External search
[checked]*\ " option as well a parser must be (or have been)
implemented. Finally to set up an external hosted collection the admin
also has to create a new local collection named exactly as the key of
the external hosted collection's ``key:value`` pair in the python
dictionary. The new local collection's query has to begin with
``hostedcollection:`` (under the current configuration it is sufficient
for the query of any external hosted collection to just be defined as
``hostedcollection:``) and the collection itself has to be attached to
the tree to be visible in the search home page. Note that due to the
nature of external hosted collections their corresponding local
collections cannot have any other collections as sons; in other words
they shouldn't have any other branches growing from them.

5. Webcoll Status
-----------------

WebColl is the daemon that normally periodically runs via
`BibSched </help/admin/bibsched-admin-guide>`__ and
that updates the collection cache with the collection parameters
configured in the previous section. Alternatively to running webcoll via
BibSched, you can also run it any time you want from the command line,
either for all collections or for selected collection only. See the
--help option.

The WebSearch Admin interface has got a WebColl Status menu that shows
when the collection cache was last updated and when the next update is
scheduled. It warns in case something suspicious was discovered.

6. Collections Status
---------------------

The Collection Status menu of the WebSearch Admin interface shows the
list of all collections and checks if there is anything wrong regarding
configuration of collections, together with the languages the collection
name has been translated into, etc. Here is the detailed explanation of
the functionality:

**ID**
  ID of the collection.

**Name**
  Name of the collection.

**Query**
  The collection definition query. Note that it should be empty if a
  collection got subcollections. If not, then a query is needed.

**Subcollections**
  The subcollections that the collection is composed of. Note that a
  collection which got defined by a query should not have any
  subcollections.

**Restricted**
  A restricted collection can only be accessed by users belonging to
  the Apache groups mentioned in this column.

**Hosted**
  A hosted collection is practicly an external one behaving just as if
  it were local.

**I18N**
  Show which languages the collection name has been translated into.

**Status**
  If no errors was found, *OK* is displayed for each collection. If an
  error was found, then an error number and short message are shown.
  The meaning of the error messages is the following: *1:Conflict*
  means that the collection was defined via a query but also via
  subcollections too; *2:Empty* means that the collection wasn't
  defined neither via query nor via subcollections.

7. Check External Collections
-----------------------------

The Check External Collections menu of the WebSearch Admin interface is
a simple tool to check and control the consistency of the external
collections the user has defined. External collections exist both in
their own database table as well in a user defined configuration file.
This tool will check the consistency between the two and report back to
the user giving them the option to fix any potential inconsistencies.

8. Edit Search Engine Parameters
--------------------------------

9. Search Engine Cache
----------------------

10. Additional Information
--------------------------

`WebSearch
Internals </help/hacking/search-engine-internals>`__

.. |image0| image:: /_static/iconcross.gif
.. |image1| image:: /_static/arrow_up.gif
.. |image2| image:: /_static/arrow_down.gif
.. |image3| image:: /_static/move_from.gif
.. |image4| image:: /_static/move_to.gif
