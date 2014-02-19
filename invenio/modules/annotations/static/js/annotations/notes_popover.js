/**
This file is part of Invenio.
Copyright (C) 2013 CERN.

Invenio is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

Invenio is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with Invenio; if not, write to the Free Software Foundation, Inc.,
59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
**/

'use strict';

/* global PDF_NOTES_HELPER */
/* exported NOTES_POPOVER */

/**
 * Utilities for displaying a popover in the add comments textarea showing how
 * to add notes.
 *
 * @module
 * @param {jQuery} $ usually window's jQuery object.
 */
var NOTES_POPOVER = (function($) {

    /**
     * Attaches a popover to the #comment-textarea element; the content should
     * be specified in #comment-textarea.attr(popover_content)
     */
    function bindPopover() {
        var content = $('#comment-textarea').attr('popover_content');
        if(content && content.length > 0) {
            $('#comment-textarea').popover({
                title: 'Title',
                content: content,
                trigger: 'focus',
                html: true,
                container: 'body'
            });
        }
    }

    $(document).on('shown.bs.modal', function() {
        bindPopover();
        $('#comment-textarea').popover('show');
        if(typeof PDF_NOTES_HELPER !== 'undefined') {
            var noteMarker = PDF_NOTES_HELPER.getTextAreaFill() || '';
            var replyContent = $('#comment-textarea').val() || '';
            if (replyContent && noteMarker) {
                replyContent = replyContent + '\n';
            }
            $('#comment-textarea').val(replyContent + noteMarker);
            PDF_NOTES_HELPER.setTextAreaFill(null);
        }
    });

    $(document).ready(function() {
        // add popover in the comments.add stand-alone page
        bindPopover();
    });
})(window.jQuery);
