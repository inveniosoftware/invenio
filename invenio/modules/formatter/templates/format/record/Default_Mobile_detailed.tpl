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

<div class="content">
<div class="displayInfo">
{{ bfe_topbanner(bfo, prefix='<div>', suffix='</div><hr/>') }}

<div>
{{ bfe_title(bfo, prefix="<div class='recordTitle'>", separator="<br /><br />", suffix="</div>") }}
<p align="center">
{{ bfe_authors(bfo, suffix="<br />", limit="5", link_mobile_pages="yes", print_affiliations="yes", affiliation_prefix="<small> (", affiliation_suffix=")</small>") }}
{{ bfe_addresses(bfo, ) }}
{{ bfe_affiliation(bfo, ) }}
{{ bfe_date(bfo, prefix="<br />", suffix="<br />") }}
{{ bfe_publisher(bfo, prefix="<small>", suffix="</small>") }}
{{ bfe_place(bfo, prefix="<small>", suffix="</small>") }}
{{ bfe_isbn(bfo, prefix="<br />ISBN: ") }}
</p>


{{ bfe_abstract(bfo, prefix_en="<small><strong>Abstract: </strong>", prefix_fr="<small><strong>R&eacute;sum&eacute;</strong>", suffix_en="</small><br />", suffix_fr="</small><br />") }}

{{ bfe_keywords(bfo, prefix="<br /><small><strong>Keyword(s): </strong></small>", keyword_prefix="<small>", keyword_suffix="</small>") }}

{{ bfe_notes(bfo, note_prefix="<br /><small><strong>Note: </strong>", note_suffix=" </small>", suffix="<br />") }}

{{ bfe_publi_info(bfo, prefix="<br /><br /><strong>Published in: </strong>") }}<br />
{{ bfe_doi(bfo, prefix="<small><strong>DOI: </strong>", suffix=" </small><br />") }}

</div>
</div>
<div class="infos">
<div class="listFile">
{{ bfe_fulltext(bfo, prefix='', style="note", suffix="", focus_on_main_file="yes") }}
</div>
<div class="media">
{{ bfe_field(bfo, tag="8564_", instances_separator="<br>", subfields_separator=" - ", limit="30") }}
</div>
<div class="extern">
{{ bfe_field(bfo, tag="8567_", instances_separator="<br>", subfields_separator=" - ", limit="30") }}
</div>
<div class="references">
{{ bfe_report_numbers(bfo, ) }}
</div>
</div>
</div>

{# WebTags #}
{{ tfn_webtag_record_tags(record['recid'], current_user.get_id())|prefix('<hr />') }}
