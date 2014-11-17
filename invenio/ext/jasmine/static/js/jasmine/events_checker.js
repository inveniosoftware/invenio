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
   * var checker = new jasmine.EventsChecker();
   * checker.init(connectionList);
   * // ... initialize all the objects here ...
   * expect(checker).toPassConnectionTests()
   *
   */
  function EventsChecker() {

    this.reset();
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
      var didPassBefore = true;//!spy.calls.any();
      if (spy.calls.any()) {
        spy.calls.reset();
      }
      trigger(item.triggered);
      var didPassAfter = spy.calls.any();
      // check if has been called with required args
//      if (item.triggered.args && item.triggered.args.length > 0) {
//        if (util.contains(spy.calls.allArgs(), item.triggered.args, customEqualityTesters)) {
//      }
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
      // FIXME: this.object.constructor does not really work here
      return this.methodName + ' of ' + this.object.constructor;
    }
  };

  EventsChecker.checkMethods = {
    event: 'event',
    'function': 'function',
  };

  EventsChecker.prototype = {

    checkMethods: EventsChecker.checkMethods,

    /**
     * Initialize
     * @param connectionsList {Array} of {
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
    init: function (connectionsList) {

      this.reset();
      this.connectionsList = connectionsList;
      for (var i = 0; i < this.connectionsList.length; i++) {
        var item = this.connectionsList[i];
        try {
          item.triggered = initActivityDescription(item.triggered);
        } catch(e) {
          e.message = 'Error at item ' + i + ' (triggered): ' + e.message;
          throw e;
        }
        try {
          item.expected = initActivityDescription(item.expected);
        } catch(e) {
          e.message = 'Error at item ' + i + ' (expected): ' + e.message;
          throw e;
        }
        var spy;
        if (item.expected.type == this.checkMethods.event) {
          spy = spyOnEvent(item.expected.$element,
            item.expected.event);
        } else { // spy on function
          try {
            spy = spyOn(item.expected.object, item.expected.methodName).and.callThrough();
          } catch (e) {
            if (/has\ already\ been\ spied\ upon$/.test(e.message)) {
              spy = item.expected.object[item.expected.methodName];
              spy.calls.reset();
            } else {
              throw e;
            }
          }
        }
        this.tests[i] = {
          spy: spy,
          trigger: triggerFunctions[item.triggered.type],
          tester: testerFunctions[item.expected.type],
        };
      }
      this.ready = true;

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

    reset: function () {

      this.tests = [];
      this.connectionsList = [];
      this.ready = false;
      // holds true for an index when given expected activity was
      // detected before running the trigger
      this.failsBefore = [];
      // holds true for an index when after calling the trigger the expected
      // function/event was not called
      this.failsAfter = [];
      this.done = false;
    },

    checkConnections: function () {

      if (this.done) {
        return {
          pass: false,
          message: 'The tests were already run, please run init method ' +
            'again before checking the connections.',
        };
      }

      var exceptionMessages = '';
      var noExceptions = true;

      for (var i = 0; i < this.connectionsList.length; i++) {
        try {
          var result = this.tests[i].tester(
            this.connectionsList[i],
            this.tests[i].trigger,
            this.tests[i].spy
          );
        } catch(err) {
          if (err.type == 'EmptyThis') {
            exceptionMessages += '' + i + '. ' + err.message + '\n';
            noExceptions = false;
            continue; // do next test
          } else {
            throw err;
          }
        }
        if (!result.before) {
          this.failsBefore.push(i);
        }

        if (!result.after) {
          this.failsAfter.push(i);
        }
      }
      this.done = true;

      if (exceptionMessages) {
        exceptionMessages = 'Other exceptions:\n' + exceptionMessages;
      }

      return {
        pass: !this.failsBefore.length && !this.failsAfter.length && noExceptions,
        message: this.getMessages() + '\n\n' + exceptionMessages,
      };


    },

    getMessages: function () {

      var message = '';
      var that = this;

      if (this.failsBefore.length > 0) {
        message += 'Following events had the expected action triggered before their reason:\n';
        message += printForIndices(this.failsBefore);
      }

      if (this.failsAfter.length > 0) {
        message += 'Following events didn\'t result with expected action after triggering the reason:\n';
        message += printForIndices(this.failsAfter);
      }

      return message;

      function printForIndices(indicesArray) {
        var message = '';
        for (var i = 0; i < indicesArray.length; i++) {
          message += that.printTestFailMessage(indicesArray[i]) + '\n';
        }
        return message;
      }

    },

    printTestFailMessage: function (index) {
      var triggered = this.connectionsList[index].triggered;
      var expected = this.connectionsList[index].expected;
      var indexSpace = ('' + index).length;
      var margin = Array(indexSpace + 1).join(" ");
      return '' + index + '. triggered: ' + triggered.print() + '\n' +
        margin + ' ' + ' expected: ' + expected.print();
    }
  };

  beforeEach(function () {
    jasmine.addMatchers({
      toPassConnectionTests: function () {
        return {
          compare: function (connections) {
            var checker = new EventsChecker();
            checker.init(connections);
            if (!checker.ready) {
              return {
                pass: false,
                message: "EventsChecker not initialized properly.",
              }
            }
            return checker.checkConnections();
          }
        };
      },
    });
  });
}(window, window.jasmine, window.jQuery));
