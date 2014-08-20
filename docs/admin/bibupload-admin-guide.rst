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

.. _bibupload-admin-guide:

BibUpload Admin Guide
=====================


1. Overview
-----------

BibUpload enables you to upload bibliographic data in MARCXML format
into Invenio bibliographic database. It is also used internally by other
Invenio modules as the sole entrance of metadata into the bibliographic
databases.

Note that before uploading a MARCXML file, you may want to run provided
``/opt/invenio/bin/xmlmarclint`` on it in order to verify its
correctness.

2. Configuring BibUpload
------------------------

BibUpload takes a MARCXML file as its input. There is nothing to be
configured for these files. If the files have to be coverted into
MARCXML from some other format, structured or not, this is usually done
beforehand via the `BibConvert <bibconvert-admin>`__ module.

Note that if you are using external system numbers for your records,
such as when your records are being synchronized from an external
system, then BibUpload knows about the 970 tag as the one containing
external system number. (To change this 970 tag into something else, you
would have to edit BibUpload config source file.)

Note that BibUpload also similarly knows about OAI identifiers,
so it will refuse to insert the same OAI-harvested record twice,
for example.

3. Running BibUpload
--------------------

3.1 Inserting new records
~~~~~~~~~~~~~~~~~~~~~~~~~

Consider that you have an MARCXML file containing new records that is to
be uploaded into the Invenio. (For example, it might have been produced
by `BibConvert <bibconvert-admin>`__.) To finish the upload, you would
call the BibUpload script in the insert mode as follows:

::

    $ bibupload -i file.xml



    In the insert mode, all the records from the file will be treated as
    new.  This means that they should not contain neither 001 tags
    (holding record IDs) nor 970 tags (holding external system numbers).
    BibUpload would refuse to upload records having these tags, in order
    to prevent potential double uploading.  If your file does contain 001
    or 970, then chances are that you want to update existing records, not
    re-upload them as new, and so BibUpload will warn you about this and
    will refuse to continue.


    For example, to insert a new record, your file should look like this:


        <record>
            <datafield tag="100" ind1=" " ind2=" ">
                <subfield code="a">Doe, John</subfield>
            </datafield>
            <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">On The Foo And Bar</subfield>
            </datafield>
        </record>

3.2 Inserting records into the Holding Pen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A special mode of BibUpload that is tigthly connected with BibEdit
is the *Holding Pen* mode.

When you insert a record using the holding pen mode such as in the
following example:

    ::

        $ bibupload -o file.xml

the records are not actually integrated into the database, but are
instead put into an intermediate space called holding pen, where
authorized curators can review them, manipulate them and eventually
approve them.

The holding pen is integrated with
`BibEdit </help/admin/bibedit-admin-guide>`__.

3.3 Updating existing records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you want to update existing records, with the new content from
your input MARCXML file, then your input file should contain either
tags 001 (holding record IDs) or tag 970 (holding external system
numbers). BibUpload will try to match existing records via 001 and
970 and if it finds a record in the database that corresponds to a
record from the file, it will update its content. Otherwise it will
signal an error saying that it could not find the
record-to-be-updated.

For example, to update a title of record #123 via correct mode, your
input file should contain record ID in the 001 tag and the title in
245 tag as follows:

::

        <record>
            <controlfield tag="001">123</controlfield>
            <datafield tag="245" ind1=" " ind2=" ">
                <subfield code="a">My Newly Updated Title</subfield>
            </datafield>
        </record>

There are several updating modes:

