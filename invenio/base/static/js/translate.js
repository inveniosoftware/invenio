/**
 * This file is part of Invenio.
 * Copyright (C) 2013, 2014 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.

 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

require(['jquery'], function($) {
    'use strict';

    /**
     * translate the given word.
     *
     * @param word String source
     * @return html translation
     */
    function _(word) {
        var $child = $('#translated').find('#t' + word.replace(/ /g,''));
        if($child) {
            console.log(word + " translated to " + $child.html());
            return $child.html();
        }
        console.warning("translation missing for: " + word);
        return word;
    }

    window._ = _;
});
