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

.. _bibedit-admin-guide:

BibEdit Admin Guide
===================

1. Overview
-----------

BibEdit enables you to directly manipulate bibliographic data, edit a
single record, do global replacements, and other cataloguing tasks.

2. Edit records via Web interface
---------------------------------

To edit records via the web interface, please go to `BibEdit
Editor </record/edit/>`__. This interface will let
you add, change or delete fields in a record.

If you want to change several records at once, you can use the batch
command-line techniques described below or the `Multi-Record
Editor <#3.1>`__.

Please note that 8564 tags pointing to fulltext files managed by Invenio
can't be manipulated via BibEdit. In order to modify them please use the
`FFT tags through BibUpload <bibupload-admin-guide#3.5>`__ or the
bibdocfile command line tool.

2.1 Keyboard shortcuts on BibEdit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basic record actions
^^^^^^^^^^^^^^^^^^^^

+----------------------+--------------------------+--------------------------+
| Shortcut             |                          |                          |
| Definition           |                          |                          |
| Action               |                          |                          |
+======================+==========================+==========================+
| g                    | Ctrl+Right               | Ctrl+Left                |
| Select               | Next                     | Previous                 |
| Go to the record     | Go to next record (in    | Go to previous record    |
| selection field      | search results).         | (in search results).     |
+----------------------+--------------------------+--------------------------+

Focused (clicked) subfield or field
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

+--------------------------+--------------------------+
| Shortcut                 |                          |
| Definition               |                          |
| Action                   |                          |
+==========================+==========================+
| Ctrl+Up                  | Ctrl+Down                |
| Move up                  | Move down                |
| Move focused subfield    | Move focused subfield    |
| up.                      | down.                    |
+--------------------------+--------------------------+

Input field/form
^^^^^^^^^^^^^^^^

+--------------------------+
| Shortcut                 |
| Definition               |
| Action                   |
+==========================+
| Esc                      |
| Cancel                   |
| Cancel edition of        |
| subfield                 |
+--------------------------+

Other functionality
^^^^^^^^^^^^^^^^^^^

+--------------------------+--------------------------+--------------------------+
| Shortcut                 |                          |                          |
| Definition               |                          |                          |
| Action                   |                          |                          |
+==========================+==========================+==========================+
| alt+s                    | Ctrl+Shift+z             | Ctrl+Shift+y             |
| Selection mode           | Undo                     | Redo                     |
| Toggle selection mode.   | Undo last action.        | Redo last action.        |
+--------------------------+--------------------------+--------------------------+



3. Edit multiple records via web interface
------------------------------------------

The purpose of the `Multi-Record Editor Web
interface </record/multiedit/>`__ is to allow
cataloguers to easily edit more than one record in one go.

The Multi-Record Editor allows cataloguers to easily look up various
records in the system in order to find record sets upon which to
operate, and then to allow some easy replacement procedures on these
records in one go, e.g. a substring substitution of some field value in
some field tags.

3.1 Multi-Record Editor user guide
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While working with the Multi-Record Editor, the first step is to filter
the set of records that are going to be modified.

In order to do that, three options are available in the interface:

::

    Search criteria:    [         ]
    Filter collection:  [         ]
    Output tags:        [         ]
    [Search]

-  Search criteria allows to search records using the same syntax
   offered by Invenio's web search.
-  These records can be filtered by the desired collection, thus
   narrowing the search results.
-  Finally, for convenience, the tags displayed for each record can be
   specified. The tags have to be separated by commas.

After clicking the ``Search`` button, the set of records that will be
affected by the changes will be visible at the bottom of the interface.
It is possible to specify whether to visualize them in ``MARC`` format
or in ``HTML Brief`` format.

The next step is to specify the desired changes to be made on the
records. When defining a new field action, the field tag and its
indicators (if necessary) have to be specified and one of the three
actions (Add field, Delete field, Update field) selected.

::

    Field
    [ tag ][ind1][ind2]     [Select action[V]]

After that, as many actions on subfields as needed can be defined. The
subfield tag has to be specified and one action
(``Add subfield, Delete subfield, Replace full content, Replace substring``)
selected. Depending on the field action selected some actions for
subfields will not be available.

The difference between ``Replace full content`` and
``Replace substring`` resides in that the former deletes all the content
present in a subfield and writes the specified value on it whereas the
latter looks for a string and substitutes it by a new string.

All subfield actions have the ``Apply only to specific field instances``
option. This is useful, for example, in cases where there are multiple
authors (``700__`` tags) and we do not want to act in all of them.

In that case one could add the condition that only fields where the tag
``$a`` is equal to ``Ellis A.`` should be modified.

::

    700__   Update Field
            [u] [Replace full content]
                [Ellis J.]
            when other subfield [u] is equal to [Ellis A.]

Every subfield action defined has to be saved using the correspondent
button before applying the changes.

Once all the actions for fields and subfields have been specified the
modifications can be previewed using the corresponding button.

Finally, when clicking on the ``Apply changes`` button all modifications
will be sent to the server and will be visible after some time.

4. Edit records via command line
--------------------------------

The idea is to download record in XML MARC format, edit it by using any
editor, and upload the changes back. Note that you can edit any number
of records at the same time: for example, you can download all records
written by ``Qllis, J``, open the file in your favourite text editor,
and change globally the author name to the proper form ``Ellis, J``.

You therefore continue as follows:

#. Download the record in XML MARC. For example, download record ID
   1234:

   ::

                $ wget -O z.xml 'http://your.site/record/1234?of=xm'


   or download latest 5,000 public documents written by ``Qllis, J``:

   ::

                $ wget -O z.xml 'http://your.site/search?p=Qllis%2C+J&f=author&of=xm&rg=5000'


   Note also that you can access history of records as covered in a
   `access record history <#6>`__ section below.