::


        -r, --replace Replace existing records by those from the XML
                      MARC file.  The original content is wiped out
                      and fully replaced.  Signals error if record
                      is not found via matching record IDs or system
                      numbers.
                      Fields defined in Invenio config variable
                      CFG_BIBUPLOAD_STRONG_TAGS are not replaced.

                      Note also that `-r' can be combined with `-i'
                      into an `-ir' option that would automatically
                      either insert records as new if they are not
                      found in the system, or correct existing
                      records if they are found to exist.

        -a, --append  Append fields from XML MARC file at the end of
                      existing records.  The original content is
                      enriched only.  Signals error if record is not
                      found via matching record IDs or system
                      numbers.

        -c, --correct Correct fields of existing records by those
                      from XML MARC file.  The original record
                      content is modified only on those fields from
                      the XML MARC file where both the tags and the
                      indicators match: the original fields are
                      removed and replaced by those from the XML
                      MARC file.  Fields not present in XML MARC
                      file are not changed (unlike the -r option).
                      Fields with "provenance" subfields defined in
                      'CFG_BIBUPLOAD_CONTROLLED_PROVENANCE_TAGS'
                      are protected against deletion unless the
                      input MARCXML contains a matching
                      provenance value.
                      Signals error if record is not found via
                      matching record IDs or system numbers.

        -d, --delete  Delete fields of existing records that are
                      contained in the XML MARC file. The fields in
                      the original record that are not present in
                      the XML MARC file are preserved.
                      This is incompatible with FFT (see below).

Note that if you are using the ``--replace`` mode, and you specify
in the incoming MARCXML a 001 tag with a value representing a record
ID that does not exist, bibupload will not create the record
on-the-fly unless the ``--force`` parameter was also passed on the
command line. This is done in order to avoid accidentally creating
gaps in the database list of record identifiers. In fact, when you ask
to ``--replace`` a non-existing record imposing a record ID
with a value of, say, ``1 000 000`` and, subsequently, you
``--insert`` a new record, this will automatically receive an ID
with the value ``1 000 001``.

If you combine the ``--pretend`` parameter with the above updating
mode, you can actually test what would be executed without modifying
the database or altering the system status.

3.4 Inserting and updating at the same time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that the insert/update modes can be combined together. For
example, if you have a file that contains a mixture of new records
with possibly some records to be updated, then you can run:

::

    $ bibupload -i -r file.xml



    In this case BibUpload will try to do an update (for records having
    either 001 or 970 identifiers), or an insert (for the other ones).


    3.6 Uploading fulltext files

    The fulltext files can be uploaded and revised via a special FFT
    ("fulltext file transfer") tag with the following
    semantic:


        FFT $a  ...  location of the docfile to upload (a filesystem path or a URL)
            $d  ...  docfile description (optional)
            $f  ...  format (optional; if not set, deduced from $a)
            $m  ...  new desired docfile name (optional; used for renaming files)
            $n  ...  docfile name (optional; if not set, deduced from $a)
            $o  ...  flag (repeatable subfield)
            $r  ...  restriction (optional, see below)
            $s  ...  set timestamp (optional, see below)
            $t  ...  docfile type (e.g. Main, Additional)
            $v  ...  version (used only with REVERT and DELETE-FILE, see below)
            $x  ...  url/path for an icon (optional)
            $z  ...  comment (optional)
            $w  ... MoreInfo modification of the document
            $p  ... MoreInfo modification of a current version of the document
            $b  ... MoreInfo modification of a current version and format of the document
            $u  ... MoreInfo modification of a format (of any version) of the document

For example, to upload a new fulltext file ``thesis.pdf``
associated to record ID 123:

::

        <record>
            <controlfield tag="001">123</controlfield>
            <datafield tag="FFT" ind1=" " ind2=" ">
                <subfield code="a">/tmp/thesis.pdf</subfield>
                <subfield code="t">Main</subfield>
                <subfield code="d">
                  This is the fulltext version of my thesis in the PDF format.
                  Chapter 5 still needs some revision.
                </subfield>
            </datafield>
        </record>

The FFT tag can be repetitive, so one can pass along another FFT
tag instance containing a pointer to e.g. the thesis defence
slides. The subfields of an FFT tag are non-repetitive.

When more than one FFT tag is specified for the same document
(e.g. for adding more than one format at a time), if $t (docfile
type), $m (new desired docfile name), $r (restriction), $v
(version), $x (url/path for an icon), are specified, they should
be identically specified for each single entry of FFT. E.g. if
you want to specify an icon for a document with two formats (say
.pdf and .doc), you'll write two FFT tags, both containing the
same $x subfield.

The bibupload process, when it encounters FFT tags, will
automatically populate the fulltext storage space
(``/opt/invenio/var/data/files``) and metadata record associated
tables (``bibrec_bibdoc``, ``bibdoc``) as appropriate. It will
also enrich the 856 tags (URL tags) of the MARC metadata of the
record in question with references to the latest versions of
each file.

Note that for the $a and $x subfields, the filesystem paths must be
absolute (e.g. ``/tmp/icon.gif`` is valid, while
``Destkop/icon.gif`` is not) and they must be readable by the
user/group of the bibupload process that will handle the FFT.

The bibupload process supports the usual modes correct, append,
replace, insert with a semantic that is somewhat similar to the
semantic of the metadata upload:

    Metadata
    Fulltext
    objects being uploaded
    MARC field instances characterized by tags (010-999)
    fulltext files characterized by unique file names (FFT $n)
    insert
    insert new record; must not exist
    insert new files; must not exist
    append
    append new tag instances for the given tag XXX, regardless
    of existing tag instances
    append new files, if filename (i.e. new format) not already
    present
    correct
    correct tag instances for the given tag XXX; delete existing
    ones and replace with given ones
    correct files with the given filename; add new revision or
    delete file; if the docname does not exist the file is added
    replace
    replace all tags, whatever XXX are
    replace all files, whatever filenames are
    delete
    delete all existing tag instances
    not supported

Note that in append and insert mode

::

    $m

is ignored.

In order to rename a document just use the the correct mode
specifing in the $n subfield the original docname that should be
renamed and in $m the new name.

Special values can be assigned to the $t subfield.

Value

Meaning

``PURGE``

In order to purge previous file revisions (i.e. in order to keep
only the latest file version), please use the correct mode with
$n docname and $t PURGE as the special keyword.

``DELETE``

In order to delete all existing versions of a file, making it
effectively hidden, please use the correct mode with $n docname
and $t DELETE as the special keyword.

EXPUNGE

In order to expunge (i.e. remove completely, also from the
filesystem) all existing versions of a file, making it
effectively disappear, please use the correct mode with $n
docname and $t EXPUNGE as the special keyword.

``FIX-MARC``

In order to synchronize MARC to the bibrec/bibdoc structure
(e.g. after an update or a tweak in the database), please use
the correct mode with $n docname and $t FIX-MARC as the special
keyword.

``FIX-ALL``

In order to fix a record (i.e. put all its linked documents in a
coherent state) and synchronize the MARC to the table, please
use the correct mode with $n docname and $t FIX-ALL as the
special keyword.

``REVERT``

In order to revert to a previous file revision (i.e. to create a
new revision with the same content as some previous revision
had), please use the correct mode with $n docname, $t REVERT as
the special keyword and $v the number corresponding to the
desired version.

``DELETE-FILE``

In order to delete a particular file added by mistake, please
use the correct mode with $n docname, $t DELETE-FILE, specifing
$v version and $f format. Note that this operation is not
reversible. Note that if you don't spcify a version, the last
version will be used.

In order to preserve previous comments and descriptions when
correcting, please use the KEEP-OLD-VALUE special keyword with
the desired $d and $z subfield.

The $r subfield can contain a string that can be used to restrict
the given document. The same value must be specified for all the
format of a given document. By default the keyword will be used
as the status parameter for the "viewrestrdoc" action, which can
be used to give access right/restriction to desired user. e.g.
if you set the keyword "thesis", you can the connect the
"thesisviewer" to the action "viewrestrdoc" with parameter
"status" set to "thesis". Then all the user which are linked
with the "thesisviewer" role will be able to download the
document. Instead any other user *which are not considered as
authors* for the given record will not be allowed. Note, if you
use the keyword "KEEP-OLD-VALUE" the previous restrictions if
applicable will be kept.

More advanced document-level restriction is indeed possible. If
the value contains in fact:

-  ``email: john.doe@example.org``: then only the user having
   ``john.doe@example.org`` as email address will be authorized
   to access the given document.
-  ``group: example``: then only users belonging to the
   local/external group ``example`` will be authorized to access
   the given document.
-  ``role: example``: then only the users belonging to the
   WebAccess role ``example`` will be authorized to access the
   given document.
-  ``firerole: allow .../deny...``: then only the users
   implicitly matched by the given `firewall like role
   definition </help/admin/webaccess-admin-guide#6>`__ will be
   authorized to access the given document.
