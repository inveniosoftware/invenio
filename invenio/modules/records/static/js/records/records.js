/*
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014, 2015 CERN.
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

    var $ = require('jquery'),
        hasPushState = typeof window.history.pushState === 'function'

    // Could be written as a jQuery plugin.
    function Records(options) {
        this.options = $.extend({}, {
            menu: '#record-links',
            content: '#record_content'
        }, options)

        this.init()
    }

    Records.prototype.init = function() {
        this.element = $(this.options.menu)
        this.currentPath = this.element.find('li.active a').attr('href')
        this.states = []

        this.element.on('click', 'li a', this, function(e) {
            e.preventDefault()

            var a = $(e.target).closest('a'),
                path = a.attr('href'),
                li = a.closest('li')

            if (path && hasPushState && !li || !li.hasClass('disabled')) {
                window.history.pushState({path: path}, document.title, path)
                e.data.states.push({path: e.data.currentPath})
                e.data.reloadTab(path)
            }
        })

        $(window).on('popstate', this, function(e) {
            var state;
            if (e.state && e.state.path) {
                state = e.state
            } else if (e.data.states.length) {
                state = e.data.states.pop()
            } else {
                // No states to go back to.
                return
            }

            e.data.reloadTab(state.path)
        })
    }

    Records.prototype.reloadTab = function(path) {
        this.currentPath = path

        var element = this.element,
            content = $(this.options.content)

        $.ajax({
            method: "POST",
            url: path
        }).done(function(d) {
            element.find('li.active').removeClass('active')
            element.find('a[href="'+path+'"]').closest('li').addClass('active')

            content.html(d)
        }).fail(function() {
            alert("Something horrible just happened, send us a bug report if it persists.")
        });
    };

    return Records;
});
