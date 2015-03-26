# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2014, 2015 CERN.
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

"""BibFormat element - wrap the Add This service: <http://www.addthis.com/>."""

try:
    from invenio.config import CFG_BIBFORMAT_ADDTHIS_ID
except ImportError:
    CFG_BIBFORMAT_ADDTHIS_ID = None

from invenio.legacy.search_engine import get_all_restricted_recids


def format_element(bfo, only_public_records=1,
                   addthis_id=CFG_BIBFORMAT_ADDTHIS_ID):
    """Print the AddThis box from the <http://www.addthis.com/> service.

    :param only_public_records: if set to 1 (the default), prints the box only
        if the record is public (i.e. if it belongs to the root colletion and
        is accessible to the world).
    :param addthis_id: the pubid API parameter as provided by the service
        (e.g. ra-4ff80aae118f4dad). This can be set at the repository level
        in the variable CFG_BIBFORMAT_ADDTHIS_ID in invenio(-local).conf
    """
    if not addthis_id:
        return ""
    if int(only_public_records) and \
            bfo.recID not in get_all_restricted_recids():
        return ""
    return """\
<!-- AddThis Button BEGIN -->
<div class="addthis_toolbox addthis_default_style ">
<a class="addthis_button_preferred_1"></a>
<a class="addthis_button_preferred_2"></a>
<a class="addthis_button_preferred_3"></a>
<a class="addthis_button_preferred_4"></a>
<a class="addthis_button_compact"></a>
<a class="addthis_counter addthis_bubble_style"></a>
</div>
<script type="text/javascript">var addthis_config = {"data_track_clickback":true};</script>
<script type="text/javascript" src="http://s7.addthis.com/js/250/addthis_widget.js#pubid=%(addthis_id)s"></script>
<!-- AddThis Button END -->
""" % {'addthis_id': addthis_id}


def escape_values(bfo):
    """Check if output of this element should be escaped."""
    return 0
