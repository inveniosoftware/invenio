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

.. _bibrank-admin-guide:

BibRank Admin Guide
===================

1. Overview
-----------

The bibrank module consist currently of two tools:

1. bibrank - Generates ranking data for ranking search results based on
   methods like:::

        Journal Impact Factor
        Word Similarity/Similar Records
        Combined Method
         ##Number of downloads
         ##Author Impact
         ##Citation Impact

2. bibrankgkb - For generating knowledge base files for use with bibrank

The bibrankgkb may not be necessary to use, it depends on which ranking
methods you are planning to use, and what data you already got. This
guide will take you through the necessary steps in detail in order to
create different kinds of ranking methods for the search engine to use.

2. Configuration Conventions
----------------------------

- comment line starts with '#' sign in the first column
- each section in a configuration file is declared inside '[' ']' signs
- values in knowledgebasefiles are separated by '---'

3. BibRank Admin Interface
--------------------------

The bibrank web interface enables you to modify the configuration of
most aspects of BibRank. For full functionality, it is advised to let
the http-daemon have write/read access to your invenio/etc/bibrank
directory. If this is not wanted, you have to edit the configuration
files from the console using your favourite text editor.

3.1 Main interface
~~~~~~~~~~~~~~~~~~

In the main interface screen, you see a list of all rank methods
currently added. Each rank method is identified by the rank method code.
To find out about the functionality available, check out the topics
below.

**Explanation of concepts**

::

    Rank method:
    A method responsible for creating the necessary data to rank a result.
    Translations:
    Each rank method may have many names in many languages.
    Collections:
    Which collections the rank method should be visible in.

3.2 Add rank method
~~~~~~~~~~~~~~~~~~~

When pressing the link in the upper right corner from the main
interface, you will see the interface for adding a new rank method. The
two available options that needs to be decided upon, are the bibrank
code and the template to use, both values can be changed later. The
bibrank code is used by the bibrank daemon to run the method, and should
be fairly short without spaces. Which template you are using, decides
how the ranking will be done, and must before used, be changed to suit
your Invenio configuration. When confirming to add a new rank method, it
will be added to the list of possible rank methods, and a configuration
file will be created if the httpd user has proper rights to the
'invenio/etc/bibrank' directory. If not, the file has to manually be
created with the name 'bibrankcode.cfg' where bibrankcode is the same as
given in the interface.

3.3 Show details of rank method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This interface gives you an overview of the current status of the rank
method, and gives direct access to the various interfaces for changing
the configuration. In the overview section, you see the bibrank code,
for use with the bibrank daemon, and the date for the last run of the
rank method. In the statistics section you see how many records have
been added to the rank method and other statistic data. In the
collection part, the collections which the rank method is visible to is
shown. The translations part shows the various translations in the
languages available in Invenio. On the bottom the configuration file is
shown, if accessible.

3.4 Modify rank method
~~~~~~~~~~~~~~~~~~~~~~

This interface gives access to modify the bibrank code given when
creating the rank method and the configuration file of the rank method,
if the file can be accessed. If not, it may not exist, or the httpd user
doesn't have enough rights to read the file. On the bottom of the
interface, it is possible to choose a template, see it, and copy it over
the old rank method configuration if wanted. Remember that the values
present in the template is an example, and must be changed where
necessary. See this documentation for information about this, and the
'BibRank Internals' link below for additional information.

3.5 Delete rank method
~~~~~~~~~~~~~~~~~~~~~~

If it is necessary to delete a rank method, some precautions must be
taken since the configuration of the method will be lost. When deleting
a rank method, the configuration file will also be deleted
('invenio/etc/bibrank/bibrankcode.cfg' where bibrankcode is the code of
the rank method) if accessible to the httpd user. If not, the file can
be deleted manually from console. Any bibrank tasks scheduled to run the
deleted rank method must be modified or deleted manually.

3.6 Modify translations
~~~~~~~~~~~~~~~~~~~~~~~

If you want to use internalisation of the rank method names, you have to
add them using the 'Modify translations' interface. Below a list of all
the languages used in the Invenio installation will be shown with the
possibility to add the translation for each language.

3.7 Modify visibility toward collections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a rank method should be visible to the users of the Invenio search
interface, it must be enabled for one or several collections. A rank
method can be visible in the search interface of the whole site, or just
one collection. The collections in the upper list box does not show the
rank method in the search interface to the user. To change this select
the wanted collection and press 'Enable' to enable the rank method for
this collection. The collections that the method has been activated for,
is shown in the lower list box. To remove a collection, select it and
press the 'Disable' button to remove it from the list of collections
which the rank method is enabled for.

