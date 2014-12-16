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

.. _bibmatch-admin-guide:

BibMatch Admin Guide
====================


1. Overview
-----------

1.1 What is BibMatch
~~~~~~~~~~~~~~~~~~~~

BibMatch is a tool for matching bibliographic meta-data records against
a local or remote Invenio repository. The incoming records can be
matched against zero, one or more then one records. This way, it is
possible to identify potential duplicate entries before they are
uploaded into the repository. This can also be helpful in detecting
already existing duplicates in the database.

BibMatch also acts as a filter for incoming records, by splitting the
records into 'new records' or 'existing records'. In most cases this
separation makes a big difference when ingesting content into a digital
repository.

1.2 Features
~~~~~~~~~~~~

-  Matches meta-data records locally and remotely
-  Supports user authentication to allow matching against restricted
   collections
-  Highly configurable match validation step for reliable matching
   results
-  Allows full customisation of the search queries used to find matching
   candidates
-  Incoming meta-data can be manipulated through BibConvert formatting
   functions
-  Supports transliteration of Unicode meta-data into ASCII (useful for
   legacy systems)

2. Usage
--------

2.1 Basic usage
~~~~~~~~~~~~~~~

Input records
^^^^^^^^^^^^^

BibMatch needs a set of records to match. You can give BibMatch these
records in two ways:

By standard input:::

    $ bibmatch < input.xml

or, by *-i* parameter:::

    $ bibmatch -i input.xml


Output records
^^^^^^^^^^^^^^

When BibMatch matches records, they will be classified in one of 4
ways:

-  **Match** - exact match found
-  **Ambiguous** - record matches more then one record
-  **Fuzzy** - record *may* match a record
-  **New** - record does not match any record

You can choose which types of records to output after matching has
completed by specifying it in the command:::

    $ bibmatch --print-match < input.xml
    $ bibmatch --print-new < input.xml

You can also output all matching results to a set of files, by
specifying a filename-prefix to the command-line option *-b*:::

    $ bibmatch -b output_results < input.xml

This will create a set of 4 files: *output\_results.matched.xml*,
*output\_results.new.xml*, *output\_results.fuzzy.xml*,
*output\_results.ambiguous.xml*

Matching queries
^^^^^^^^^^^^^^^^

By default, BibMatch will try to find potential record matches using the
MARC tag 245\_\_$$a, i.e. the title. In many cases this is not an
efficient metric to find all potential matching records with, because of
its ambiguous nature. As such, BibMatch provide users a way to specify
the exact queries to use and where to extract meta-data to put in the
queries.

Using the command-line option *-q* you can specify your own
*querystrings* to use when searching for records. Read more about
querystrings `here <#querystrings>`__.

For example, if available in the meta-data, you can search using the
ISBN or DOI, which *usually* are stable identifiers:::

    $ bibmatch -q "[020__a] or [0247_a]" -b output_results < input.xml

As you can see, any data from the input record you want to replace in
the query is referenced using square-brackets [] containing the exact
MARC notation.

You can specify several *-q* queries and they will all be performed in
order, until a match is found. If you want to avoid specifying long
complicated query-strings every time, you can use short-hand *template
queries* that can be defined in the configuration of BibMatch. (See
hacking guide)

