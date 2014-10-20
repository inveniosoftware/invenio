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

  function Util() {
    this.bytesToSize = function(bytes) {
      var SIZES = ['Bytes', 'KB', 'MB', 'GB', 'TB'],
      k = 1000,
      i = null;

      if (typeof bytes !== 'number') {
        return NaN;
      }
      if (bytes === 0) {
        return '0 Bytes';
      }
      i = Math.floor(Math.log(bytes) / Math.log(k));
      return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + SIZES[i];
    };

    this.guid = (function() {
      var gen = function() {
        return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
      };

      return function() {
        return gen() + gen() + '-' + gen() + '-' + gen() + '-' + gen() + '-' + gen() + gen() + gen();
      };
    }());

    this.getObjectSize = function(obj) {
      var size = 0,
      key;
      for (key in obj) {
        if (obj.hasOwnProperty(key)) size++;
      }
      return size;
    }
  }

  return Util;
});