#. Edit the metadata as necessary:

   ::

                $ emacs z.xml


#. Upload changes back:

   ::

                $ bibupload -r z.xml


#. See the progress of the treatment of the file via BibSched:

   ::

                $ bibsched


   If you do not want to wait for the next wake-up time of indexing and
   formatting daemons, launch them manually now:

   ::

                $ bibindex
                $ bibreformat
                $ webcoll


   and watch the progress via ``bibsched``.

After which the record(s) should be fully modified and formatted and all
indexes and collections updated, as necessary.

5. Delete records via command line
----------------------------------

Once a record has been uploaded, we prefer not to \*destroy\* it fully
anymore (i.e. to wipe it out and to reuse its record ID for another
record) for a variety of reasons. For example, some users may have put
this record already into their baskets in the meantime, or the record
might have already been announced by alert emails to the external world,
or the OAI harvestors might have harvested it already, etc. We usually
prefer only to \*mark\* records as deleted, so that our record IDs are
ensured to stay permanent.

Thus said, the canonical way to delete the record #1234 in Invenio
v0.1.x development branch is to download its XML MARC:

::

           $ wget -O z.xml 'http://your.site/record/1234?of=xm'


and to mark it as deleted by adding the indicator \`\`DELETED'' into the
MARC 980 $$c tag:

::

           $ emacs z.xml
           [...]
            <datafield tag="980" ind1=" " ind2=" ">
              <subfield code="a">PREPRINT</subfield>
              <subfield code="c">DELETED</subfield>
            </datafield>
           [...]


and upload thusly modified record in the \`replace' mode:

::

           $ bibupload -r z.xml


and watch the progress via ``bibsched``, as mentioned in the `section
3 <#3>`__.

This procedure will remove the record from the collection cache so that
the record won't be findable anymore. In addition, if the users try to
access this record via direct URL such as distributed by the alert
engine (record/1234) or via their baskets, they will see a message
\`\`This record has been deleted''. Please note though that the original
MARCXML of the record stays kept in the database, for example you can
access it by:

::

       $ python -c "from zlib import decompress; \\
                    from invenio.legacy.dbquery import run_sql; \\
                    print decompress(run_sql('SELECT value FROM bibfmt \\
                    WHERE id_bibrec=1234 AND format=\'xm\'')[0][0])"

In some cases you may want to hide the record from the searches, but to
leave it accessible via direct URLs or via baskets. In this case the
best it to alter its collection tag (980) to some non-existent
collection, for example:

::

       $ wget -O z.xml 'http:://localhost/record/1234?of=xm'
       $ perl -pi -e 's,ARTICLE,HIDDENARTICLE,g' z.xml
       $ bibupload -r z.xml

This will make the record non-existent as far as the search engine is
concerned, because it won't belong to any existing collection, but the
record will exist \`\`on its own'' and the users knowing its recID will
be able to access it.

P.S. Note that the \`\`bibXXx'' tables will keep having entries for the
deleted records. These entries are to be cleaned from time to time by
the BibEdit garbage collector. This GC isn't part of Invenio yet;
moreover in the future we plan to abolish all the bibXXx tables, so that
this won't be necessary anymore.

6. Delete all records
---------------------

If you want to wipe out all the existing bibliographic content of your
site, for example to start uploading the documents from scratch again,
you can launch:

::

           $ /opt/invenio/bin/dbexec < /opt/invenio/src/invenio-0.90/modules/miscutil/sql/tabbibclean.sql
           $ rm -rf /opt/invenio/var/data/files/*
           $ /opt/invenio/bin/webcoll
           $ /opt/invenio/bin/bibindex --reindex


Note that you may also want to delete the fulltext files and the
submission counters in ``/opt/invenio/var/data`` subdirectories, if you
use WebSubmit.

7. Access record history
------------------------

Every revision of the metadata of a record is stored in the "history"
table containing all previous MARCXML master formats of the record. You
can access them via the ``bibedit`` command line utility.

To list previous revisions of record ID 1:

::

         $ /opt/invenio/bin/bibedit --list-revisions 1
         1.20080319193118
         1.20080318172536
         1.20080311020315


To get MARCXML of the revision 1.20080318172536 (record ID 1, revision
date 2008-03-18 17:25:36):

::

         $/opt/invenio/bin/bibedit --get-revision 1.20080318172536 | head -5
         <record>
           <controlfield tag="001">1</controlfield>
           <datafield tag="037" ind1=" " ind2=" ">
             <subfield code="a">CERN-EX-0106015</subfield>
           </datafield>
         [...]


To compare the differences between the two last revisions:

::

         $ /opt/invenio/bin/bibedit --diff-revisions 1.20080318172536 1.20080319193118
         --- 1.20080318172536
         +++ 1.20080319193118
         @@ -4,7 +4,7 @@
              <subfield code="a">CERN-EX-0106015</subfield>
            </datafield>
            <datafield tag="100" ind1=" " ind2=" ">
         -    <subfield code="a">Photolab</subfield>
         +    <subfield code="a">Photolab SOME TEST EDIT HERE</subfield>
            </datafield>
            <datafield tag="245" ind1=" " ind2=" ">
              <subfield code="a">ALEPH experiment: Candidate of Higgs boson production</subfield>
         @@ -26,7 +26,7 @@
            </datafield>
            <datafield tag="650" ind1="1" ind2="7">
              <subfield code="2">SzGeCERN</subfield>
         -    <subfield code="a">Experiments and Tracks</subfield>
         +    <subfield code="a">Experiments and Tracks SOME TEST EDIT THERE</subfield>
            </datafield>
            <datafield tag="653" ind1="1" ind2=" ">
              <subfield code="a">LEP</subfield>


