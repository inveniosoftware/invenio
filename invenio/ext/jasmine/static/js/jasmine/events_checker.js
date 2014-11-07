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

  /**
   *
   * Usage:
   * expect(connectionList).toPassConnectionTests()
   *
   */
  function EventsChecker() {
    // holds messages describing connections for indexes if their expected
    // activity was detected before running the trigger
    this.failsBefore = [];
    // holds messages describing connections for indexes if their expected
    // function/event was not called
    this.failsAfter = [];
    this.exceptions = [];
  }

  function Error(message) {
    this.name = 'EventsChecker';
    this.message = message;
  }

  function typeOfExpectedActivity(item) {
    // event
    if (item.$element &&
      item.event && typeof item.event === 'string') {
      if (item.$element.length !== 1) {
        throw new Error('event element is a one element');
      }
      return EventsChecker.checkMethods.event;
    }
    // object method
    if (item.methodName && typeof(item.methodName) == 'string') {
      return EventsChecker.checkMethods.function;
    }
    throw new Error('Invalid connectionsList');
  }

  var triggerFunctions = {
    'function': function callMethod(triggered) {
      var args = triggered.args ? triggered.args : [];
      try {
        triggered.object[triggered.methodName].apply(triggered.object, args);
      } catch (err) {
        // cause jasmine generates its own error messages
        err.message += '\nMaybe you have not set `this` pointer properly in a ' +
          'function call description.';
        err.type = 'EmptyThis';
        throw err;
      }
    },
    event: function triggerEvent(triggered) {
      triggered.$element.trigger(triggered.event);
    },
  };

  var testerFunctions = {
    'function': function checkMethodCall(item, trigger, spy) {
      var didPassBefore = !spy.calls.any();
      if (spy.calls.any()) {
        spy.calls.reset();
      }
      trigger(item.triggered);
      var didPassAfter = spy.calls.any();
      item.expected.object[item.expected.methodName].calls.reset();
      return {
        before: didPassBefore,
        after: didPassAfter,
      };
    },
    event: function checkEvent(item, trigger, spy) {
      var didPassBefore = !jasmine.jQuery.events.wasTriggered(spy.selector, spy.eventName);
      if (!didPassBefore) {
        spy.reset();
        didPassBefore = true;
      }
      trigger(item.triggered);
      var didPassAfter = jasmine.jQuery.events.wasTriggered(spy.selector, spy.eventName);
      spy.reset();
      return {
        before: didPassBefore,
        after: didPassAfter,
      }
    },
  };

  var printFunc = {
    event: function printEvent() {
      return this.event + ' from ' + this.$element[0].outerHTML;
    },

    'function': function printFunc() {
      return this.methodName + ' of ' + this.object.constructor.name;
    }
  };

  EventsChecker.checkMethods = {
    event: 'event',
    'function': 'function',
  };

  EventsChecker.prototype = {

    checkMethods: EventsChecker.checkMethods,

    getTestForConnection: function(connection) {
      var triggered, expected;
      try {
        triggered = initActivityDescription(connection.triggered);
      } catch(e) {
        e.message = 'Error at item ' + i + ' (triggered): ' + e.message;
        throw e;
      }
      try {
        expected = initActivityDescription(connection.expected);
      } catch(e) {
        e.message = 'Error at item ' + i + ' (expected): ' + e.message;
        throw e;
      }
      var spy;
      if (expected.type == this.checkMethods.event) {
        spy = jasmine.jQuery.events.spyOn(expected.$element, expected.event);
      } else { // spy on function
        try {
          spy = spyOn(expected.object, expected.methodName).and.callThrough();
        } catch (e) {
          if (/has\ already\ been\ spied\ upon$/.test(e.message)) {
            spy = expected.object[expected.methodName];
            spy.calls.reset();
          } else {
            throw e;
          }
        }
      }
      return {
        spy: spy,
        trigger: triggerFunctions[triggered.type],
        tester: testerFunctions[expected.type],
      };

      function initActivityDescription(desc) {
        desc.type = typeOfExpectedActivity(desc);
        desc.print = printFunc[desc.type];
        if (desc.args == undefined) {
          desc.args = [];
        }
        if (desc.type == 'function' && !desc.object) {
          desc.object = window;
        }
        return desc;
      }
    },

    checkConnection: function(connection, test) {
      var result = {};
      try {
        result = test.tester(
          connection,
          test.trigger,
          test.spy
        );
      } catch(err) {
        if (err.type == 'EmptyThis') {
          result.exception = err.message;
        } else {
          throw err;
        }
      }
      return result;
    },

    test: function(connectionsList) {
      for (var i = 0; i < connectionsList.length; i++) {
        var connection = connectionsList[i];
        var test = this.getTestForConnection(connection);
        var testResult = this.checkConnection(connection, test);
        if (!testResult.before) {
          this.failsBefore[i] = this.printTestFailMessage(connection);
        }
        if (!testResult.after) {
          this.failsAfter[i] = this.printTestFailMessage(connection);
        }
        if (testResult.exception) {
          this.exceptions[i] = testResult.exception;
        }
      }

      return {
        pass: !this.failsBefore.length && !this.failsAfter.length && !this.exceptions.length,
        message: this.getMessages(),
      };
    },

    getMessages: function () {

      var message = '';

      if (this.failsBefore.length > 0) {
        message += 'Following events had the expected action triggered before their reason:\n';
        message += this.printList(this.failsBefore);
      }

      if (this.failsAfter.length > 0) {
        message += 'Following events didn\'t result with expected action after triggering the reason:\n';
        message += this.printList(this.failsAfter);
      }

      if (this.exceptions.length > 0) {
        message += 'Other exceptions:\n';
        message += this.printList(this.exceptions);
      }

      return message;
    },

    printTestFailMessage: function (connection) {
      var triggered = connection.triggered;
      var expected = connection.expected;
      return 'triggered: ' + triggered.print() + '\n' +
          '   expected: ' + expected.print();
    },

    /**
     * Prints a list of messages:
     * index. message
     * @param list {Array} array of strings
     */
    printList: function(list) {
      var message = '';
      for (var i = 0; i < list.length; i++) {
        if (!list[i]) {
          continue;
        }
        message += i + '. ' + list[i] + '\n';
      }
      return message;
    }
  };

  beforeEach(function () {
    jasmine.addMatchers({
      toPassConnectionTests: function () {
        return {
          /**
           * Initialize
           * @param connections {Array} of {
           *  triggered: {{
           *    $element: {jQuery object}
           *    event: {String}
           *    args: {Array}
           *  } | {
           *    function: {String},
           *    args: {Array}
           *  }}
           *  expected: {{
           *    $element: {jQuery object}
           *    event: {String}
           *    args: {Array}
           *  } | {
           *    function: {String},
           *    args: {Array}
           *  }}
           * }
           */
          compare: function (connections) {
            var checker = new EventsChecker();
            return checker.test(connections);
          }
        };
      },
    });
  });
}(window, window.jasmine, window.jQuery));