4. BibRank Daemon
-----------------

The bibrank daemon read the necessary metadata from the Invenio database
and combines the read metadata in different ways to create the ranking
data necessary at searchtime to fast be able to rank the results.

4.1 Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~

    ::

        Usage bibrank:
               bibrank -wjif -a --id=0-30000,30001-860000 --verbose=9
               bibrank -wjif -d --modified='2002-10-27 13:57:26'
               bibrank -wwrd --recalculate --collection=Articles
               bibrank -wwrd -a -i 234-250,293,300-500 -u admin@localhost

         Ranking options:
         -w, --run=r1[,r2]         runs each rank method in the order given

         -c, --collection=c1[,c2]  select according to collection
         -i, --id=low[-high]       select according to doc recID
         -m, --modified=from[,to]  select according to modification date
         -l, --lastupdate          select according to last update

         -a, --add                 add or update words for selected records
         -d, --del                 delete words for selected records
         -S, --stat                show statistics for a method

         -R, --recalculate         recalculate weigth data, used by word frequency method
                                   should be used if ca 1% of the document has been changed
                                   since last time -R was used
         Repairing options:
         -k,  --check              check consistency for all records in the table(s)
                                   check if update of ranking data is necessary
         -r, --repair              try to repair all records in the table(s)
         Scheduling options:
         -u, --user=USER           user name to store task, password needed
         -s, --sleeptime=SLEEP     time after which to repeat tasks (no)
                                    e.g.: 1s, 30m, 24h, 7d
         -t, --time=TIME           moment for the task to be active (now)
                                    e.g.: +15s, 5m, 3h , 2002-10-27 13:57:26
         General options:
         -h, --help                print this help and exit
         -V, --version             print version and exit
         -v, --verbose=LEVEL       verbose level (from 0 to 9, default 1)

4.2 Using BibRank
~~~~~~~~~~~~~~~~~

Step 1 - Adding the rank option to the search interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To be able to add the needed ranking data to the database, you first
have to add the rank method to the database, and add the wished code you
want to use together with it. The name of the configuration file in the
next section, needs to have the same name as the code stored in the
database.

Step 2 - Get necessary external data (ex. jif values)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Find out what is necessary of data for each method. The bibrankgkb
documentation below may be of assistance.

**Example of necessary data** (``jif.kb`` - journal impact factor
knowledge base)

    ::

        Phys. Rev., D---3.838
        Phys. Rev. Lett.---6.462
        Phys. Lett., B---4.213
        Nucl. Instrum. Methods Phys. Res., A---0.964
        J. High Energy Phys.---8.664

Step 3 - Modify the configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The configuration files for the different rank methods has different
option, so verify that you are using the correct configuration file and
rank method. A template for each rank method exists as examples, but may
not work on all configurations of Invenio. For a description of each
rank method and the configuration necessary, check section 6 below.

Step 4 - Add the ranking method as a scheduled task
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the configuration is okay, you can add the bibrank daemon to the
task scheduler using the scheduling options. The daemon can then do a
update of the rank method once each day or similar automatically.

**Example**

    ::

        $ bibrank -wjif -r
        Task #53 was successfully scheduled for execution.

It is adviced to run the BibRank daemon using no parameters, since the
default settings then will be used.

**Example**

    ::

        $ bibrank
        Task #2505 was successfully scheduled for execution.

Step 5 - Running bibrank manually
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If BibRank is scheduled without any parameters, and no records has been
modified, you may get a output like shown below.

**Example**

    ::

        $ bibrank 2505
        2004-09-07 17:51:46 --> Task #2505 started.
        2004-09-07 17:51:46 -->
        2004-09-07 17:51:46 --> Running rank method: Number of downloads.
        2004-09-07 17:51:47 --> No new records added since last time method was run
        2004-09-07 17:52:10 -->
        2004-09-07 17:52:10 --> Running rank method: Journal Impact Factor.
        2004-09-07 17:52:10 --> No new records added since last time method was run
        2004-09-07 17:52:11 --> Reading knowledgebase file: /home/invenio/etc/bibrank/cern_jif.kb
        2004-09-07 17:52:11 --> Number of lines read from knowledgebase file: 420
        2004-09-07 17:52:11 --> Number of records available in rank method: 0
        2004-09-07 17:52:12 -->
        2004-09-07 17:52:12 --> Running rank method: Word frequency
        2004-09-07 17:52:13 --> rnkWORD01F contains 256842 words from 677912 records
        2004-09-07 17:52:14 --> rnkWORD01F is in consistent state
        2004-09-07 17:52:14 --> Using the last update time for the rank method
        2004-09-07 17:52:14 --> No new records added. rnkWORD01F is up to date
        2004-09-07 17:52:14 --> rnkWORD01F contains 256842 words from 677912 records
        2004-09-07 17:52:14 --> rnkWORD01F is in consistent state
        2004-09-07 17:52:14 --> Task #2505 finished.

