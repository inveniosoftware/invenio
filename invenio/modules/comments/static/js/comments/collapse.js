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

/* exported COMMENTS_COLLAPSE */

/**
 * Comment collapse utilities.
 *
 * @module
 * @param {jQuery} $ usually window's jQuery object.
 */
var COMMENTS_COLLAPSE = (function($) {

    function bindCollapse() {
        $('.collapse').on('shown.bs.collapse', function(e) {
            $('[data-target="#' + e.target.id + '"').children()
                .removeClass('glyphicon-chevron-right')
                .addClass('glyphicon-chevron-down');
            $.get($(this).attr('data-action'));
            e.stopPropagation();
        });

        $('.collapse').on('hidden.bs.collapse', function(e) {
            $('[data-target="#' + e.target.id + '"').children()
                .removeClass('glyphicon-chevron-down')
                .addClass('glyphicon-chevron-right');
            $.get($(this).attr('data-action')).fail(function() { return; });
            e.stopPropagation();
        });

        $('a.collapse-comment').on('click', function(e) { e.preventDefault(); });
    }

    $(document).ready(bindCollapse);

    return {
        bindCollapse: bindCollapse
    };
})(window.jQuery);
