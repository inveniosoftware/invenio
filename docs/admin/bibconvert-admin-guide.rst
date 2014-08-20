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

.. _bibconvert-admin-guide:

BibConvert Admin Guide
======================

A. Overview
-----------

BibConvert utility enables you to convert metadata records from various
metadata formats into another metadata format supported by the Invenio
local database. It is designed to process XML harvested metadata
records, converting them into MARC21 before they are uploaded into the
database. However, BibConvert is flexible enough to deal also with other
structured metadata according to your needs, and offers a way to
actually insert what you want into the database.

BibConvert is suitable for tasks such as conversion of records received
from multiple data sources, or conversion of records from another system
that may support a different metadata format.

In order to cover a wider range of possible conversions, BibConvert has
2 different modes, each dealing with different types of data, and each
using different configuration files.

**Plain text-oriented mode:**
    Deals with source data being typically structured with line breaks,
    and character-based separators. You can use this mode when you need
    to process line-based data, such as comma/tab separated values.
    Still, this mode is powerful enough to convert complex structures,
    at the cost of a more complex configuration.
**XML-oriented mode**
    Convert source data being encoded in XML. Provided you have
    installed a supported XSLT processor on your machine, BibConvert can
    make use of standard XSLT to interpret your XML data.

In addition to XSLT, we provide a home-made solution for converting
XML source data. It uses our own BFX language as transformation
language, extended with XPath for node selections.

You should consider using this solution only in the case where you
have not installed (or do not want to install) an XSLT processor on your
machine.

B. XML-Oriented Mode
--------------------

1. Configuration File Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using XSLT
^^^^^^^^^^

You can use standard XSL stylesheets to transform your source data.
Have a look at the provided samples in ``etc/bibconvert/config``
directory of your Invenio installation.

Using BFX
^^^^^^^^^

BFX (BibFormat for XML) uses a syntax similar to XSLT. Roughly they
only differ in the name of the tags.
More documentation about it is to be added soon (FIXME).
Have a look at the provided samples in ``etc/bibconvert/config``
directory of your Invenio installation to learn more about it.

2. Running BibConvert
~~~~~~~~~~~~~~~~~~~~~

BibConvert in XML-oriented mode has only 1 parameter: ``-c``. It is used
to specify which transformation stylesheet to apply to the piped XML.

::

    $ bibconvert -coaidc2marcxml.xsl < sample.xml > /tmp/record.xml

If the stylesheet you want to use is installed in the
``etc/bibconvert/config`` directory of your Invenio installation, then
you can just refer to it by its filename. Otherwise use the full path to
the file.

C. Plain Text-Oriented Mode
---------------------------

1. Configuration File Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

OAI DublinCore into MARC21 and OAI MARC into MARC21 configurations will
be provided as default configuration, ensuring the standard uploading
sequence (incl. `OAIHarvest <oaiharvest-admin-guide>`__ and
`BibUpload <bibupload-admin-guide>`__ utilities). Other configurations
can be created according to your needs. The configuration file that has
to be created for each data source is a text file with following
structure:

    ::

          ### the configuration starts here
          ### Configuration of bibconvert templates
          ### source data :
         
          === data extraction configuration template ===
          ### here comes the data extraction configuration template
          #   entry example:
         
          AU---%A---MAX---;---
         
          #   extracts maximum available data by field from metadata record
          #   the values are found between specified tags
          #   in this case between the '%A' tag and other tags defined
          #   repetitive values are recognized by a semicolon separator
          #   resp. by multiple presence of '%A' tag
         
          ===   data source configuration template   ===
          ### here comes the data source configuration template
          #   entry example:
         
          AU---<:FIRSTNAME:>-<:SURNAME:>
         
          #   describes the contents of extracted source data fields
          #   in this case, the field AU is described as having two distinct subfields
         
          ===   data target configuration template   ===
          ### here comes the data target configuration template
          #   entry example:
         
          AU::CONF(AU,,0)---<datafield id="700" ind1="" ind2=""><subfield code="a"><:AU*::SURNAME::CAP():>, <AU*::FIRSTNAME::ABR():></subfield></datafield>
         
          #   This section concerns rather the desired output, while previous two were focused on the data source structures.
          #   Each line equals to one output line, composed of given literals and values from extracted source data fields.
          #   In this example, the XML Marc21 output line is defined,
          #   containing re-formatted values of source fields SURNAME and FIRSTNAME
         
          ### the configuration ends here

