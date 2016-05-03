# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""BibFormat element.

* Creates a list of record recommendations
"""

import re

from invenio.config import CFG_RECOMMENDER_REDIS
from invenio.messages import gettext_set_language


html_script = """
<script>
$( document ).ready(function() {
    $.getJSON("%(recommendations_url)s" , function( data ) {
        var root = $( "<div/>", {class: 'recommendations',
                                 style: 'display:none;'})
        var records = data.items;
        var items = [];
        if (records.length === 0 ) {
            return;
        }

        var header = $( "<div/>", {class: 'recommendation_header'})
                    .appendTo(root);
        $( "<h3/>", {class: 'recommendations_contents',
            text: "%(text_title)s:" }).appendTo(header);
        var list = $( "<ul/>", {
            "class": "record_recommendation",
        });


        $.each( records, function( key, val ) {
            var title = "";
            var titleSplit = val.record_title.split(" ");
            if (titleSplit.length >= 10){
                title = titleSplit.slice(0, 10).join(" ") + " [...]";
            }else{
                title = val.record_title;
            }

            var authors = "";
            var authorsSplit = val.record_authors.split(";");
            if (authorsSplit.length > 3){
                var countAuthors = authorsSplit.length - 3;
                authors = authorsSplit.slice(0, 3).join(" ;")
                            + " + " + countAuthors + ' more';
            }else{
                authors = val.record_authors;
            }

            if (authors.length >= 2){
                authors = " - by " + authors;
            }

            $("<li/>", { class: 'record_recommendation',
                         id: val.number,
                         text: authors})
                    .appendTo(list)
                    .prepend($( "<a/>", { href: val.record_url,
                                          text: title })
            );

        });
        $(list).appendTo(root);
        root.appendTo($("div.pagebodystripemiddle"));
        $(root).fadeIn("Slow");
    });

});
</script>
"""


def format_element(bfo):
    """Create the HTML and JS code to display the recommended records."""
    if CFG_RECOMMENDER_REDIS == "":
        return ""
    try:
        re.search(r'/record/', bfo.user_info.get('uri')).group()
    except AttributeError:
        # No record url found
        return ""

    _ = gettext_set_language(bfo.lang)

    url = "/record/" + str(bfo.recID) + "/recommendations"
    html = html_script % {'recommendations_url': url,
                          'text_title': _("You might also be interested in"),
                          }
    return html


def escape_values(bfo):
    """Called by BibFormat to check if output should be escaped."""
    return 0
