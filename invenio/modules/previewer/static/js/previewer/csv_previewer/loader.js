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
'use strict';

define(function(require) {

  var $ = require('jquery'),
      d3 = require('vendors/d3/d3');

  return require('flight/lib/component')(Loader);

  function Loader() {
    var Loader;

    this.handleShowLoader = function (ev, data) {
      if (data.id === Loader.id){
        this.$node.show();
      }
    };

    this.handleHideLoader = function (ev, data) {
      if (data.id === Loader.id){
        this.$node.hide();
      }
    };

    this.after('initialize', function () {
      Loader = this;
      Loader.id = Loader.$node.data('csv-target');

      Loader.on(document, 'showLoader', Loader.handleShowLoader);
      Loader.on(document, 'hideLoader', Loader.handleHideLoader);
      Loader.on('click', function (ev) {
        ev.preventDefault();
        Loader.trigger(document, 'loadNext', {
          id: Loader.id
        });
      });

      Loader.$node.hide();
    });
  }

});