Step 6 - Fast update of modified records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you just want to update the latest additions or modified records, you
may want to do a faster update by running the daemon without the
recalculate option. (the recalculate option is off by default). This may
cause lower accurancy when ranking.

5. BibRank Methods
------------------

Each BibRank method has a configuration file which contains different
parameters and sections necessary to do the ranking.

5.1 Single tag rank method
~~~~~~~~~~~~~~~~~~~~~~~~~~

This method uses one MARC tag together with a file containing possible
values for this MARC tag together with a ranking value. This data is
used to create a structure containing the record id associated with the
ranking value based on the content of the tag. The method can be used
for various ways of ranking like ranking by Journal Impact Factor, or
use it to let certain authors always appear top of a search. The
parameters needed to be configured for this method is the
'tag','kb\_src' and 'check\_mandatory\_tags'.


**Example**::

    [rank_method]
    function = single_tag_rank_method

    [single_tag_rank]
    tag = 909C4p
    kb_src = /home/invenio/etc/bibrank/jif.kb
    check_mandatory_tags = 909C4c,909C4v,909C4y

**Explanation:**::

    [rank_method]
      ##The function which is responsible for doing the work. Should not be changed
      function = single_tag_rank_method
     
      ##This section must be available if the single_tag_rank_method is going to be used
      [single_tag_kb]
     
      ##The tag which got the value to be searched for on the left side in the kb file (like the journal name)
      tag = 909C4p
     
      ##The path to the kb file which got the content of the tag above on left side, and value on the left side
      kb_src = /home/invenio/etc/bibrank/jif.kb
     
      ##Tags that must be included for a record to be added to the ranking data, to disable remove tags
      check_mandatory_tags = 909C4c,909C4v,909C4y
         

The kb\_src file must contain data on the form:::

    Phys. Rev., D---3.838
    Phys. Rev. Lett.---6.462
    Phys. Lett., B---4.213
    Nucl. Instrum. Methods Phys. Res., A---0.964
    J. High Energy Phys.---8.664

The left side must match the content of the tag mentioned in the tag
variable.

5.2 Word Similarity/Similar Records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Word Similarity/Similar Records method uses the content of the tags
selected to determine which records is most relevant to a query, or most
similar to a selected record. This method got a lot of parameters to
configure, and it may need some tweaking to get the best result. The
BibRank code for this method has to be 'wrd' for it to work. For best
result, it is adviced to install the stemming module mentioned in
INSTALL, and use a stopword list containing stopwords in the languages
the records exists in. The stemmer and stopword list is used to get
better results and to limit the size of the index, thus making ranking
faster and more accurate. For best result with the stemmer, it is
important to mark each tag to be used with the most common language the
value of the tag may be in. It is adviced to not change the
'function','table' and the parameters under [find\_similar]. If the
stemmer is not installed, to assure that no problems exists, the
'stem\_if\_avail' parameter should be set to 'no'. Each tag to be used
by the method has to be given a point. The number of points describes
how important one word is in this tag.

When running BibRank to update the index for this rank method, it is not
necessary to recalculate each time, but when large number of records has
been updated/added, it can be wise to recalculate using the recalculate
parameter of BibRank.

**Example**::

    [rank_method]
    function = word_similarity

    [word_similarity]
    stemming = en
    table = rnkWORD01F
    stopword = True
    relevance_number_output_prologue = (
    relevance_number_output_epilogue = )
     #MARC tag,tag points, tag language
    tag1 = 6531_a, 2, en
    tag2 = 695__a, 1, en
    tag3 = 6532_a, 1, en
    tag4 = 245__%, 10, en
    tag5 = 246_%, 1, fr
    tag6 = 250__a, 1, en
    tag7 = 711__a, 1, en
    tag8 = 210__a, 1, en
    tag9 = 222__a, 1, en
    tag10 = 520__%, 1, en
    tag11 = 590__%, 1, fr
    tag12 = 111__a, 1, en
    tag13 = 100__%, 2, none
    tag14 = 700__%, 1, none
    tag15 = 721__a, 1, none


    [find_similar]
    max_word_occurence = 0.05
    min_word_occurence = 0.00
    min_word_length = 3
    min_nr_words_docs = 3
    max_nr_words_upper = 20
    max_nr_words_lower = 10
    default_min_relevance = 75