Match remote installations
^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, BibMatch will try to match records on the local
installation. In order to match against records on a remote Invenio
installation (like http://cds.cern.ch or http://inspire-hep.net) you can
use the option *-r*:::

    $ bibmatch -r "http://cds.cern.ch" -q "[020__a] or [0247_a]" -b output_results < input.xml

If the remote installation requires user authentication, you can also
specify this using *--user*. You will then be prompted for a password:::

    $ bibmatch -r "http://cds.cern.ch" --user admin -q "[020__a] or [0247_a]" -b output_results < input.xml


Using TEXTMARC
^^^^^^^^^^^^^^

BibMatch usually works with MARCXML, but you can still input TEXTMARC
files that will be automatically converted to MARCXML in BibMatch. If
you want to also receive the output in TEXTMARC (limited support) you
can use the command-line option *-t*:::

    $ bibmatch -b out.marc -t < input.marc


2.2 Advanced usage
~~~~~~~~~~~~~~~~~~

When matching records against a repository you *may* sometimes want to
update or replace any existing records in the database with the given
records. In order to allow for easy upload after BibMatch has run, you
can use the *-a* parameter to tell BibMatch to add the matched records
001 identifier.::

    $ bibmatch -q "[020__a] or [0247_a]" -b output_records -a < input.xml

To match using BibConvert formats to manipulate MARC field-values from
the input records. See `BibConvert Admin
Guide </help/admin/bibconvert-admin-guide#C.3.4>`__
for more details on formats. An example of extracting the first word
from the 100\_\_a field and lower-case it:::

    $ bibmatch --query-string=\"[245__a] [100__a::WORDS(1,R)::DOWN()]" < input.xml > output.xml

You can also search directly in specific collection(s) in the repository
using the *--collection* option. To match more then one collection,
separate each with comma:::

    $ bibmatch --collection 'Books,Articles' < input.xml

If some collections are restricted or you are searching for restricted
meta-data fields in the repository, you can specify a user login with
the *--user* command:::

    $ bibmatch --collection 'Theses' --user admin < input.xml


3. More examples
----------------

3.1 More examples
~~~~~~~~~~~~~~~~~

To match records on title in the title index, also print out only new
(unmatched) ones:::

    $ bibmatch --print-new -q "[title]" --field=\"title\" < input.xml > output.xml

To print potential duplicate entries before manual upload using
predefined queries, use:::

    $ bibmatch --print-match -q title-author < input.xml > output.xml

Two options for matching on multiple fields, including predefined fields
(title, author etc.):::

    $ bibmatch --query-string="[245__a] [author]" < input.xml > output.xml
    $ bibmatch --query-string="245__a||author" < input.xml > output.xml

To print "fuzzy" (almost matching by title) records:::

    $ bibmatch --print-fuzzy  < input.xml > output.xml

An example of use of predefined searching::

    $ bibmatch --print-match -q title-author < input.xml > output.xml


Appendix
--------

A. Querystrings
~~~~~~~~~~~~~~~

Querystrings determine which type of query/strategy to use when
searching for the matching records in the database.

**Predefined querystrings:**

There are some predefined querystrings available:

-  **title** - standard title search. (i.e. "this is a title") (default)
-  **title-author** - title and author search (i.e. "this is a title AND
   Lastname, F")
-  **reportnumber** - reportnumber search (i.e.
   reportnumber:REP-NO-123).

You can also add your own predefined querystrings inside invenio.conf
file.

You can structure your query in different ways:

-  Old-style: fieldnames separated by '\|\|' (conforms with earlier
   BibMatch versions):

   ::

        -q "773__p||100__a"

-  New-style: Invenio query syntax with "bracket syntax":

   ::

        -q "773__p:\"[773__p]\" 100__a:[100__a]"

Depending on the structure of the query, it will fetch associated values
from each record and put it into the final search query. i.e in the
above example it will put journal-title from 773\_\_p.

When more then one value/datafield is found, i.e. when looking for
700\_\_a (additional authors), several queries will be put together to
make sure all combinations of values are accounted for. The queries are
separated with given operator (-o, --operator) value.

Note: You can add more then one query to a search, just give more (-q,
--query-string) arguments. The results of all queries will be combined
when matching.

B. BibConvert formats
~~~~~~~~~~~~~~~~~~~~~

Another option to further improve your matching strategy is to use
BibConvert formats. By using the formats available by BibConvert you can
change the values from the retrieved record-fields.

i.e. using WORDS(1,R) will only return the first (1) word from the right
(R). This can be very useful when adjusting your matching parameters to
better match the content. For example only getting authors last-name
instead of full-name.

You can use these formats directly in the querystrings (indicated by '::'):

-  Old-style: -q "100\_\_a::WORDS(1,R)::DOWN()"
   This query will take first word from the right from 100\_\_a and
   also convert it to lower-case.
-  New-style: -q "100\_\_a:[100\_\_a::WORDS(1,R)::DOWN()]"
   See BibConvert documentation for a more detailed explanation of
   formats.

C. Predefined fields
~~~~~~~~~~~~~~~~~~~~

In addition to specifying distinct MARC fields in the querystrings you
can use predefined fields as configured in the LOCAL(!) Invenio system.
These fields will then be mapped to one or more fieldtags to be
retrieved from input records.

Common predefined fields used in querystrings: (for Invenio demo site,
your fields may vary!)

::

    'abstract', 'affiliation', 'anyfield', 'author', 'coden', 'collaboration',
     'collection', 'datecreated', 'datemodified', 'division', 'exactauthor', 'exactfirstauthor',
     'experiment', 'fulltext', 'isbn', 'issn', 'journal', 'keyword', 'recid',
     'reference', 'reportnumber', 'subject', 'title', 'year'

D. BibMatch commmand-line tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    Output:

     -0 --print-new (default) print unmatched in stdout
     -1 --print-match print matched records in stdout
     -2 --print-ambiguous print records that match more than 1 existing records
     -3 --print-fuzzy print records that match the longest words in existing records

     -b --batch-output=(filename). filename.new will be new records, filename.matched will be matched,
          filename.ambiguous will be ambiguous, filename.fuzzy will be fuzzy match
     -t --text-marc-output transform the output to text-marc format instead of the default MARCXML

     Simple query:

     -q --query-string=(search-query/predefined-query) See "Querystring"-section below.
     -f --field=(field)

     General options:

     -n   --noprocess          Do not print records in stdout.
     -i,  --input              use a named file instead of stdin for input
     -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)
     -r,  --remote=URL         match against a remote Invenio installation (Full URL, no trailing '/')
                               Beware: Only searches public records attached to home collection
     -a,  --alter-recid        The recid (controlfield 001) of matched or fuzzy matched records in
                               output will be replaced by the 001 value of the matched record.
                               Note: Useful if you want to replace matched records using BibUpload.
     -z,  --clean              clean queries before searching
     --no-validation           do not perform post-match validation
     -h,  --help               print this help and exit
     -V,  --version            print version information and exit

     Advanced options:

     -m --mode=(a|e|o|p|r)     perform an advanced search using special search mode.
                                 Where mode is:
                                   "a" all of the words,
                                   "o" any of the words,
                                   "e" exact phrase,
                                   "p" partial phrase,
                                   "r" regular expression.

     -o --operator(a|o)        used to concatenate identical fields in search query (i.e. several report-numbers)
                                 Where operator is:
                                   "a" boolean AND (default)
                                   "o" boolean OR

     -c --config=filename      load querystrings from a config file. Each line starting with QRYSTR will
                               be added as a query. i.e. QRYSTR --- [title] [author]

     -x --collection           only perform queries in certain collection(s).
                               Note: matching against restricted collections requires authentication.

     --user=USERNAME           username to use when connecting to Invenio instance. Useful when searching
                               restricted collections. You will be prompted for password.

