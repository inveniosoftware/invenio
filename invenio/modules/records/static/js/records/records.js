/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
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

define(function(require) {
    'use strict';

    var $ = require('jquery');

    var reloadTab = function(path) {
        $(window).trigger('tabreload', [path]);
        $('#record-links li.active').removeClass('active');
        $('#record-links a[href="'+path+'"]').parent().addClass('active');
        $.post(path, function(data) {
            $('#record_content').html(data);
            $(window).trigger('tabreloaded', [path]);
        });
    };

    $(window).on('load', function() {
        $('#record-links li.disabled a').on('click', function(event) {
            event.preventDefault();
            event.stopImmediatePropagation();
            return false;
        });

        $('#record-links li:not(.disabled) a').on('click', function(event) {
            var path = $(event.target).attr('href');
            event.preventDefault();
            event.stopImmediatePropagation();
            if (typeof(window.history.pushState) === 'function') {
                window.history.pushState({path:path}, document.title, path);
            } else {
                window.location.hash = '#!' + path;
            }
            reloadTab(path);
        });


    });

    var initHref = $('#record-links li.active a').attr('href'),
    initLoc = null,
    lastLoc = window.location;

    window.onpopstate = function(event) {
        if (event.state && event.state.path) {
            reloadTab(event.state.path);
        } else if (event.target.location === initLoc) {
            if (lastLoc !== initLoc) {
                reloadTab(initHref);
            }
        } else {
            initLoc = window.location;
        }
        lastLoc = window.location;
    };

});