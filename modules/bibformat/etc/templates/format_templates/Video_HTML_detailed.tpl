
	<link rel="stylesheet" href="/img/video_platform_record.css" type="text/css" />
	<link rel="stylesheet" href="/mediaelement/mediaelementplayer.css" type="text/css" />
	<script type="text/javascript" src="/js/jquery.min.js"></script>
	<script type="text/javascript" src="/mediaelement/mediaelement-and-player.js"></script>
	<script type="text/javascript" src="/js/video_platform_record.js"></script>

		<!-- VIDEO PLAYER -->
		<div class="video_black_band">
			<div class="video_player">
				{{ bfe_video_platform_sources(bfo, ) }}
				<video id="mediaelement" controls preload>
			</div>
		</div>
		<!-- CONTENT -->
		<div class="video_content_wrapper">
			<!-- LEFT COLUMN -->
			<div class="video_content_left">
				<!-- VIDEO CONTENT -->
				<div class="video_content_box">
					<div class="video_content_year">
						{{ bfe_field(bfo, tag="909C0Y") }}
					</div>
					<div class="video_content_title">
						{{ bfe_title(bfo, prefix="", suffix="", default="", escape="", highlight="no", separator=" ") }}
					</div>
					<div class="video_content_author">
						by {{ bfe_authors(bfo, prefix="", suffix="", default="", escape="", affiliation_suffix=")", extension="[...]", link_author_pages="no", limit="", print_links="yes", separator=" ; ", print_affiliations="no", highlight="no", interactive="no", affiliation_prefix=" (") }} {{ bfe_copyright(bfo, ) }}
					</div>
					<div class="video_content_description">
						{{ bfe_abstract(bfo, ) }}
					</div>
					<div class="video_content_clear"></div>
				</div>
				<!-- DOWNLOAD BUTTON -->
				<div id="video_download_button">
					Download Video
				</div>
				<!-- VIDEO COMMENTS -->
				{{ bfe_comments(bfo, show_reviews="False") }}
			</div>
			<!-- RIGHT COLUMN -->
			<div class="video_content_right">
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