**Explanation:**::

    [rank_method]
     #internal name for the bibrank program, do not modify
    function = word_similarity

    [word_similarity]
     #if stemmer is available, default stemminglanguage should be given here. Adviced to turn off if not installed
    stemming = en
     #the internal table to load the index tables from.
    table = rnkWORD01F
     #remove stopwords?
    stopword = True
     #text to show before the rank value when the search result is presented. <-- to hide result
    relevance_number_output_prologue = (
     #text to show after the rank value when the search result is presented. --> to hide result
    relevance_number_output_epilogue = )

     #MARC tag,tag points, tag language
     #a list of the tags to be used, together with a number describing the importance of the tag, and the
     #most common language for the content. Not all languages are supported. Among the supported ones are:
     #fr/french, en/english, no/norwegian, se/swedish, de/german, it/italian, pt/portugese

     #keyword
    tag1 = 6531_a, 1, en #keyword
    tag2 = 695__a, 1, en #keyword
    tag3 = 6532_a, 1, en #keyword
    tag4 = 245__%, 10, en #title, the words in the title is usually describing a record very good.
    tag5 = 246_% , 1, fr #french title
    tag6 = 250__a, 1, en #title
    tag7 = 711__a, 1, en #title
    tag8 = 210__a, 1, en #abbreviated
    tag9 = 222__a, 1, en #key title

    [find_similar]
     #term should exist in maximum X/100% of documents
    max_word_occurence = 0.05
     #term should exist in minimum X/100% of documents
    min_word_occurence = 0.00
     #term should be atleast 3 characters long
    min_word_length = 3
     #term should be in atleast 3 documents or more
    min_nr_words_docs = 3
     #do not use more than 20 terms for "find similar"
    max_nr_words_upper = 20
     #if a document contains less than 10 terms, use much used terms too, if not ignore them
    max_nr_words_lower = 10
     #default minimum relevance value to use for find similar
    default_min_relevance = 75

Tip: When executing a search using a ranking method, you can add
"verbose=1" to the list of parameteres in the URL to see which terms
have been used in the ranking.

5.2.1 Solr Word Similarity/Similar Records
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Solr Word Similarity/Similar Records method uses Solr to serve word
similarity ranking and similar records queries. To use it, the following
steps are necessary:

First, Solr is installed:::

    $ cd <invenio source tree>
    $ sudo make install-solrutils

Second, ``invenio-local.conf`` is amended:::

    CFG_SOLR_URL = http://localhost:8983/solr

Third, ``idxINDEX`` is amended:::

    UPDATE idxINDEX SET indexer='SOLR' WHERE name='fulltext'

Fourth, the Solr word similarity ranking method is used:::

    <invenio installation>/etc/bibrank$ sudo -u www-data cp template_word_similarity_solr.cfg wrd.cfg

Fifth, Solr is started:::

    <invenio installation>/lib/apache-solr-3.1.0/example$ sudo -u www-data java -jar start.jar

5.3 Time-dependent citation counts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This ranking method is an extension of the well known "rank by number of
citation" method. The difference is that the citations are weighted
differently, based on their publication year. In this way, we can weight
more the newly acquired citations, rather than treating them in the same
way as older ones. By doing this, rather than just counting the
citations, we can identify highly cited publications that are currently
of interest for the scientific community.

The different weighting is controlled by the time-decay factor. This
factor can have values between 0 and 1. With a time-decay factor of 0
the algorithm will behave as the classical "rank by number of
citations". With a time-decay factor of 1, the algorithm will take into
consideration only the citations that come from documents published in
the current year. The time-decay parameter can be adjusted in the
configuration file. In order for the algorithm to run, the appropriate
tags for the publication year and the creation date of a document, need
to be set.

Please take a look in the configuration file for further explanations.

5.4 Link-based ranking
~~~~~~~~~~~~~~~~~~~~~~

