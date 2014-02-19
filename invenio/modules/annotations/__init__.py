# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""

    invenio.modules.annotations
    ---------------------------

    To enable the module, make sure to remove it from ``PACKAGES_EXCLUDE``,
    where it is placed by default.

    To enable Web page annotations, add the following to your templates:

    .. code-block:: html

        {%- from "annotations/macros.html" import annotations_toolbar, annotations_js, annotations_css -%}

        {%- block global_css -%}
          {{ super() }}
          {{ annotations_css() }}
        {%- endblock global_css -%}

        {%- block global_javascript -%}
          {{ super() }}
          {{ annotations_js() }}
        {%- endblock global_javascript -%}

        {%- block page_body -%}
          {{ annotations_toolbar() }}
          {{ super() }}
        {%- endblock page_body -%}

    To enable document annotations, along with the previewer, set the following
    configuration variables to ``True``:

    .. code-block:: python

        ANNOTATIONS_NOTES_ENABLED = True
        ANNOTATIONS_PREVIEW_ENABLED = True
"""