Having prepared a configuration, the BibConvert will convert the source
data file according to it in a batch mode. The BibConvert is fully
compatible with the Uploader1.x configuration language. For more
information, have a look at the `BibConvert Configuration
Guide <#C.3>`__ section below.

2. Running BibConvert
~~~~~~~~~~~~~~~~~~~~~

For a fully functional demo, consider the following sample input data:

    `sample.dat </static/bibconvert-admin-guide/sample.dat>`__
    -- sample bibliographic data to be converted and inputted into
    Invenio
    `sample.cfg </static/bibconvert-admin-guide/sample.cfg>`__
    -- sample configuration file, featuring knowledge base demo

To convert the above data into XML MARC, use the following command:

    ::

        $ bibconvert -b'<collection>' -csample.cfg -e'</collection>' < sample.dat > /tmp/sample.xml

and see the XML MARC output file. You would then continue the upload
procedure by calling `BibUpload <bibupload-admin-guide>`__.

Other useful BibConvert configuration examples:

    `dcq.cfg </static/bibconvert-admin-guide/dcq.cfg>`__
    -- Qualified Dublin Core in SGML to XML MARC example
    `dcq.dat </static/bibconvert-admin-guide/dcq.dat>`__
    -- corresponding data file, featuring collection identifiers demo

    `dcxml-to-marcxml.cfg </static/bibconvert-admin-guide/dcxml-to-marcxml.cfg>`__
    -- OAI XML Dublin Core to XML MARC example

    `bibtex.cfg </static/bibconvert-admin-guide/bibtex.cfg>`__
    -- BibTeX to XML MARC example

3. BibConvert Configuration Guide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Conventions
^^^^^^^^^^^

- comment line starts with '#' sign in the first column
- each section is declared by a line starting with '==='
  (further characters on the line are ignored)
- values are separated by '---'

3.1 Step 1 Definition of Source record
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Create/edit "data extraction configuration template" section of the
  configuration file.
- Each line of this section stands for a definition of one source
  field:

**name---keyword---terminating string---separator---**

- Choose a (valid) name allowed by the system
- Enter **keyword** and **terminating string**, which are boundary
  tags for the wanted value extraction
- In case the field is repetitive, enter the value **separator**
- "**---**\ "is mandatory separator between all values, even
  zero-length
