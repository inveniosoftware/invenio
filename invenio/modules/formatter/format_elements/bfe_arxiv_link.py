# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
"""BibFormat element - Links to arXiv"""

from cgi import escape
from invenio.base.i18n import gettext_set_language

def format_element(bfo, tag="037__", target="_blank"):
    """
    Extracts the arXiv preprint information and
    presents it as a direct link towards arXiv.org
    """
    _ = gettext_set_language(bfo.lang)
    potential_arxiv_ids = bfo.fields(tag)
    arxiv_id = ""
    for potential_arxiv_id in potential_arxiv_ids:
        if potential_arxiv_id.get('9') == 'arXiv' and potential_arxiv_id.get('a', '').startswith('arXiv:'):
            arxiv_id = potential_arxiv_id['a'][len('arXiv:'):]
            return '<a href="http://arxiv.org/abs/%s" target="%s" alt="%s">%s</a>' % (
                escape(arxiv_id, True),
                escape(target, True),
                escape(_("This article on arXiv.org"), True),
                escape(arxiv_id))
    return ""

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0


