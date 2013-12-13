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

$(document).ready(function() {
    // Support for AJAX loaded modal window.
    // Focuses on first input textbox after it loads the window.
    $('[data-toggle="modal"]').click(function(e) {
        e.preventDefault();
        var href = $(this).attr('href');
        if (href.indexOf('#') === 0) {
            $(href).modal('open');
        } else {
            $.get(href, function(data) {
                $('<div class="modal" >' + data + '</div>').modal();
            }).success(function() { $('input:text:visible:first').focus(); });
        }
    });

    $('.collapse').on('show', function(e) {
        $.get($(this).attr('data-action'));
        e.stopPropagation();
    });

    $('.collapse').on('hide', function(e) {
        $.get($(this).attr('data-action')).fail(function() { return; });
        e.stopPropagation();
    });

    $('a.collapse-comment').on('click', function(e) { e.preventDefault(); });

});
