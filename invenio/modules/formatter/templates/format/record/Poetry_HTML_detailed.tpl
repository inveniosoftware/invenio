{#
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
#}

{{ bfe_topbanner(bfo, prefix='<div style="padding-left:10px;padding-right:10px">', suffix='</div><hr/>') }}

<div style="padding-left:10px;padding-right:10px">
{{ bfe_title(bfo, separator="<br /><br />") }}
<p align="center">
{{ bfe_authors(bfo, suffix="<br />", limit="25", interactive="yes", print_affiliations="yes", affiliation_prefix="<small> (", affiliation_suffix=")</small>") }}
{{ bfe_addresses(bfo) }}
{{ bfe_affiliation(bfo) }}
{{ bfe_date(bfo, prefix="<br />", suffix="<br />") }}
{{ bfe_publisher(bfo, prefix="<small>", suffix="</small>") }}
{{ bfe_place(bfo, prefix="<small>", suffix="</small>") }}
{{ bfe_isbn(bfo, prefix="<br />ISBN: ") }}
</p>

<p style="margin-left: 15%; width: 70%">

{{ bfe_abstract(bfo) }}

{{ bfe_keywords(bfo, prefix="<br /><small><strong>Keyword(s): </strong></small>", keyword_prefix="<small>", keyword_suffix="</small>") }}

{{ bfe_notes(bfo, note_prefix="<br /><small><strong>Note: </strong>", note_suffix=" </small>", suffix="<br />") }}

{{ bfe_publi_info(bfo, prefix="<br /><br /><strong>Published in: </strong>") }}
<br />

</div>

{{ bfe_addthis(bfo, ) }}

{{ bfe_appears_in_collections(bfo, prefix="<p style='margin-left: 10px;'><em>The record appears in these collections:</em><br />", suffix="</p>") }}

{# WebTags #}
{{ tfn_webtag_record_tags(record['recid'], current_user.get_id())|prefix('<hr />') }}

{{ tfn_get_back_to_search_links(record['recid'])|wrap(prefix='<div class="pull-right linksbox">', suffix='</div>') }}
