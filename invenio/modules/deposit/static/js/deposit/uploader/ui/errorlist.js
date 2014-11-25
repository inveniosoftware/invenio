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

define(function(require) {

    return require('flight/lib/component')(ErrorList);

    function ErrorList() {

        this.attributes({
            errorListSelector: "#errorList"
        });

        var errorListRow = require('hgn!../../templates/error');

        this.handleErrorOccurred = function(ev, error) {
            var html = "";
            this.$node.css("visibility", "visible");
            html = errorListRow(error);
            this.select('errorListSelector').append(html);
        };

        this.after('initialize', function() {
            this.on('errorOccurred', this.handleErrorOccurred);
        });
    }
});
