<div style="padding-left:10px;padding-right:10px">
{{ bfe_topbanner(bfo, ) }}
</div>
<hr />
<div style="padding-left:10px;padding-right:10px">
{{ bfe_title(bfo, prefix="<center><big><big><strong>", separator="<br/><br/>", suffix="</strong></big></big></center>") }}

{{ bfe_notes(bfo, ) }}
{{ bfe_date(bfo, prefix="<center>", suffix="</center>") }}
{{ bfe_contact(bfo, ) }}
<center>
{{ bfe_authors(bfo, prefix="Photographer:<small> ", suffix="</small>", print_links="yes", print_affiliations="yes", limit="10", interactive="yes") }}

{{ bfe_addresses(bfo, prefix="<small>", suffix="</small>", print_link="yes") }}
</center>
<br/>

{{ bfe_keywords(bfo, prefix="<small><strong>Keyword(s): </strong>", suffix="</small>") }}

<table> <tr>
<td valign="top" align="left">
{{ bfe_field(bfo, tag="909CP$s", prefix="<br/> <strong>Original ref.</strong>: ", suffix=" ") }}
{{ bfe_field(bfo, tag="909CP$t", prefix="<br/><strong>Available pictures</strong>: ", suffix="  ") }}

{{ bfe_abstract(bfo, prefix_en='<p><span class="blocknote">
 Caption</span><br /> <small>', suffix_en='</small></p>', prefix_fr='<p><span class="blocknote">
 Légende</span><br /><small>', suffix_fr='</small></p>') }}

{{ bfe_external_publications(bfo, prefix='<p><span class="blocknote">See also:</span><br /><small>', suffix="</small></p>") }}

</td>

<td valign="top">
{{ bfe_photos(bfo, style="border:1px solid #bbb;padding:3px;margin:1px;", prefix='<span class="blocknote">Resources</span><br />') }}
</td>

</tr>

<tr><td colspan="2">
 <strong>© CERN Geneva: </strong>
<small>The use of photos requires prior authorization (from <a href="http://cern.ch/cern-copyright/">CERN copyright</a>).
The words CERN Photo must be quoted for each use. </small>
</td>
</tr>
</table>
</div>

{# WebTags #}
{{ tfn_webtag_record_tags(record['recid'], current_user.get_id())|prefix('<hr />') }}

{{ tfn_get_back_to_search_links(record['recid'])|wrap(prefix='<div class="pull-right linksbox">', suffix='</div>') }}