This ranking method is an extension of the well known pagerank method.
Unlike ranking by number of citations, where all the citations are
weighed equally, the link-based ranking weights each citation based on
its importance. A high rank for a publication means not necessary that
it has been cited a lot, but that it has been cited by other high ranked
publications. In this way it can identify a large number of modestly
cited publications that contain important results for the scientific
community. In other words, it associates each publication with an
"all-time achievement" rank.

In the case of an incomplete citation graph (a lot of citations missing
from the repository), the link-based ranking can cause "artificial
inflation" of some of the weights, thus creating errors in ranking. In
order to correct this, we advise the use of the external citations (by
setting the "use\_external\_citations" parameter to "yes"). This will
assure the correct propagation of the weight through the network. We use
the term of "external links" to denote all the citations that are
missing from the database, and "internal links" to denote all the
citations available in the database. The algorithm can be adjusted by
changing the values of the two main parameters (ext\_alpha and
ext\_beta).

For more details, please consult the configuration file.

5.5 Time-dependent link-based ranking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method combines the previous two methods. Its purpose is to
highlight important publications that are currently of interest for the
scientific community. This method is not really suited to repositories
that allow cycles in their citation graph. Even the bibliographic data
sets can allow cycles due to certain inconsistencies in the publication
dates or in the listing of references. Since some of the publications
are not dated, the identification/removal of the cycles can produce a
high computational overhead. Because of this and of the link-based
ranking which iteratively propagates the weight in the graph, when a
strong time decay factor is used, the newly published documents that are
part of a cycle accumulate artificial weight, resulting in an inexact
ranking.

For more details, please consult the configuration file.

5.6 Combine method
~~~~~~~~~~~~~~~~~~

The 'Combine method' is running each method mentioned in the config file
and adding the score together based on the importance of the method
given by the percentage.

**Example**::

    [rank_method]
    function = combine_method
    [combine_method]
    method1 = cern_jif,33
    method2 = cern_acc,33
    method3 = wrd,33
    relevance_number_output_prologue = (
    relevance_number_output_epilogue = )

**Explanation:**::

    [rank_method]
     #tells which method to use, do not change
    function = combine_method
    [combine_method]
     #each line tells which method to use, the code is the same as in the BibRank interface, the number describes how
     #much of the total score the method should count.
    method1 = jif,50
    method2 = wrd,50
     #text to be shown before the rank value on the search result screen.
    relevance_number_output_prologue = (
     #text to be shown after the rank value on the search result screen.
    relevance_number_output_epilogue = )

6. bibrankgkb Tool
------------------

For some ranking methods, like the single\_tag\_rank method, a knowledge
base file (kb) with the needed data in the correct format is necessary.
This file can be created using the bibrankgkb tool which can read the
data either from the Invenio database, from several web pages using
regular expressions, or from another file. In case one source has
another naming convention, bibrank can convert between them using a
convert file.

6.1 Command Line Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~

    ::

        Usage: bibrankgkb %s [options]
             Examples:
               bibrankgkb --input=bibrankgkb.cfg --output=test.kb
               bibrankgkb -otest.cfg -v9
               bibrankgkb

         Generate options:
         -i,  --input=file          input file, default from /etc/bibrank/bibrankgkb.cfg
         -o,  --output=file         output file, will be placed in current folder
         General options:
         -h,  --help                print this help and exit
         -V,  --version             print version and exit
         -v,  --verbose=LEVEL       verbose level (from 0 to 9, default 1)

6.2 Using bibrankgkb
~~~~~~~~~~~~~~~~~~~~

Step 1 - Find sources
^^^^^^^^^^^^^^^^^^^^^

Since some of the data used for ranking purposes is not freely
available, it cannot be bundled with Invenio. To get hold of the
necessary data, you may find it useful to ask your library if they have
a copy of the data that can be used (like the Journal Impact Factors
from the Science Citation Index), or use google to search the web for
any public source.

