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

<link rel="stylesheet" href="/css/video_platform_record.css" type="text/css" />
<link rel="stylesheet" href="/vendors/mediaelement/build/mediaelementplayer.css" type="text/css" />
<script type="text/javascript" src="/vendors/mediaelement/build/mediaelement-and-player.js"></script>
<script type="text/javascript" src="/js/video_platform_record.js"></script>

<!-- VIDEO PLAYER -->
<div class="row video_black_band">
    <div class="col-md-12 video_player">
        {{ bfe_video_platform_sources(bfo, ) }}
        <video id="mediaelement" controls preload>
    </div>
</div>
<!-- CONTENT -->
<div class="row video_content_wrapper">
    <!-- LEFT COLUMN -->
    <div class="col-md-8 video_content_left">
        <!-- VIDEO CONTENT -->
        <div class="video_content_box">
            <div class="video_content_year">
                {{ bfe_field(bfo, tag="909C0Y") }}
            </div>
            <div class="video_content_title">
                {{ bfe_title(bfo, prefix="", suffix="", default="", escape="", highlight="no", separator=" ") }}
            </div>
            <div class="video_content_author">
                {{ _("by") }} {{ bfe_authors(bfo, prefix="", suffix="", default="", escape="", affiliation_suffix=")", extension="[...]", link_author_pages="no", limit="", print_links="yes", separator=" ; ", print_affiliations="no", highlight="no", interactive="no", affiliation_prefix=" (") }} {{ bfe_copyright(bfo, ) }}
            </div>
            <div class="video_content_description">
                {{ bfe_abstract(bfo, ) }}
            </div>
            <div class="video_content_clear"></div>
        </div>
        <!-- DOWNLOAD BUTTON -->
        <div class="btn btn-default pull-right">
            <i class="glyphicon glyphicon-download-alt"></i> {{ _("Download Video") }}
        </div>
        <!-- VIDEO COMMENTS -->
        <a href="{{ url_for("comments.add", recid=recid) }}" class="btn btn-primary">
            <i class="glyphicon glyphicon-pencil"></i> {{ _("Write a comment") }}
        </a>

        <div class="clearfix"></div>
        <br/>
    </div>
    <!-- RIGHT COLUMN -->
    <div class="col-md-4 video_content_right">
        {{ bfe_video_platform_suggestions(bfo, ) }}
    </div>
    <div class="video_content_clear"></div>
</div>

<div class="video_content_clear"></div>

<!-- Elements that are only evaluated by JavaScript -->
{{ bfe_video_platform_downloads(bfo, ) }}

{# WebTags #}
{{ tfn_webtag_record_tags(record['recid'], current_user.get_id())|prefix('<hr />') }}

{{ tfn_get_back_to_search_links(record['recid'])|wrap(prefix='<div class="pull-right linksbox">', suffix='</div>') }}