-  ``status: example``: then only the users belonging to roles
   having an authorization for the WebAccess action
   ``viewrestrdoc`` with parameter ``status`` set to ``example``
   will be authorized (that is exactly like setting $r to
   ``example``).

Note, that authors (as defined in the record MARC) and
superadmin are always authorized to access a document, no matter
what is the given value of the status.

Some special flags might be set via FFT and associated with the
current document by using the $o subfield. This feature is
experimental. Currently only two flags are actively considered:

-  **HIDDEN**: used to specify that the file that is currently
   added (via revision or append) must be hidden, i.e. must not
   be visible to the world but only known by the system (e.g. to
   allow for fulltext indexing). This flag is permanently
   associated with the specific revision and format of the file
   being added.
-  **PERFORM\_HIDE\_PREVIOUS**: used to specify that, although
   the current file should be visible (unless the HIDDEN flag is
   also specified), any other previous revision of the document
   should receive the HIDDEN flag, and should thus be hidden to
   the world.

Note that each time bibupload is called on a record, the 8564
tags pointing to locally stored files are recreated on the basis
of the full-text files connected to the record. Thus, if you
whish to update some 8564 tag pointing to a locally managed
file, the only way to perform this is through the FFT tag, not
by editing 8564 directly.

The subfield $s of FFT can be used to set time stamp of the
uploaded file to a given value, e.g. 2007-05-04 03:02:01. This
is useful when uploading old files. When $s is not present, the
current time will be used.

