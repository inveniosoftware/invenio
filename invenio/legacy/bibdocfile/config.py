# This file is part of Invenio.
# Copyright (C) 2012 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from __future__ import unicode_literals

import re

try:
    from invenio.config import CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_MISC
except ImportError:
    CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_MISC = {
        'can_revise_doctypes': ['*'],
        'can_comment_doctypes': ['*'],
        'can_describe_doctypes': ['*'],
        'can_delete_doctypes': ['*'],
        'can_keep_doctypes': ['*'],
        'can_rename_doctypes': ['*'],
        'can_add_format_to_doctypes': ['*'],
        'can_restrict_doctypes': ['*']}

try:
    from invenio.config import CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_DOCTYPES
except ImportError:
    CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_DOCTYPES = [
        ('Main', 'Main document'),
        ('LaTeX', 'LaTeX'),
        ('Source', 'Source'),
        ('Additional', 'Additional File'),
        ('Audio', 'Audio file'),
        ('Video', 'Video file'),
        ('Script', 'Script'),
        ('Data', 'Data'),
        ('Figure', 'Figure'),
        ('Schema', 'Schema'),
        ('Graph', 'Graph'),
        ('Image', 'Image'),
        ('Drawing', 'Drawing'),
        ('Slides', 'Slides')]

try:
    from invenio.config import CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_RESTRICTIONS
except ImportError:
    CFG_BIBDOCFILE_DOCUMENT_FILE_MANAGER_RESTRICTIONS = [
        ('', 'Public'),
        ('restricted', 'Restricted')]

# CFG_BIBDOCFILE_ICON_SUBFORMAT_RE -- a subformat is an Invenio concept to give
# file formats more semantic. For example "foo.gif;icon" has ".gif;icon"
# 'format', ".gif" 'superformat' and "icon" 'subformat'. That means that this
# particular format/instance of the "foo" document, not only is a ".gif" but
# is in the shape of an "icon", i.e. most probably it will be low-resolution.
# This configuration variable let the administrator to decide which implicit
# convention will be used to know which formats will be meant to be used
# as an icon.
CFG_BIBDOCFILE_ICON_SUBFORMAT_RE = re.compile(r"icon.*")

# CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT -- this is the default subformat used
# when creating new icons.
CFG_BIBDOCFILE_DEFAULT_ICON_SUBFORMAT = "icon"
