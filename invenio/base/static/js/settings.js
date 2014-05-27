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

require.config({
    baseUrl: '',
    paths: {
        bootstrap: 'js/boostrap/js',
        typeahead: 'js/typeahead',
    },
    shim: {
        'bootstrap/affix': { deps: ['jquery'], exports: '$.fn.affix' },
        'bootstrap/alert': { deps: ['jquery'], exports: '$.fn.alert' },
        'bootstrap/button': { deps: ['jquery'], exports: '$.fn.button' },
        'bootstrap/carousel': { deps: ['jquery'], exports: '$.fn.carousel' },
        'bootstrap/collapse': { deps: ['jquery'], exports: '$.fn.collapse' },
        'bootstrap/dropdown': { deps: ['jquery'], exports: '$.fn.dropdown' },
        'bootstrap/modal': { deps: ['jquery'], exports: '$.fn.modal' },
        'bootstrap/popover': {
            deps: ['jquery', 'bootstrap/tooltip'],
            exports: '$.fn.popover'
        },
        'bootstrap/scrollspy': { deps: ['jquery'], exports: '$.fn.scrollspy' },
        'bootstrap/tab': { deps: ['jquery'], exports: '$.fn.tab' },
        'bootstrap/tooltip': { deps: ['jquery'], exports: '$.fn.tooltip' },
        'bootstrap/transition': { deps: ['jquery'], exports: '$.fn.transition' }
        jquery: { exports: '$' }
    }
})