Step 2 - Create configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The default configuration file is shown below.

    ::

         ##The main section
        [bibrankgkb]
         ##The url to a web page with the data to be read, does not need to have the same name as this one, but if there
        are several links, the url parameter should end with _0->
        url_0 = http://www.taelinke.land.ru/impact_A.html
        url_1 = http://www.taelinke.land.ru/impact_B.html
        url_2 = http://www.taelinke.land.ru/impact_C.html
        url_3 = http://www.taelinke.land.ru/impact_DE.html
        url_4 = http://www.taelinke.land.ru/impact_FH.html
        url_5 = http://www.taelinke.land.ru/impact_I.html
        url_6 = http://www.taelinke.land.ru/impact_J.html
        url_7 = http://www.taelinke.land.ru/impact_KN.html
        url_8 = http://www.taelinke.land.ru/impact_QQ.html
        url_9 = http://www.taelinke.land.ru/impact_RZ.html
         ##The regular expression for the url mentioned should be given here
        url_regexp =

         ##The various sources that can be read in, can either be a file, web page or from the database
        kb_1 = /home/invenio/modules/bibrank/etc/cern_jif.kb
        kb_2 = /home/invenio/modules/bibrank/etc/demo_jif.kb
        kb_2_filter = /home/invenio/modules/bibrank/etc/convert.kb
        kb_3 = SELECT id_bibrec,value FROM bib93x,bibrec_bib93x WHERE tag='938__f' AND id_bibxxx=id
        kb_4 = SELECT id_bibrec,value FROM bib21x,bibrec_bib21x WHERE tag='210__a' AND id_bibxxx=id
         ##This points to the url above (the common part of the url is 'url_' followed by a number
        kb_5 = url_%s

         ##This is the part that will be read by the bibrankgkb tool to determine what to read.
         ##The first two part (separated by ,,) gives where to look for the conversion file (which convert
         ##the names between to formats), and the second part is the data source. A conversion file is not
         ##needed, as shown in create_0. If the source is from a file, url or the database, it must be
         ##given with file,www or db. If several create lines exists, each will be read in turn, and added
         ##to a common kb file.
         ##So this means that:
         ##create_0: Load from file in variable kb_1 without converting
         ##create_1: Load from file in variable kb_2 using conversion from file kb_2_filter
         ##create_3: Load from www using url in variable kb_5 and regular expression in url_regexp
         ##create_4: Load from database using sql statements in kb_4 and kb_5
        create_0 = ,, ,,file,,%(kb_1)s
        create_1 = file,,%(kb_2_filter)s,,file,,%(kb_2)s
         #create_2 = ,, ,,www,,%(kb_5)s,,%(url_regexp)s
         #create_3 = ,, ,,db,,%(kb_4)s,,%(kb_4)s

When you have found a source for the data, created the configuration
file, it may be necessary to create an conversion file, but this depends
on the conversions used in the available data versus the conversion used
in your Invenio installation.

The available data may look like this:

    ::

        COLLOID SURFACE A---1.98

But in Invenio you are using:

    ::

        Colloids Surf., A---1.98

By using a conversion file like:

    ::

        COLLOID SURFACE A---Colloids Surf., A

You can convert the source to the correct naming convention.

    ::

        Colloids Surf., A---1.98

Step 3 - Run tool
^^^^^^^^^^^^^^^^^

When ready to run the tool, you may either use the default file
(/etc/bibrank/bibrankgkb.cfg), or use another one by giving it using the
input variable '--input'. If you want to test the configuration, you can
use '--verbose=9' to output on screen, or if you want to save it to a
file, use '--output=filename', but remember that the file will be saved
in the program directory.

The output may look like this:

    ::

        $ ./bibrankgkb -v9
        2004-03-11 17:30:17 --> Running: Generate Knowledge base.
        2004-03-11 17:30:17 --> Reading data from file: /home/invenio/etc/bibrank/jif.kb
        2004-03-11 17:30:17 --> Reading data from file: /home/invenio/etc/bibrank/conv.kb
        2004-03-11 17:30:17 --> Using last resource for converting values.
        2004-03-11 17:30:17 --> Reading data from file: /home/invenio/etc/bibrank/jif2.kb
        2004-03-11 17:30:17 --> Converting between naming conventions given.
        2004-03-11 17:30:17 --> Colloids Surf., A---1.98
        2004-03-11 17:30:17 --> Phys. Rev. Lett.---6.462
        2004-03-11 17:30:17 --> J. High Energy Phys.---8.664
        2004-03-11 17:30:17 --> Nucl. Instrum. Methods Phys. Res., A---0.964
        2004-03-11 17:30:17 --> Phys. Lett., B---4.213
        2004-03-11 17:30:17 --> Phys. Rev., D---3.838
        2004-03-11 17:30:17 --> Total nr of lines: 6
        2004-03-11 17:30:17 --> Time used: 0 second(s).

7. Additional Information
-------------------------

- `BibRank Internals </help/hacking/bibrank-internals>`__
