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

.. _bibcirculation-admin-guide:

BibCirculation Admin Guide
==========================

1. Overview
-----------

BibCirculation enables you to manage the circulation of books (and other
items) in a traditional library. BibCirculation has 2 sides: the user
(borrower) interface and the admin (librarian) interface. In order to
being able to use the librarian interface you need to have the
correspondent rights as Invenio user.

If you have rights to run BibCirculation, click on the "Administration"
tab and select "Run Bibcirculation". You will see the so called "main
menu", that will be present almost in every page in the librarian
interface.

2. Items
--------

The first you need to circulate books are books. "Item" refers to
anything that can have a barcode. In the case of books, an item is a
copy of a book. The first thing you need is adding copies to the system.
If you already have digitalized data about your copies, it is
recommended to write a script to add the copies to the database.
Otherwise, you need to add them one by one. To do this, search the book
record in Invenio, go to the 'Detailed record' view, then the 'Holdings'
tab. If you have BibCirculation rights, you will see a link. This link
will let you add the first copy for that record (in case it has none) or
it will take you to the record details in the librarian interface (in
case it already has copies) where you can find a "Add new copy" button.

You can get to the "Item details" page clicking in the book title link
that can be found in many places around the module. You can also get to
this page by searching a record using the "Items" in the main menu. In
the "Item details" page the actions and the information diplayed will be
different fot Periodicals and other records.

FIXME