3.7 Obtaining feedbacks
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, to implement a particular workflow or policy in a
digital repository, it might be nice to receive an automatic
machine-friendly feedback that acknowledges the outcome of a
bibupload execution. To this aim the ``--callback-url`` command
line parameter can be used. This parameter expects a *URL* to be
specified to which a **`JSON <http://json.org/>`__-serialized**
response will **POSTed**.

Say, you have an external service reachable via the URL
``http://www.example.org/accept_feedback``. If the argument:

::

    --callback-url http://www.example.org/accept_feedback

is added to the usual bibupload call, at the end of the
execution of the corresponding bibupload task, an HTTP POST
request will be performed, if possible to the given URL,
reporting the outcome of the bibupload execution as a
JSON-serialized response with the following structure:

-  a JSON **object** with the following *string* -- *value*
   mapping:

   -  string: **results** -- value: a JSON **array** whose
      values are all JSON **objects** with the following
      *string* -- *value* mapping:

      -  **recid**: an integer number, representing the
         described record identifier (``-1`` if no record
         identifier can be retrieved)
      -  **success**: either ``true`` or ``false`` depending on
         the success of the elaboration of the corresponding
         MARCXML
      -  **error\_message**: a **string** containing a
         human-friendly description of the error that caused the
         MARCXML elaboration to fail (in case ``success`` was
         having ``false`` value)
      -  **marcxml**: in case of success, this contains the
         final MARCXML representation of the record
      -  **url**: in case of success, this contains the final
         URL where the detailde representation of the record can
         be fetched (i.e. its canonical URL)

For example, a possible JSON response posted to a specified URL
can look like:

