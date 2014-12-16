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

(function (window, jasmine, $) {

  "use strict";

  function getNotInitializedProperties(obj, ignoredList) {
    var notInitializedProperties = [];
    for (var property in obj) {
      if (obj.hasOwnProperty(property) &&
        !(ignoredList.indexOf(property) > -1)) {
        if (obj[property] === undefined) {
          notInitializedProperties.push(property);
          continue;
        } else if (property.indexOf('$') == 0 &&
          obj[property].length == 0) {
          notInitializedProperties.push(property);
        }
      }
    }
    return notInitializedProperties;
  }

  /**
   * Checks if properties starting with $ are not empty arrays.
   *
   * @param obj
   * @param ignoredList
   * @returns {Array}
   */
  function getEmptyJQueryObjects(obj, ignoredList) {
    var emptyJQueryObjects = [];
    for (var property in obj) {
      if (obj.hasOwnProperty(property) &&
        property.indexOf('$') == 0 &&
        ignoredList.indexOf(property) == -1 &&
        obj[property].length == 0)
      {
        emptyJQueryObjects.push(property);
      }
    }
    return emptyJQueryObjects;
  }

  function compare_initializedTest(obj, ignoredList) {

    // ensure ignored list is an array
    ignoredList = [].concat(ignoredList);
    var notInitialized = getNotInitializedProperties(obj, ignoredList);
    var result = { pass: !notInitialized.length };

    if (!result.pass) {
        result.message = 'Expected an object to have all the ' +
        'properties initialized';
        if (ignoredList && ignoredList.length) {
          result.message += ' beside: ' + ignoredList.join(', ') + '.'
        }
        result.message += '.\nNot initialized properties are: ' + notInitialized.join(', ');
    }
    return result;
  }

  function compare_emptyJQueryObj(obj, ignoredList) {

    // ensure ignored list is an array
    ignoredList = [].concat(ignoredList);
    var empty = getEmptyJQueryObjects(obj, ignoredList);
    var result = { pass: !empty.length };

    if (!result.pass) {
        result.message = 'Expected an object to have all the ' +
        'properties which are jQuery objects to be not empty';
        if (ignoredList && ignoredList.length) {
          result.message += ' beside: ' + ignoredList.join(', ') + '.'
        }
        result.message += '.\nEmpty properties are: ' + empty.join(', ');
    }
    return result;
  }

  beforeEach(function () {
    jasmine.addMatchers({
      toHaveAllPropertiesInitializedExcept: function () {
        return {
          compare: function (obj, ignoredList) {
            return compare_initializedTest(obj, ignoredList)
          }
        };
      },
      toHaveAllPropertiesInitialized: function () {
        return {
          compare: function (obj) {
            return compare_initializedTest(obj, [])
          }
        };
      },
      toHaveNoEmptyJQueryObjects: function () {
        return {
          compare: function (obj) {
            return compare_emptyJQueryObj(obj, [])
          }
        };
      },
      toHaveNoEmptyJQueryObjectsExcept: function () {
        return {
          compare: function (obj, ignoredList) {
            return compare_emptyJQueryObj(obj, ignoredList)
          }
        };
      }
    });
  });
}(window, window.jasmine, window.jQuery));