- **MAX**/**MIN** keywords can be used instead of terminating string
  

Example of a definition of author(repetitive) and title (non-repetitive) fields:

::

      === data extraction configuration template ===
      ### here comes the data extraction configuration template
     
      AU---AU_---MAX---;---
      TI---TI_---EOL------

3.2 Step 2 Definition of Source fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Each field extracted from the source according to the definition done
in the first step can have an internal structure, which is described in
this section.*

- Create/edit "data source configuration template" section of the
  configuration file.
- Each line of this section stands for a definition of one source field
  corresponds to the name defined in the step 1

name---{CONST<:SUBFIELD:>[CONST]}}

- Enter only constants that appear systematically.
- Between two discrete subfields has to be defined a constant of a non
  zero length
- "---"is a mandatory separator between the name and the source field
  definition

Example of a definition of author(repetitive) and title (non-repetitive)
fields:

::

    ===   data source configuration template   ===
    TI---<:TI:>
    AU---<:FIRSTNAME:>-<:SURNAME:>

3.3 Step 3 Definition of target record
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*This definition describes the layout of the target record that is
created by the conversion, together with the corresponcence to the
source fields defined in step 2.*

- Create/edit "data target configuration template" section of the
  configuration file.
- Each line of this section stands for an output line created by the
  conversion.
- <name> corresponds to the name defined in the steps 1 and 2

CODE---CONST<:name::SUBFIELD::FUNCT():>CONST<:GENERATED\_VALUE:>

- **CODE** stands for a tag for readability (optional)
- "**::**\ "is a mandatory separator between the name and the subfield
  definition
- optionally, you can apply the appropriate `formatting function(s) <#C.3.4.1>`__
  and `generated values <#C.3.4.2>`__
- "**::**\ "is a mandatory separator between the subfield definition
  and the function(s)
- "**---**\ "is a mandatory separator between the tag and the output
  code definition
- mark repetitive source fields with an asterisk (\*)

Example of a definition of author (repetitive) and title
(non-repetitive) codes:

::

    AU::CONF(AU,,0)---<datafield id="700" ind1="" ind2=""><subfield code="a"><:AU*::AU:></subfield></datafield>
    TI::CONF(TI,,0)---<datafield id="245" ind1="" ind2=""><subfield code="a"><:TI::TI::SUP(SPACE, ):></subfield></datafield>

- preserve newlines in a source field for later use by formatting
  functions by marking them with "^"

Example of a definition of a book editors field in which the newlines
are preserved so that they can be processed by the JOINMULTILINES
formatting function:

::

    AU---<datafield id="773" ind1=" " ind2=" "><:BOOKEDITOR^::BOOKEDITOR::JOINMULTILINES(<subfield code="a">,</subfield>):></datafield>

    With a value such as:
    Test
    Case, A

    The results may be:
    <datafield tag="773" ind1="" ind2=""><subfield code="a">Test</subfield><subfield code="a">Case, A</subfield></datafield>

3.4 Formatting in BibConvert
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

3.4.1 Definition of formatting functions
''''''''''''''''''''''''''''''''''''''''

Every field can be processed with a variety of functions that
partially or entirely change the original value.

There are three types of functions available that take as element
either single characters, words or the entire value of processed
field.
  

Every function requires a certain number of parameters to be entered
in brackets. If an  insufficient number of parameters is present,
the function uses default values. Default values are constructed
with attempt to keep the original value.

The configuration of templates is case sensitive.

The following functions are available:

`ADD(prefix,suffix) - add prefix/suffix <#ADD>`__
`KB(kb\_file,[0-9]) -lookup in kb\_file and replace value <#KB>`__
`ABR(x,suffix)/ABRW(x,suffix) - abbreviation with suffix
addition <#ABR>`__
`ABRX() - abbreviate exclusively words longer <#ABRX>`__
`CUT(prefix,postfix) - remove substring from side <#CUT>`__
`REP(x,y) - replacement of characters <#REP>`__
`SUP(type) - suppression of characters of specified type <#SUP>`__
`LIM(n,L/R)/LIMW(str,L/R) - restriction to n letters <#LIM>`__
`WORDS(n,side) - restriction to n words from L/R <#WORDS>`__
`MINL(n)/MAXL(n) - replacement of words shorter/greater than <#MINL>`__
`MINLW(n) - replacement of short values <#MINLW>`__
`EXP(str,1\|0)/EXPW(type) - replacement of words from value if containing spec.
type/string <#EXPW>`__
`IF(value,valueT,valueF) - replace T/F value <#IF>`__
`UP/DOWN/CAP/SHAPE/NUM - lower case and upper case, shape <#UP>`__
`SPLIT(n,h,str,from)/SPLITW(sep,h,str,from) - split into more lines <#SPLIT>`__
`CONF(field,value,1/0)/CONFL(value,1/0) - confirm validity of a field <#CONF>`__
`RANGE(from,to) - confirm only entries in the specified range <#RANGE>`__
`DEFP() - default print <#DEFP>`__
`IFDEFP(field,value,1/0) - IF condition is met, default print <#IFDEFP>`__
`JOINMULTILINES(prefix,suffix) - Join a multiline string into a single line
with each segment having prefix and suffix <#JOINMULTILINES>`__
  

ADD(prefix,postfix)
^^^^^^^^^^^^^^^^^^^

default: ADD(,)    no addition

Adds prefix/postfix to the value, we can use this function to add
the proper field name as a prefix of the value itself:

ADD(WAU=,)    prefix for the first author (which may have been
taken from the field AU2)
  

KB(kb\_file)    -    kb\_file search
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: KB(kb\_file,1/0/R)

The input value is compared to a kb\_file and may be replaced by
another value. In the case that the input value is not recognized,
it is by default kept without any modification. This default can be
overridden by **\_DEFAULT\_---default value** entry in the kb\_file

The file specified in the parameter is a text file representing a
table of values that correspond to each other:

::

    {**input\_value---output\_value**\ }

    KB(file,1) searches the exact value passed.
    KB(file,0) searches the KB code inside the value passed.
    KB(file,2) as 0 but not case sensitive
    KB(file,R) replacements are applied on substrings/characters only.

    bibconvert look-up value in KB\_file in one of following modes:
    ===========================================================
    1 - case sensitive / match (default)
    2 - not case sensitive / search
    3 - case sensitive / search
    4 - not case sensitive / match
    5 - case sensitive / search (in KB)
    6 - not case sensitive / search (in KB)
    7 - case sensitive / search (reciprocal)
    8 - not case sensitive / search (reciprocal)
    9 - replace by \_DEFAULT\_ only
    R - not case sensitive / search (reciprocal) replace

Edge spaces are not considered. Output value is not further
formated.

ABR(x,trm),ABRW(x,trm)  - abbreviate term to x places with(out) postfix
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: ABR(1,.)
default: ABRW(1,.)

The words in the input value are shortened according to the
parameters specified. By default, only the initial character is kept
and the output value is terminated by a dot.

ABRW takes entire value as one word.

+-----------------------+--------------------------+--------------------------+
| example               | ABR()                    | ABR(1,)                  |
| input                 | firstname\_surname       | firstname\_surname       |
| output                | f.\_s.                   | f\_s                     |
+-----------------------+--------------------------+--------------------------+

ABRX() - abbreviate exclusively words longer than given limit
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: ABRX(1,.)

Exclusively words that reach the specified length limit in the input
value are abbreviated. No suffix is appended to the words shorter
than specified limit.

CUT(prefix,postfix) - remove substring from side
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: CUT(,)

Remove string from the value (reverse function to the "ADD")

REP(x,y)   - replace x with y
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: REP(,)    no replacement

The input value is searched for the string specified in the first
parameter. All such strings are replaced with the string specified
in the second parameter.

SUP(type,string)   - suppress chars of certain type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: SUP(,)    type not recognized

All groups of characters belonging to the type specified in the
first parameter are suppressed or replaced with a string specified
in the second parameter.

Recognized types::

    SPACE .. invisible chars incl. NEWLINE
    ALPHA .. alphabetic
    NALPHA .. not alphabetic
    NUM .. numeric
    NNUM    .. not numeric
    ALNUM  .. alphanumeric
    NALNUM  .. non alphanumeric
    LOWER  .. lower case
    UPPER  .. upper case
    PUNCT  .. punctuation
    NPUNCT  .. not punctuation


+----------------------+--------------------------+--------------------------+
| example              | SUP(SPACE,-)             | SUP(NNUM)                |
| input                | sep\_1999                | sep\_1999                |
| output               | sep-1999                 | 1999                     |
+----------------------+--------------------------+--------------------------+


LIM(n,side)/LIMW(str,side)   - limit to n letters while trimming L/R side
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

 default: LIM(0,)        no change
 default: LIMW(,R)        no change

Limits the value to the required number of characters by cutting
excess characters either on the Left or Right.

LIMW locates the first occurrence of (str) string and cut either
Left or Right side.
         
+-----------------------+--------------------------+-------------------------+
| example               | LIM(4,L)                 | LIM(4,R)                |
| input                 | sep\_1999                | sep\_1999               |
| output                | 1999                     | sep\_                   |
+-----------------------+--------------------------+-------------------------+


WORDS(n,side)  - limit to n words while trimming L/R side
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: WORDS(0,R)

Keeps the number of words specified in the first parameter and cuts
the excessive characters either on Left or Right.

+----------------------+--------------------------+--------------------------+
| example              | WORDS(1,R)               | WORDS(1,L)               |
| input                | Sep 1999                 | Sep 1999                 |
| output               | Sep                      | 1999                     |
+----------------------+--------------------------+--------------------------+

MINL(n)   - exp. words shorter than n
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: MINL(1)

All words shorter than the limit specified in the parameter are
replaced from the sentence. The words with length exactly n are kept.
         
+----------------------+--------------------------+--------------------------+
| example              | MINL(2)                  | MINL(3)                  |
| input                | History of Physics       | History of Physics       |
| output               | History of Physics       | History Physics          |
+----------------------+--------------------------+--------------------------+


MAXL(n)   - exp. words longer than n
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: MAXL(0)

All words greater in number of characters than the limit specified
in the parameter are replaced. Words with length exactly n are kept.
 
+----------------------+--------------------------+--------------------------+
| example              | MAXL(2)                  | MAXL(3)                  |
| input                | History of Physics       | History of Physics       |
| output               | of                       | of                       |
+----------------------+--------------------------+--------------------------+


MINLW(n) - replacement of short values
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: MINLW(1) (no change)

The entire value is deleted if shorter than the specified limit.
This is used for the validation of created records, where we have
20 characters in the header.
The default validation is MINLW(21), i.e. the record entry will
not be consided as valid, unless it contains at least 21 characters
including the header. This default setting can be overriden by the
-l command line option.

In order to increase the necessary length of the output line in the
configuration itself, apply the function on the total value::

    AU::MINLW(25)---CER <:SYSNO:> AU    L <:SURNAME:>, <:NAME:>


EXP(str,1\|0) - exp./aprove word containing specified string
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: EXP   (,0)     leave all value

The record is shortened by replacing words containing the specified string.

The second parameter states whether the string approves the word
(0) or disables it (1).

For example, to get the email address from the value, use the following:
         
+----------------------+--------------------------+--------------------------+
| example              | EXP(@,0)                 | EXP(:,1)                 |
| input                | mail to: libdesk@cern.ch | mail to: libdesk@cern.ch |
| output               | libdesk@cern.ch          | mail libdesk@cern.ch     |
+----------------------+--------------------------+--------------------------+


EXPW(type)   - exp. word from value if containing spec. type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: EXPW        type not recognized

The sentence is shortened by replacing words containing specified
type of character.

Types supported in EXPW function::

    ALPHA .. alphabetic
    NALPHA .. not alphabetic
    NUM .. numeric
    NNUM    .. not numeric
    ALNUM  .. alphanumeric
    NALNUM  .. non alphanumeric
    LOWER  .. lower case
    UPPER  .. upper case
    PUNCT  .. punctuation
    NPUNCT  .. non punctuation

.. note:: SPACE is not handled as a keyword, since all space characters
          are considered as word separators.

         
+----------------------+--------------------------+--------------------------+
| example              | EXPW(NNUM)               | EXPW(NUM)                |
| input                | sep\_1999                | sep\_1999                |
| output               | 1999                     | sep                      |
+----------------------+--------------------------+--------------------------+


IF(value,valueT,valueF) - replace T/F value
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

default: IF(,,)

Compares the value with the first parameter. In case the result is
TRUE, the input value is replaced with the second parameter,
otherwise the input value is replaced with the third parameter.

In case the input value has to be kept, whatever it is, the
keyword ORIG can be used (usually in the place of the third parameter)

::
         
        example
        input
        output
        IF(sep\_1999,sep)
        sep\_1999
        sep
        IF(oct\_1999,oct)
        sep\_1999
        IF(oct\_1999,oct,ORIG)
        sep\_1999
        oct\_1999


UP - upper case
^^^^^^^^^^^^^^^

Convert all characters to upper case


DOWN - lower case
^^^^^^^^^^^^^^^^^

Convert all characters to lower case


CAP - make capitals
^^^^^^^^^^^^^^^^^^^

Convert the initial character of each word to upper case and the
rest of characters to lower case


SHAPE - format string
^^^^^^^^^^^^^^^^^^^^^

Supresses all invalid spaces


NUM - number
^^^^^^^^^^^^

If it contains at least one digit, convert it into a number by
suppressing other characters. Leading zeroes are deleted.


SPLIT(n,h,str,from)
^^^^^^^^^^^^^^^^^^^

Splits the input value into more lines, where each line contains at
most (n+h+length of str) characters, (n) being the number of
characters following the number of characters in the header,
specified in (h). The header repeats at the beginning of each line.
An additional string can be inserted as a separator between the
header and the following value. This string is specified by the
third parameter (str). It is possible to restrict the application of
(str) so it does not appear on the first line by entering "2" for
(from)


SPLITW(sep,h,str,from)
^^^^^^^^^^^^^^^^^^^^^^

Splits the input value into more lines by replacing the line
separator stated in (sep) with CR/LFs. Also, as in the case of the
SPLIT function, the first (h) characters are taken as a header and
repeat at the beginning of each line.  An additional string can be
inserted as a separator between the header and the following value.
This string is specified by the third parameter (str). It is
possible to restrict the application of (str) so it does not appear
on the first line by entering "2" for (from)


CONF(field,value,1/0)  - confirm validity of a field
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The input value is taken as it is, or refused depending on the value
of some other field. In case the other (field) contains  the string
specified in (value), then the input value is confirmed (1) or
refused (0).


CONFL(str,1\|0) - confirm validity of a field
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The input value is confirmed if it contains (**1**)/misses(\ **0**)
the specified string (**str**)


RANGE(from,to) - confirm only entries in the specified range
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Left side function of target template configuration section to
select the desired entries from the repetitive field.
The range can only be continuous.

The entry is confirmed in case its input falls into the range
from-to specified in the parameter, border values included. As an
upper limit it is possibe to use the keyword MAX.

This is useful in case of AU code, where the first entry has a
different definition from other entries::

    AU::RANGE(1,1)---CER <:SYSNO:> AU2    L <:AU::SURNAME:>,
    <:AU::NAME:>    ... takes the first name from the defined AU field
    AU::RANGE(2,MAX)---CER <:SYSNO:> AU     L <:AU::SURNAME:> ,
    <:AU::NAME:>    ... takes the the rest of namesfrom the AU field


DEFP() - default print
^^^^^^^^^^^^^^^^^^^^^^

The value is printed by default even if it does not contain any variable
input from the source file.


IFDEFP(field,value,1/0) - IF condition is met, default print
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The line is printed by default (even if it does not contain any
variable input from the source file) IF a condition is met that
depends on the value of some other field. The condition is basically
either that "field" contains "value" (in which case the 3rd
parameter should be set to 1), or that "field" does NOT contain
"value" (in which case the 3rd parameter should be set to 0).
For example, given the following line::

    690C::REP(EOL,)::IFDEFP(comboYEL,BOOK,1)---<datafield tag="690"
    ind1="C" ind2=" "><subfield code="a">BOOK</subfield></datafield>

We want to print the line if the (field) "comboYEL" contains the
(value) "BOOK", otherwise we don't want to print it. Therefore, the
3rd parameter is set to "1". However, in the following line::

    690C::REP(EOL,)::IFDEFP(comboYEL,BOOK,0)---<datafield tag="690"
    ind1="C" ind2=" "><subfield code="a">OTHER</subfield></datafield>

We want to print the line if the (field) "comboYEL" does NOT
contain the (value) "BOOK", otherwise we don't want to print it.
Therefore, the 3rd parameter is set to "0".

This is achieved by using "IFDEFP". If the line had contained
variables, the "CONF" function would have been used instead.

JOINMULTILINES(prefix,suffix) - Join a multiline string into a single line with each segment having prefix and suffix
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given a field-value with newlines in it, split the field on the new
lines (\\n), separating them with prefix, then suffix. E.g. for the
field XX with the value::

       Test
       Case, A

And the function call::

       <:XX^::XX::JOINMULTILINES(<subfield code="a">,</subfield>):>

The results would be::

      <subfield code="a">Test</subfield><subfield code="a">Case, A</subfield>

One note on this: ``<:XX^::XX:``
Without the ^ the newlines will be lost as bibconvert will remove
them, so you'll never see an effect from this function.

3.4.2 Generated values
^^^^^^^^^^^^^^^^^^^^^^

In the template configurations, values can be either taken from the
source or generated in the process itself. This is mainly useful for
evaluating constant values.

Currently, the following date values are generated:
     
DATE(format,n)
^^^^^^^^^^^^^^

default: DATE(,10)

where n is the number of digits required.

Generates the current date in the form given as a parameter. The
format has to be given according to the ANSI C notation, i.e. the
string is composed out of following components::

    %a    abbreviated weekday name
    %A    full weekday name
    %b    abbreviated month name
    %B    full month name
    %c    date and time representation
    %d    decimal day of month number (01-31)
    %H    hour (00-23)(12 hour format)
    %I    hour (01-12)(12 hour format)
    %j    day of year(001-366)
    %m    month (01-12)
    %M    minute (00-59)
    %p    local equivalent of a.m. or p.m.
    %S    second (00-59)
    %U    week number in year (00-53)(starting with Sunday)
    %V    week number in year
    %w    weekday (0-6)(starting with Sunday)
    %W    week number in year (00-53)(starting with Monday)
    %x    local date representation
    %X    local time representation
    %y    year (no century prefix)
    %Y    year (with century prefix)
    %Z    time zone name
    %%    %


WEEK(diff)
^^^^^^^^^^

Enters the two-digit number of the current week (%V) increased by
specified difference.
If the resulting number is negative, the returned value is zero (00).
Values are kept up to 99, three digit values are shortened from the
left.

::

    WEEK(-4)    returns 48, if current week is 52
    WEEK        current week
     

SYSNO
^^^^^

Works the same as DATE, however the format of the resulting value
is fixed so it complies with the requirements of further record
handling. The format is 'whhmmss', where::

    w     current weekday
    hh    current hour
    mm    current minute
    ss    current second

The system number, if generated like this, contains a variable value
changing every second. For the system number is an identifier of the
record, it is needed to ensure it will be unique for the entire
record processed. Unlike the function DATE, which simply generates
the value of format given, SYSNO keeps the value persistent
throughout the entire record and excludes collision with other
records that are generated in period of one week with one second
granularity.

It is not possible to use the DATE function for generating a system
number instead.

The system number is unique in range of one week only, according
to the current definition.


OAI
^^^

Inserts OAI identifier incremented by one for earch record Starting
value that is used in the first record in the batch job can be
specified on the command line using the -o<starting\_value> option.
