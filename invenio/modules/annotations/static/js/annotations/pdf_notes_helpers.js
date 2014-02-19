/**
This file is part of Invenio.
Copyright (C) 2013, 2014 CERN.

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

/* global PDF_VIEWER */
/* global _ */
/* global bindModals */
/* global COMMENTS_COLLAPSE */

/* exported PDF_NOTES_HELPER */

/**
 * Utilities for combining the PDF preview and Notes features.
 *
 * @module
 * @param {jQuery} $ usually window's jQuery object.
 */
var PDF_NOTES_HELPER = (function($) {

    /**
     * Retrives the notes from the server via an AJAX request.
     *
     * @param  {*} callerData unused, AJAX callback source.
     * @param  {*} ajaxStatus unused, AJAX callback source.
     * @param  {*} ajaxObject unused, AJAX callback source.
     * @param  {Boolean} all true if all the notes should be retrieved, false if
     *                   only those on the currently previewed page.
     */
    function getNotes(callerData, ajaxStatus, ajaxObject, all) {
        if(all === undefined && ALL_TOGGLED) {
            // AJAX callback on page change while `all-notes-toggle` is toggled
            return;
        }
        var page = all ? -1 : PDF_VIEWER.getCurrentPage();
        $.ajax({
            url: 'notes',
            data: { page: page },
            success: function(data) {
                $('#notes-wrapper').html(data);
                bindModals('[data-filter="annoreply"]');
                COMMENTS_COLLAPSE.bindCollapse();
            }
        });
    }

    /**
     * true if all the notes are currently displayed, false if only those on
     * currently previewd page.
     *
     * @type Boolean
     */
    var ALL_TOGGLED = false;

    /**
     * Text that should fill the add comment textarea when modal opens (usually
     * the current page note marker).
     *
     * @type String
     */
    var TEXTAREA_FILL;

    /**
     * Uses the currently previewed page number to construct an note marker that
     * will fill the add comment textarea.
     */
    function fillCommentsTextArea() {
        TEXTAREA_FILL = 'P.' + PDF_VIEWER.getCurrentPage() + ': ';
    }

    /**
     * Changes the view notes button text, depending on what is previewed
     * currently (all notes/ notes on page).
     */
    function changeAllNotesButtonText() {
        if(!ALL_TOGGLED) {
            $('#all-notes-toggle').
                html('<i class="glyphicon glyphicon-eye-open"></i> ' +
                     _('Show all annotations'));
        } else {
            $('#all-notes-toggle').
                html('<i class="glyphicon glyphicon-eye-open"></i> ' +
                     _('Show page annotations'));
        }
    }

    /**
     * Returns the text that should fill the add comment textarea.
     *
     * @return {String}
     */
    function getTextAreaFill() {
        return TEXTAREA_FILL;
    }

    /**
     * Sets the text that should fill the add comment textarea.
     *
     * @param {String} fill
     */
    function setTextAreaFill(fill) {
        TEXTAREA_FILL = fill;
    }

    /**
     * Bootstrapping actions.
     */
    function init() {
        // get notes on previewed page change
        PDF_VIEWER.bindPageChangeAction(getNotes);

        // when clicking the on PDF viewer. a new comment with the current page
        // note marker should be initialized
        $('#pdf-preview').on('click', fillCommentsTextArea);

        $('#all-notes-toggle').on('click', function() {
            // this event is called before the button has the 'active' class set
            ALL_TOGGLED = !ALL_TOGGLED;
            getNotes(undefined, undefined, undefined, ALL_TOGGLED);
            changeAllNotesButtonText();
        });
    }

    $(document).ready(function() {
        init();
    });

    $(window).on('tabreloaded', function() {
        init();
    });

    /**
     * Injects currently previewed PDF page number into the form for
     * after-submit redirection.
     */
    function injectPage() {
        try {
            $('#pdf_page').val(PDF_VIEWER.getCurrentPage());
        } catch(e) {
            // FIXME: check if we can inject and remove try ... catch
            return;
        }
    }

    return {
        getTextAreaFill: getTextAreaFill,
        setTextAreaFill: setTextAreaFill,
        injectPage: injectPage,
        fillCommentsTextArea: fillCommentsTextArea
    };
})(window.jQuery);
