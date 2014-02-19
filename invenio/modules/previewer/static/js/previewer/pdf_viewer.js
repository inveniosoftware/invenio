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

/* global _ */
/* exported PDF_VIEWER */

/**
 * PDF viewer presentation logic.
 *
 * @param {[jQuery} $ usually window's jQuery object.
 */
var PDF_VIEWER = (function($) {

    /**
     * Currently displayed page.
     *
     * @type Number
     */
    var CURRENT_PAGE = 1;

    /**
     * PDF's number of pages.
     *
     * @type Number
     */
    var MAX_PAGE = 1;

    /**
     * Displays image for currently previewed page.
     *
     * @param  {String} base 64 encoded PNG image data.
     */
    function displayImage(data) {
        if(data.responseText !== '404') {
            $('#pdf-preview').html('<img class="img-responsive" src="data:image/png;base64,' +
                                   data +
                                   '" />');
        }
    }

    /**
     * Displays the current page and total number of pages in the UI.
     */
    function displayPageCount() {
        if(MAX_PAGE > 0) {
            $('#page-counter').html([_('Page'), CURRENT_PAGE,
                _('of'), MAX_PAGE].join(' '));
        }
    }

    /**
     * Callbacks for page change.
     *
     * @type Array callback functions.
     */
    var PAGE_CHANGE_ACTIONS = [displayImage, displayPageCount];

    /**
     * Adds a new callback for the page change event.
     *
     * @param  {Function} func the callback to add.
     */
    function bindPageChangeAction(func) {
        PAGE_CHANGE_ACTIONS = PAGE_CHANGE_ACTIONS.concat(func);
    }

    /**
     * Bootstrapping actions.
     *
     * @param  {String} path the current page path; in a AJAX tab context, this
     *                  function should work only in the comments tab.
     */
    function init(path) {
        getMaxPage(getHash, true);

        if(path === undefined || path.indexOf('comments') !== -1 ) {
            $('#frst-page').on('click', function() {
                setCurrentPage(1);
            });

            $('#prev-page').on('click', function() {
                setCurrentPage(CURRENT_PAGE-1);
            });

            $('#next-page').on('click', function() {
                setCurrentPage(CURRENT_PAGE+1);
            });

            $('#last-page').on('click', function() {
                setCurrentPage(MAX_PAGE);
            });
        }
    }

    /**
     * Parses the window.location.hash; if an integer is found, the currently
     * previewed page is set to that value.
     *
     * @param {Boolean} [force] if true, a page for preview will be requested
     *                          regardless of the validity of the hash.
     */
    function getHash(force) {
        var hash = parseInt(window.location.hash.substring(1));
        if (hash) {
            setCurrentPage(hash);
        } else if(force) {
            setCurrentPage(CURRENT_PAGE);
        }
    }

    $(document).ready(function() {
        init();
    });

    $(window).on('tabreloaded', function(event, path) {
        init(path);
    });

    $(window).on('hashchange', getHash);

    /**
     * Returns the number of the currently previewed page.
     *
     * @return {Number} the page number.
     */
    function getCurrentPage() {
        return CURRENT_PAGE;
    }


    /**
     * Sets the currently previewd page; it checks the new value against the
     * document bounds, rewrites the URL hash and requests the preview via AJAX.
     *
     * @param {Number} page the page to be set
     */
    function setCurrentPage(page) {
        if (page >= 1 && page <= MAX_PAGE) {
            CURRENT_PAGE = page;
        }
        window.location.hash = CURRENT_PAGE;
        requestPage();  // FIXME: don't request if page not changed
    }

    /**
     * Performs an AJAX request for the preview of the current page.
     */
    function requestPage() {
        $.ajax({
            url: 'preview',
            data: {page: CURRENT_PAGE},
            success: PAGE_CHANGE_ACTIONS,
            error: PAGE_CHANGE_ACTIONS
        });
    }

    /**
     * Performs an AJAX request for the total number of pages of the previewd
     * PDF.
     *
     * @param  {Function} cb
     */
    function getMaxPage(cb) {
        $.ajax({
            url: 'preview/pdfmaxpage',
            success: [function(data) { MAX_PAGE = data.maxpage; }].concat(cb)
        });
    }

    return {
        getCurrentPage: getCurrentPage,
        MAX_PAGE: MAX_PAGE,
        bindPageChangeAction: bindPageChangeAction
    };
})(window.jQuery);