::

    {
        "results": [
            {
                "recid": -1,
                "error_message": "ERROR: can not retrieve the record identifier",
                "success": false
            },
            {
                "recid": 1000,
                "error_message": "",
                "success": true,
                "marcxml": "1000...",
                "url": "http://www.example.org/record/1000"
            },
            ...
        ]
    }

Note that, currently, in case the specified URL can not be
reached at the time of the POST request, the whole bibupload
task will fail.

If you use the same callback URL to receive the feedback from
more than one bibupload request you might want to be able to
correctly identify each bibupload call with the corresponding
feedback. For this reason you can pass to the bibupload call an
additional argument:

::

    --nonce VALUE

where value can be any string you wish. Such string will be then
added to the JSON structure, as in (supposing you specified
``--nonce 1234``):

::

    {
        "nonce": "1234",
        "results": [
            {
                "recid": -1,
                "error_message": "ERROR: can not retrieve the record identifier",
                "success": false
            },
            {
                "recid": 1000,
                "error_message": "",
                "success": true,
                "marcxml": "1000...",
                "url": "http://www.example.org/record/1000"
            },
            ...
        ]
    }

3.8 Assigning additional information to documents and other entities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some bits of meta-data should not be viewed by Invenio users
directly and stored in the MARC format. This includes all types
of non-standard data related to records and documents, for
example flags realted to documents (sepcified inside a FFT
tag) or bits of semantic information related to entities
managed in Invenio. This type of data is usually machine
generated and should be used by modules of Invenio internally.

Invenio provides a general mechanism allowing to store objects
related to different entities of Invenio. This mechanism is
called MoreInfo and resembles well-known more-info solutions.
Every entity (document, version of a document, format of a
particular version of a document, relation between documents)
can be assigned a dictionary of arbitrary values. The dictionary
is divided into namespaces, which allow to separate data from
different modules and serving different purposes.

BibUpload, the only gateway to uploading data into the Invenio
database, allows to populate MoreInfo structures. MoreInfo
related to a given entity can be modified by providing a
Pickle-serialised byte64 encoded Python object having following
structure:

::

    {
        "namespace": {
            "key": "value",
            "key2": "value2"
        }
    }

For example the above dictionary should be uploaded as

::

    KGRwMQpTJ25hbWVzcGFjZScKcDIKKGRwMwpTJ2tleTInCnA0ClMndmFsdWUyJwpwNQpzUydrZXknCnA2ClMndmFsdWUnCnA3CnNzLg==

Which is a base-64 encoded representation of the string

