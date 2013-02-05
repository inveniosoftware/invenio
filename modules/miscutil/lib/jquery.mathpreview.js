/*
 * This file is part of Invenio.
 * Copyright (C) 2012 CERN.
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

/*
 * Add a preview panel for "LaTeX" formulas under selected fields.
 *
 * Requires MathJax to be installed and enabled on pages where this
 * plugin used. Requires jQuery. Necessary CSS styles are located in
 * Invenio main CSS file.
 *
 * Usage examples:
 *
 *  - Add preview panel to all text input fields on the page:
 *   $('input[type="text"]').mathpreview({})
 *
 *  - Add preview panel to all textareas on the page, and configure:
 *   $('textarea').mathpreview({'refresh-delay': 10,
 *                              'position': 'bottom',
 *                              'help-label': "You can use LaTeX markup in this field"})
 *
 *  TODO (optional, to be thought):
 *  - Register for each field if preview panel has been closed, and
 *    don't display it anymore.
 *  - Remove 'css-url' option?
*/

(function( $ ){

    var preview_timeout;
    var preview_hide_timeout;
    var css_added = false;

    var methods = {
	init : function( options ) {
	    /* Main function to be called */

	    var settings = $.extend({}, {
		'css-url'         : '',
		'refresh-delay'   : 100, // milliseconds,
		'help-url': "",
		'help-label': "Use '$' delimiters to write LaTeX markup",
		'hide-empty-tip-after': 3000, //milliseconds.
		'show-preview-only-if-math': true,
		'position': 'bottom' // 'bottom', 'left', 'top', 'right'
	    }, options);

	    var help_url = "";
	    if (settings['help-url'] != "") {
		help_url = ' [<a href="' + settings['help-url']  + '" target="_blank">?</a>]'
	    }

	    var preview_panel_markup_html = '<div id="mathpreviewarea"> \
<div id="mathpreviewareabar"><span>' + settings['help-label']  + help_url  + '</span><a id="mathpreviewareaclose" onclick="return false;" href="#" title="Close">X</a><div style="clear:both"></div></div> \
<div id="mathpreviewareacontent"></div> \
</div>'

	    // Key down event
	    this.keydown(function(event) {
		clearTimeout(preview_timeout);
		var current_input = $(this);
		if (settings['show-preview-only-if-math'] == false | current_input.val().indexOf("$") != -1) {
		    preview_timeout = setTimeout(function() {
			// Display preview only after some delay
			display_preview(current_input, settings['show-preview-only-if-math'], settings['position']);
		    }, settings['refresh-delay']);
		}
	    });

	    // Input focus loss
	    this.blur(function() {
		hide_preview($(this));
	    })
	    // Input focus
	    this.focus(function() {
		clearTimeout(preview_hide_timeout);
		clearTimeout(preview_timeout);
		//if ($(this).val().indexOf("$") != -1) {
		    /* Display immediately if LaTex might be there */
		    display_preview($(this), settings['show-preview-only-if-math'], settings['position']);
		//}
		/* Hide tooltip after some time if no tex exist */
		if (settings['hide-empty-tip-after'] > 0) {
		    var current_input = $(this);
		    preview_hide_timeout = setTimeout(function() {
			if (current_input.val().indexOf("$") == -1) {
			    hide_preview(current_input);
			}
		    }, settings['hide-empty-tip-after']);
		}
	    })
	    // Add necessary CSS file, if wanted
	    if (!css_added & settings['css-url'] != "") {
		$("head").append('<link href="' + settings['css-url'] + '" type="text/css" rel="stylesheet" />');
	    }

	    // Add preview panel HTML markup
	    if (!$("#mathpreviewarea").length) {
		$("body").append(preview_panel_markup_html);
	    }

	    return this;
	}
    };


    $.fn.mathpreview = function(method) {
	// Method calling logic
	if ( methods[method] ) {
	    return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
	} else if ( typeof method === 'object' || ! method ) {
	    return methods.init.apply( this, arguments );
	} else {
	    $.error( 'Method ' +  method + ' does not exist on jQuery.tooltip' );
	}
    };

    function hide_preview(current_input) {
	/* Hide preview panel */
	var fieldDiv = $('#mathpreviewarea');
	fieldDiv.fadeOut('medium');
    }

    function display_preview(input_field, preview_only_if_math, position) {
	/* Show preview panel */
	// Get input field position
	var input_field_offset = input_field.offset();
	var input_field_top    = input_field_offset.top;
	var input_field_left   = input_field_offset.left;
	// Get input field size
	var input_field_height = input_field.height();
	var input_field_width  = input_field.width();

	// Minimum preview area content  width
	var preview_area_content_field_width = input_field_width;
	if (preview_area_content_field_width < 300){
	    preview_area_content_field_width = 300;
	}
	var fieldDiv = $('#mathpreviewarea');
	var fieldPreviewDiv = $('#mathpreviewareacontent');

	// Update preview panel position/size and visibility
	fieldDiv.css("position","absolute");

	fieldPreviewDiv.css("width", preview_area_content_field_width);
	fieldDiv.stop(true, true);
	fieldDiv.fadeIn('medium');

	if (input_field.val() != '' & (preview_only_if_math == false | input_field.val().indexOf("$") != -1)) {
	    //Mirror input value in preview window (only if wanted)
	    $('#mathpreviewareacontent').html(input_field.val());
	    // Refresh LaTeX with MathJax
	    MathJax.Hub.Queue(["Typeset", MathJax.Hub, 'mathpreviewareacontent']);
	    fieldPreviewDiv.css("display", "block");
	} else {
	    fieldPreviewDiv.css("display", "none");
	}

	if (position == 'bottom') {
	    fieldDiv.css("left", input_field_left);
	    fieldDiv.css("top", input_field_top + input_field_height + 6);
	} else if (position == 'top') {
	    fieldDiv.css("left", input_field_left);
	    fieldDiv.css("top", input_field_top - fieldDiv.height() - 6);
	} else if (position == 'right') {
	    fieldDiv.css("left", input_field_left + input_field_width + 6);
	    fieldDiv.css("top", input_field_top);
	} else if (position == 'left') {
	    fieldDiv.css("left", input_field_left - fieldDiv.width() - 6);
	    fieldDiv.css("top", input_field_top);
	}
    }

})( jQuery );