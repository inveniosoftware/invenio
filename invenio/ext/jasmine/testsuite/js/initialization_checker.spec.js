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

define([
  'jasmine-jquery',
  'jasmine-initialization',
], function() {

  describe('Initialization checker', function () {

    jasmine.getFixtures().fixturesPath = '/jasmine/spec/invenio.ext.jasmine/';

    loadFixtures('simple_div.html');

    var $d1 = $('#simpleDiv');
    var $d2 = $('#simpleDiv2');
    var $d3 = $('#simpleDiv3');

    var $empty1 = $('#simpleDifff');
    var $empty2 = $('#simpleDifff2');

    describe('for undefined values', function () {

      var ProperlyInitializedClass = function () {
        this.a = 1;
        this.b = {};
        this.c = [];
      };

      var NotProperlyInitializedClass = function () {
        this.a = 1;
        this.b = {};
        this.c = [];
        this.d = undefined;
      };

      var properlyInitializedObject, notProperlyInitializedObject;

      beforeEach(function () {
        properlyInitializedObject = new ProperlyInitializedClass;
        notProperlyInitializedObject = new NotProperlyInitializedClass;
      });

      it('passes the test with properlyInitializedObject', function () {
        expect(properlyInitializedObject).toHaveAllPropertiesInitialized();
      });

      it('fails the test with notProperlyInitializedObject', function () {
        expect(function () {
          expect(notProperlyInitializedObject)
            .not.toHaveAllPropertiesInitialized();
        })
      });

      it('passes the test with notProperlyInitializedObject ' +
        'because of undefined property being on the ignoredList', function () {
        expect(notProperlyInitializedObject)
          .toHaveAllPropertiesInitializedExcept('d');
      });

      describe('with an object with two uninitialized properties', function() {

        beforeEach(function() {
          notProperlyInitializedObject.e = undefined;
        });

        it('fails the test because just one of two undefined property is on ' +
          'ignoredList', function () {
          expect(notProperlyInitializedObject)
            .not.toHaveAllPropertiesInitializedExcept('d');
        });

        it('passes the test because the two properties are ignored', function() {
          expect(notProperlyInitializedObject)
            .toHaveAllPropertiesInitializedExcept(['e', 'd']);
        });
      });
    });

    describe('for empty jQuery object properties', function () {

      var BaseClass = function ($d, $e, $f) {
        this.a = 1;
        this.b = {};
        this.c = [];
        this.$d = $d;
        this.$e = $e;
        this.$f = $f;
      };

      var properlyInitializedObject, notProperlyInitializedObject;

      beforeEach(function () {
        properlyInitializedObject = new BaseClass(
          $d1,
          $d2,
          $d3
        );
        notProperlyInitializedObject = new BaseClass(
          $d1,
          $d2,
          $empty1
        );
      });

      it('passes the test with properlyInitializedObject', function () {
        expect(properlyInitializedObject).toHaveNoEmptyJQueryObjects();
      });

      it('fails the test with notProperlyInitializedObject', function () {
        expect(function () {
          expect(notProperlyInitializedObject)
            .not.toHaveNoEmptyJQueryObjects();
        });
      });

      it('passes the test with notProperlyInitializedObject ' +
        'because of undefined property being on the ignoredList', function () {
        expect(notProperlyInitializedObject)
          .toHaveNoEmptyJQueryObjectsExcept('$f');
      });

      describe('with an object with two empty jQuery object properties', function() {

        beforeEach(function() {
          notProperlyInitializedObject.g = $empty2;
        });

        it('fails the test because just one of two undefined property is on ' +
          'ignoredList', function () {
          expect(notProperlyInitializedObject)
            .not.toHaveNoEmptyJQueryObjectsExcept('$g');
        });

        it('passes the test because the two properties are ignored', function() {
          expect(notProperlyInitializedObject)
            .toHaveNoEmptyJQueryObjectsExcept(['$g', '$f']);
        })
      });
    });
  });
});
