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

require([
  'jasmine-flight',
  'js/deposit/uploader/mixins/util',
], function(jasmineFlight, util) {
  describeMixin('js/deposit/uploader/mixins/util', function () {

    'use strict';

    describe('bytesToSize', function () {
      beforeEach(function () {
        this.setupComponent();
      });

      it('should work for 0 bytes', function () {
        expect(this.component.bytesToSize(0)).toEqual('0 Bytes');
      });
      it('should work for KB, MB, GB, TB', function () {
         expect(this.component.bytesToSize(10)).toEqual('10.00 Bytes');
         expect(this.component.bytesToSize(1e3)).toEqual('1.00 KB');
         expect(this.component.bytesToSize(1e6)).toEqual('1.00 MB');
         expect(this.component.bytesToSize(1e9)).toEqual('1.00 GB');
         expect(this.component.bytesToSize(1e12)).toEqual('1.00 TB');
      });
      it('should work for boundry values', function () {
        expect(this.component.bytesToSize(999)).toEqual('999.00 Bytes');
        expect(this.component.bytesToSize(1.1e+3)).toEqual('1.10 KB');
      });
      it('should work only for number', function () {
        expect(this.component.bytesToSize('0')).toEqual(NaN);
        expect(this.component.bytesToSize({})).toEqual(NaN);
        expect(this.component.bytesToSize([2])).toEqual(NaN);
        expect(this.component.bytesToSize(true)).toEqual(NaN);
      });
      it('should return NaN for values other then number', function () {
        expect(this.component.bytesToSize('0')).toEqual(NaN);
        expect(this.component.bytesToSize({})).toEqual(NaN);
      });
    });

    describe('guid', function () {
      beforeEach(function () {
        this.setupComponent();
      });

      it('should return string', function () {
        expect(typeof this.component.guid()).toEqual('string');
      });
      it('should be 36 characters long', function () {
        expect(this.component.guid().length).toBe(36);
      });
      it('should return pseudo-random strings', function () {
        var unique_array = function (arr) {
          return arr.reduce(function (p, c) {
            if (p.indexOf(c) < 0) p.push(c);
            return p;
          }, []);
        };
        var testStrings = [],
            i = 0;

        for(i; i < 100; i++) {
          testStrings.push(this.component.guid());
        }

        expect(unique_array(testStrings).length).toBe(testStrings.length);
      });
    });

    describe('getObjectSize', function () {
      beforeEach(function () {
        this.setupComponent();
      });

      it('should return the length of the object', function () {
        expect(this.component.getObjectSize({1:1, 2:2, 3:3, 4:4})).toBe(4);
      });
      it('should return the length of the array', function () {
        expect(this.component.getObjectSize([1,2,3,4])).toBe(4);
      });
    });
  });
});
