.. This file is part of Invenio
   Copyright (C) 2015 CERN.

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

Module naming conventions
=========================

Invenio modules are standalone independent components that implement some
functionality used by the rest of the Invenio ecosystem. The modules provide API
to other modules and use API of other modules.

A module is usually called:

1. with plural noun, meaning "database (of things)", for example
   ``invenio-records``, ``invenio-tags``, ``invenio-annotations``,

2. with singular noun, meaning "worker (using things)", for example
   ``invenio-checker``, ``invenio-editor``.

A module may have split its user interface and REST API interface, for example
``invenio-records-ui`` and ``invenio-records-rest``, to clarify dependencies and
offer easy customisation.