::

    (dp0\nS'namespace'\np1\n(dp2\nS'key2'\np3\nS'value2'\np4\nsS'key'\np5\nS'value'\np6\nss.

Removing of data keys from a dictionary can happen by providing
None value as a value. Empty namespaces are considered
non-existent.

The string representation of modifications to the MoreInfo
dictionary can be provided in several places, depending, to
which object it should be attached. The most general upload
method, the BDM tag has following semantic:

::

        BDM $r  ... Identifier of a relation between documents (optional)
            $i  ... Identifier of a BibDoc (optional)
            $v  ... Version of a BibDoc (optional)
            $n  ... Name of a BibDoc (within a current record) (optional)
            $f  ... Format of a BibDoc (optional)
            $m  ... Serialised update to the MoreInfo dictionary

All (except $m) subfields are optional and allow to identify an
entity to which MoreInfo should refer.

Besides the BDM tag, MoreInfo can be transfered using special
subfields of FFT and BDR tags. The first one allows to modify
MoreInfo of a newly uploaded document, the second of a relation.
The additional subfields have following semantic:

::

        FFT $w  ... MoreInfo modification of the document
            $p  ... MoreInfo modification of a current version of the document
            $s  ... MoreInfo modification of a current version and format of the document
            $u  ... MoreInfo modification of a format (of any version) of the document
        BDR $m  ... MoreInfo modification of a relation between BibDocs

3.8.1 Uploading relations between documents
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

One of additional pieces of non-MARC data which can be uploaded
to Invenio are relations between documents. Similarly to
MoreInfos, relations are intended to be used by Invenio modules.
The semantics of BDR field allowing to upload relations looks as
follows

::

        BDR $r  ... Identifier of the relation (optional, can be provided if modifying a known relation)

            $i  ... Identifier of the first document
            $n  ... Name of the first document (within the current record) (optional)
            $v  ... Version of the first document (optional)
            $f  ... Format of the first document (optional)

            $j  ... Identifier of the second document
            $o  ... Name of the second document (within the current record) (optional)
            $w  ... Version of the second document (optional)
            $g  ... Format of the second document (optional)

            $t  ... Type of the relation
            $m  ... Modification of the MoreInfo of the relation
            $d  ... Special field. if value=DELETE, relation is removed

Behaviour of the BDR tag in different upload modes:

+--------------------------------------+--------------------------------------+
| insert, append                       | correct, replace                     |
| Inserts new relation if necessary.   | Creates new relation if necessary,   |
| Appends fields to the MoreInfo       | replaces the entire content of       |
| structure                            | MoreInfo field.                      |
+--------------------------------------+--------------------------------------+

3.8.2 Using temporary identifiers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In many cases, users want to upload large collections of
documents using a single BibUpload task. The infrastructure
described in the rest of this manual allows easy upload of
multiple documents, but lacks facilities for relating them to
each other. A sample use-case which can not be satisfied by
simple usage of FFT tags is uploading a document and relating it
to another which is either already in the database or is being
uploaded within the same BibUpload task. BibUpload provides a
mechanism of temporary identifiers which allows to serve
scenarios similar to the aforementioned.

A temporary identifier is a string (unique in the context of a
single MARC XML document), which replaces the document number or a
version number. In the context of BibDoc manipulations (FFT, BDR
and BDM tags), temporary identifiers can appear everywhere where
version or numerical id are required. If a temporary identifier
appears in a context of document already having an ID assigned,
it will be interpreted as this already existent number. If a newly
created document is assigned a temporary identifier, the newly
generated numerical ID is assigned to the temporary id. In order
to be recognised as a temporary identifier, a string has to
begin with the **TMP:** prefix. The mechanism of temporary
identifiers can not be used in the context of records, only
with BibDocs.

A BibUpload input using temporary identifiers can look like this:

::


    <collection xmlns="http://www.loc.gov/MARC21/slim">
      <record>
        <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">This is a record of the publication</subfield>
        </datafield>
        <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://somedomain.com/document.pdf</subfield>
          <subfield code="t">Main</subfield>
          <subfield code="n">docname</subfield>
          <subfield code="i">TMP:id_identifier1</subfield>
          <subfield code="v">TMP:ver_identifier1</subfield>
        </datafield>
      </record>

      <record>
        <datafield tag="100" ind1=" " ind2=" ">
          <subfield code="a">This is a record of a dataset extracted from the publication</subfield>
        </datafield>

        <datafield tag="FFT" ind1=" " ind2=" ">
          <subfield code="a">http://sample.com/dataset.data</subfield>
          <subfield code="t">Main</subfield>
          <subfield code="n">docname2</subfielxd>
          <subfield code="i">TMP:id_identifier2</subfield>
          <subfield code="v">TMP:ver_identifier2</subfield>
        </datafield>

        <datafield tag="BDR" ind1=" " ind2=" ">
          <subfield code="i">TMP:id_identifier1</subfield>
          <subfield code="v">TMP:ver_identifier1</subfield>
          <subfield code="j">TMP:id_identifier2</subfield>
          <subfield code="w">TMP:ver_identifier2</subfield>

          <subfield code="t">is_extracted_from</subfield>
        </datafield>
      </record>

    </collection>

4. Batch Uploader
-----------------

4.1 Web interface - Cataloguers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The batchuploader web interface can be used either to upload
metadata files or documents. Opposed to daemon mode, actions
will be executed only once.

The available upload history displays metadata and document
uploads using the web interface, not daemon mode.

4.2 Web interface - Robots
~~~~~~~~~~~~~~~~~~~~~~~~~~

If it is needed to use the batch upload function from within
command line, this can be achieved with a curl call, like:

::

    $ curl -F 'file=@localfile.xml' -F 'mode=-i' http://cds.cern.ch/batchuploader/robotupload [-F 'callback_url=http://...'] -A invenio_webupload



    This service provides (client, file) checking to assure the records are put into a collection the client has rights to.
    To configure this permissions, check CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS variable in the configuration file.
    The allowed user agents can also be defined using the CFG_BATCHUPLOADER_WEB_ROBOT_AGENT variable.
    Note that you can receive machine-friendly feedbacks from the corresponding
    bibupload task that is launched by a given batchuploader request, by adding
    the optional POST field callback_url with the same semantic of the --callback-url
    command line parameter of bibupload (see the previous paragraph Obtaining feedbacks).

    A second more RESTful interface is also available: it will suffice to append to the URL the specific mode (among "insert",
    "append", "correct", "delete", "replace"), as in:

    http://cds.cern.ch/batchuploader/robotupload/insert

The *callback\_url* argument can be put in query part of the
URL as in:

::

    http://cds.cern.ch/batchuploader/robotupload/insert?callback_url=http://myhandler

In case the HTTP server that is going to receive the
feedback at *callback\_url* expect the request to be encoded
in *application/x-www-form-urlencoded* rather than
*application/json* (e.g. if the server is implemented
directly in Oracle), you can further specify the
special\_treatment argument and set it to *oracle*. The
feedback will then be further encoded into an
*application/x-www-form-urlencoded* request, with a single
form key called *results*, which will contain the final JSON
data.

The MARCXML content should then be specified as the body of
the request. With *curl* this can be implemented as in:

::

    $ curl -T localfile.xml http://cds.cern.ch/batchuploader/robotupload/insert?callback_url=http://... -A invenio_webupload -H "Content-Type: application/marcxml+xml"

The *nonce* argument that can be passed to BibUpload as
described in the previous paragraph can also be specified
with both robotupload interfaces. E.g.:

::

    $ curl -F 'file=@localfile.xml' -F 'nonce=1234' -F 'mode=-i' http://cds.cern.ch/batchuploader/robotupload -F 'callback_url=http://...' -A invenio_webupload

and

::

    $ curl -T localfile.xml http://cds.cern.ch/batchuploader/robotupload/insert?nonce=1234&callback_url=http://... -A invenio_webupload -H "Content-Type: application/marcxml+xml"

4.2 Daemon mode
~~~~~~~~~~~~~~~

The batchuploader daemon mode is intended to be a bibsched
task for document or metadata upload. The parent directory
where the daemon will look for folders ``metadata`` and
``documents`` must be specified in the Invenio configuration
file.

An example of how directories should be arranged,
considering that Invenio was installed in folder
``/opt/invenio`` would be:

::

         /opt/invenio/var/batchupload
                /opt/invenio/var/batchupload/documents
                        /opt/invenio/var/batchupload/documents/append
                        /opt/invenio/var/batchupload/documents/revise
                /opt/invenio/var/batchupload/metadata
                        /opt/invenio/var/batchupload/metadata/append
                        /opt/invenio/var/batchupload/metadata/correct
                        /opt/invenio/var/batchupload/metadata/insert
                        /opt/invenio/var/batchupload/metadata/replace

When running the batchuploader daemon there are two possible
execution modes:

::

            -m,   --metadata    Look for metadata files in folders insert, append, correct and replace.
                                All files are uploaded and then moved to the corresponding DONE folder.
            -d,   --documents   Look for documents in folders append and revise. Uploaded files are then
                                moved to DONE folders if possible.

By default, the metadata mode is used.

An example invocation would be:

    ::

        $ batchuploader --documents



        It is possible to program the batch uploader to run periodically. Read the Howto-run guide to see how.

