/*
 * This file is part of Invenio.
 * Copyright (C) 2014 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

'use strict';

define(
  [
    'jquery',
    'flight/lib/component',
    'prism'
  ],
  function(
    $,
    defineComponent,
    Prism) {

    return defineComponent(DetailsPreview);

    /**
    * .. js:class:: DetailsPreview()
    *
    * Handles the calls to the server for getting and displaying formatted data
    * chosen by the user via the preview menu and uses Prism to syntax
    * highlighting when required.
    *
    * :param string preview_url: URL for getting the formatted content.
    * :param string id_object: ID of the BibWorkflowObject being displayed.
    *
    */
    function DetailsPreview() {
      this.attributes({
        // URL
        preview_url: "",

        // BibWorkflowObject id
        id_object: "",
      });

      this.renderPreviewByFormat = function (ev, data) {
        var $this = this;
        var container_selector = 'div[id="object_preview_container' + $this.attr.id_object + '"]';
        $.ajax({
            url: $this.attr.preview_url,
            data: {'objectid': $this.attr.id_object,
                   'of': data.format},
            success: function (json) {
                if (data.format === "xm" || data.format === "xo") {
                    if (json.data === "") {
                        json.data = "Preview not available";
                    }
                    $(container_selector).empty();
                    $(container_selector).append(
                      "<pre><code id='object_preview' class='language-markup'></code></pre>"
                    );
                    $('code[id="object_preview"]').text(json.data);
                    Prism.highlightElement($('code[id="object_preview"]')[0]);
                } else {
                    if (json.data === "") {
                        json.data = "Preview not available";
                    }
                    $(container_selector).empty();
                    $(container_selector).append(json.data);
                }
            }
        });
      };

      this.after('initialize', function() {
        this.on(document, "setPreviewByFormat", this.renderPreviewByFormat)
        console.log("Details init");
      });
    }
  }
);
