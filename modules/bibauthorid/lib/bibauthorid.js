//
// This file is part of Invenio.
// Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
//
// Invenio is free software; you can redistribute it and / or
// modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// Invenio is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Invenio; if not, write to the Free Software Foundation, Inc.,
// 59 Temple Place, Suite 330, Boston, MA 02111 - 1307, USA.

/**
 * Contains all code for the Ticket Box App under the ticketbox namespace
 * @type {{module: module}}
 */
var ticketbox = {

    // Closure to protect modules.
    module: function() {

        // Module store.
        var modules = {};

        // Return shared module reference or create a new one.
        return function(name) {
            if (modules[name]) {
                return modules[name];
            }

            return modules[name] = { Views : {} };
        };
    }(),

    app: { debug: true, hasFocus: false },

    sureUpdate: function() {
        var time = 1000;
        var growth = 0.1;
        var app = ticketbox.app;

        var poller = function() {

            var failure = function() {
                    time += time * growth;
                    window.setTimeout(poller, time);
                    app.debug && console.log("[SureUpdate] FAILED: Retrying in " + time/1000 + " seconds.");
            };

            var success = function() {
                app.debug && console.log("[SureUpdate] Update succeeded after multiple attempts.");
            };

            if (app.hasFocus) {
                app.userops.fetch({"on": 'user', "error": failure, "success": success});
            }
        };

        return function(coll, resp, opt) {
            window.setTimeout(poller, time);
        };


    },

    personalDetails: function ( $box ) {
        var $quickViewBoxes = $box.find("div.bai-quick-view"),
            suggestForCname = $(".bai-details-selection").data("cname"),
            suggestionConfirmation = null;

        suggestionConfirmation = function (cname, hepRecord, $choice) {
          var bodyModel = ticketbox.app.bodyModel,
              modalContent = Handlebars.templates.hepConfirmation({ cname: cname }),
              modal =
              callbacks = null;

          callbacks = {
            "show.bs.modal": function(e) {
                var $confirmButton = $(e.currentTarget).find("a.confirm"),
                    $modal = $("#ticket-modal"),
                    $confirmationPreview = $(".confirmation-preview");

                $confirmationPreview.append($choice);

                $confirmButton.click( function() {
                  var successCallback =
                      errorCallback =
                      data = null;

                  data = {
                      cname: cname,
                      hepname: hepRecord
                  };

                  successCallback = function () {
                    $modal.find(".modal-body").html("<p>Your contribution has been submitted and will be processed soon.</p>");
                    $modal.find(".modal-header>.modal-title").text("Thank You");
                    $modal.find(".modal-footer>a.confirm").remove();
                    $modal.find(".modal-footer>a.back").text("Close");
                  };

                  errorCallback = function () {
                    $modal.find(".modal-body").html("<p>There is a problem with INSPIRE at the moment. Please try again in a couple of minutes.</p>");
                    $modal.find(".modal-header>.modal-title").text("Try again later");
                    $modal.find(".modal-footer>a.confirm").remove();
                    $modal.find(".modal-footer>a.back").text("Close");
                  };

                  $.ajax({
                    dataType: 'json',
                    type: 'POST',
                    url: '/author/manage_profile/connect_author_with_hepname_ajax',
                    data: {jsondata: JSON.stringify(data)},
                    success: successCallback,
                    error: errorCallback
                  });

                });
              }
          };

          modal = {
              prompt: true,
              shown: false,
              content: modalContent,
              callbacks: callbacks
          };
          bodyModel.set( { modal: modal } );

        };

        $(".bai-details-selection").on("click", ".list-group>a[href='#']", function(event) {
          var hepSuggestion = $(this).data("heprecord"),
              $choice = $(this).clone();

          $choice.find(".bai-quick-view-spot").popover({
            html: true,
            placement: "auto",
            trigger: "hover",
            content: $choice.find(".bai-quick-view-src").html(),
            container: ".modal-dialog"
          });

          suggestionConfirmation(suggestForCname, hepSuggestion, $choice);
          return event.preventDefault();
        });

        $quickViewBoxes.each(function( index, value ) {
          var $hotspot = $(value).find(".bai-quick-view-spot");

          $hotspot.popover({
            html: true,
            placement: "auto",
            trigger: "hover",
            content: $(value).find(".bai-quick-view-src").html(),
            container: ".bai-details-selection"
          });

        });

      }
};

/**
 * Module that defines Server boundary
 * Immediately-Invoked Function Expression. (IIFE)
 */
(function(ticketbox, Server) {

    // Dependencies
    var app = ticketbox.app;

    Server.dataOn = function(data, on) {
        var add = {
            user: {"on":"user"},
            autoclaim: {"on":"autoclaim"}
        };

        if (on in add) {
            return $.extend({}, data, add[on]);
        } else {
            app.debug && console.error("[Server Sync] ERROR: No ticket target, using 'user' as default!");
            return $.extend({}, data, {"on":'user'});
        }
    };

    Server.process = function(type, on, data) {
        // Populate data with ticket target, default is 'user'
        var params = {type: 'POST', dataType: 'json'};

        params.data = {};
        params.data.jsondata = Server.dataOn({}, on);

        // Set success and error callbacks
        params.success = function() {
            app.userops.fetch({success: data.success});
        };
        params.error = data.error || function() {
            app.userops.fetch();
            app.debug && console.error("[Server Process] ERROR: Processing Error.");
        };

        var message = "[Server Process] ";
        switch(type) {
            case "commit":
                params.url = "/author/ticket/commit";
                params.data.jsondata = $.extend({}, params.data.jsondata, data.data);
                message += "Commit: " + JSON.stringify(params);
                break;
            case "abort":
                params.url = "/author/ticket/abort";
                message += "Abort: " + JSON.stringify(params);
                break;
            case "update":
                params.url = "/author/ticket/update_status";
                message += "Update: " + JSON.stringify(params);
                break;
            default:
                message += "ERROR: Unknown process type.";
                console.log(message);
                return;

        }
        app.debug && console.log(message);

        params.data.jsondata = JSON.stringify(params.data.jsondata);
        Backbone.ajax(params);
    };

    Server.sync = function(method, model, options) {

        var params = {type: 'POST', dataType: 'json'};

        // Populate data with ticket target, default is 'user'
        params.data = {};
        params.data.jsondata = Server.dataOn({}, options.on);

        var syncCallback = function(jqXHR, status) {
            var sureUpdate = ticketbox.sureUpdate();
            if (method != "read") {
                app.userops.fetch({"on": 'user', "error": sureUpdate});
            }
        };

        // Set AJAX callbacks
        params.success = options.success;
        params.error = options.error;
        params.complete = syncCallback;

        var generateRequest = function(type) {
            var requestTypes  = {
                add: function() {
                    return {
                        'pid': model.get('pid'),
                        'action': model.get('action'),
                        'bibrefrec': model.bibrefrec(),
                        'on': model.get('on')
                    };
                },
                get_status: function() {
                    return {
                        'on': model.get('on')
                    };
                }
            };
            requestTypes.modify = requestTypes.add;
            requestTypes.remove = requestTypes.add;

            if (type in requestTypes) {
                return requestTypes[type]();
            } else {
                app.debug && console.error("[Operation Model] ERROR: No request type defined.");
                return {};
            }
        };

        switch (method) {
            case 'create':
                params.url = "/author/ticket/add_operation";
                params.data.jsondata = $.extend({}, generateRequest('add'), params.data.jsondata);
                break;

            case 'update':
                params.url = "/author/ticket/modify_operation";
                params.data.jsondata = $.extend({}, generateRequest('modify'), params.data.jsondata);
                break;

            case 'delete':
                params.url = "/author/ticket/remove_operation";
                params.data.jsondata = $.extend({}, generateRequest('remove'), params.data.jsondata);
                break;

            case 'read':
                params.url = "/author/ticket/get_status";
                params.data.jsondata = $.extend({}, generateRequest('get_status'), params.data.jsondata);
                break;

        }
        params.data.jsondata = JSON.stringify(params.data.jsondata);
        Backbone.ajax(params);

    };

    Server.search = function(type, data, options) {

        var params = {type: 'POST', dataType: 'json', data: {}};

        // Set success and error callbacks and context
        params.success = options.success;
        params.error = options.error;
        params.context = options.context;

        var dispatchers = {
            pid: function(data) {
                if (data.hasOwnProperty("query")) {
                    params.url = "/author/search_ajax/list/" + _.escape(data.query);
                    Backbone.ajax(params);
                } else if (data.hasOwnProperty("pids")) {
                    params.url = "/author/search_ajax/details";
                    params.data.jsondata = JSON.stringify({pids: data.pids});
                    Backbone.ajax(params);
                } else {
                    app.debug && console.error("[Server Search] ERROR: No search configuration data.");
                }
            }
        };

        if (type in dispatchers) {
            dispatchers[type](data);
        } else {
            app.debug && console.error("[Server Search] Search type unknown");
        }

    };


})(ticketbox, ticketbox.module("server"));


/**
 * Module that defines Router
 * Immediately-Invoked Function Expression. (IIFE)
 */
//(function(ticketbox, Router) {
//
//    // Dependencies
//    var Server = ticketbox.module("server");
//
//    // Shorthands
//    var app = ticketbox.app;
//
//    Router.Model = Backbone.Router.extend({
//        routes: {
//            "assign/:bibrefrec/:pid": "addAssignOp",
//            "reject/:bibrefrec/:pid": "addRejectOp"
//        }
//    });
//
//    // Create global router
//    app.router = new Router.Model();
//    app.router.on("route:addAssignOp", function(bibrefrec, pid) {app.debug && console.log('Assign Op: ' + bibrefrec + ' ' + pid)});
//    app.router.on("route:addRejectOp", function(bibrefrec, pid) {app.debug && console.log('Assign Op: ' + bibrefrec + ' ' + pid)});
//    Backbone.history.start();
//
//})(ticketbox, ticketbox.module("router"));


/**
 * Module that defines Operation
 * Immediately-Invoked Function Expression. (IIFE)
 */
(function(ticketbox, Operation) {

    // Dependencies
    var Server = ticketbox.module("server");

    // Shorthands
    var app = ticketbox.app;

    var template = Handlebars.templates.singleOperation;

    Operation.Model = Backbone.Model.extend({

       idAttribute: "rec",

       defaults: {
            rec_title: "Loading..",
            on: "user",
            ignored: false
        },

       sync: Server.sync,

        initialize: function(){
            app.debug && console.log("Instance of Operation Model Created.");
            this.set( { complete: this.isComplete() } );
            this.listenTo(this, "change", function() {
              app.debug && console.log(this.id + " has changed!");
              this.set( {complete: this.isComplete() } );
            });
        },

        getTarget: function() {
            return this.get('on');
        },

        setBibref: function(bibref) {
            var bibrefRegex = /\d+:\d+/;
            if (bibref === "") {
                this.set({ignored: true});
                this.set({bibref: null});
            } else if (bibrefRegex.test(bibref)) {
                this.set({bibref: bibref});
            }
        },

        getAction: function() {
            if (this.get("action") == "assign") {
                return "Assign";
            } else if (this.get("action") == "reject") {
                return "Reject";
            } else if (this.get("action") == "reset") {
                return "Forget";
            } else {
                return "Unknown";
            }
        },

        isComplete: function() {
            return (this.has('bibref') && (this.has('rec') || this.has('op_rec')));
        },



        bibrefrec: function() {

            if (this.isComplete()) {
                var rec = this.get('rec');

                if (this.isNew()) {
                    rec = this.get('op_rec');
                }
                return this.get('bibref') + "," + rec;

            } else {
                if (this.isNew()) {
                    return this.get('op_rec');
                } else {
                    return this.get('rec');
                }

            }
        }

    });

    Operation.View = Backbone.View.extend({
        tagName: "div",

        className: "col-sm-12 col-md-10 col-lg-8",

        events: {
            'click .removeOp': 'removeOperation',
            'change select': 'bibrefSelected'
        },

        initialize: function(){
            app.debug && console.log("Operation View Created!");
            this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "destroy", this.destroyOp);
            this.listenTo(this.model, "removeview", this.destroyOp);
            this.listenTo(this.model, "invalid", function() { alert("Did not pass validation!"); });

        },

        destroyOp: function() {
            var element = this;
            this.$el.hide(400, function() {
                element.remove();
            });
        },

        selectBibrefOption: function() {
            if (this.model.has("bibrefs")) {
                var items = this.$("option");
                items.removeAttr("selected");

                if (this.model.isComplete()) {
                    items.filter("[value='" + this.model.get('bibref') + "']").first().attr("selected","selected");
                } else {
                    items.filter(".nobibref").first().attr("selected","selected");
                }
            }
        },

        render: function() {

            if (this.model.has("execution_result")) {
                var operation = this.model.get('execution_result');
                    if (operation.operation == "ticketized") {
                        this.$el.css("background-color", "#AAFFAA");
                    } else {
                        this.$el.css("background-color", "#FFAAAA");
                    }
            }
            var context = {
                rec_title: this.model.get("rec_title"),
                rec_link: document.location.origin + "/record/" + this.model.get("rec"),
                cname: this.model.get("cname"),
                pid: this.model.get("pid"),
                profile: (!this.model.get("cname") && this.model.get("pid")) ? this.model.get("pid") : this.model.get("cname"),
                profile_link: document.location.origin + "/author/profile/" + this.model.get("cname"),
                editable: this.model.has("bibrefs"),
                bibrefs: this.model.get("bibrefs"),
                action: {
                    action: this.model.getAction(),
                    classes: this.getActionClasses()
                }
            };

            this.$el.html(template(context));
            this.selectBibrefOption();
            MathJax.Hub.Queue(["Reprocess", MathJax.Hub, this.$el.get(0)]);
            app.debug && console.log("Operation Rendered!");
            return this;
        },

        removeOperation: function() {
            app.debug && console.log("Operation Model Destroyed!");
            app.debug && console.log("Collection Changed - " + JSON.stringify(app.userops.toJSON()));
            this.model.destroy({"on": this.model.getTarget()});
        },

        getActionClasses: function() {
            var action = {
                assign: "op-assign",
                reject: "op-reject",
                reset: "op-reset"
            };

            var modelAction = this.model.get("action");
            if (modelAction in action) {
                return action[modelAction];
            } else {
                app.debug && console.error("[Operation View] ERROR: No class found for action.");
                return "";
            }
        },

        bibrefSelected: function(event) {
            var value = this.$("select").val();
            this.model.setBibref(value);
            app.debug && console.log("BIBREF Saved: " + JSON.stringify(value));
            app.debug && console.error("Operation Target: " + JSON.stringify({"on": this.model.getTarget()}) );
            this.model.save({"on": this.model.getTarget()});
        },

        save: function() {
            var value = this.$("select").val();
            this.model.setBibref(value);
            app.debug && console.log("BIBREF Saved: " + JSON.stringify(value));
            app.debug && console.error("Operation Target: " + JSON.stringify({"on": this.model.getTarget()}) );
            this.model.save({"on": this.model.getTarget()});
        }

    });

})(ticketbox, ticketbox.module("operation"));


/**
 * Module that defines Ticket
 * Immediately-Invoked Function Expression. (IIFE)
 */
(function(ticketbox, Ticket) {

    // Dependencies
    var Operation = ticketbox.module("operation");
    var Server = ticketbox.module("server");

    // Shorthands
    var app = ticketbox.app;

    // Template
    var add = "<span id=\"add_form\">Testing Feature ONLY: <form class=\"form-inline\" id=\"debug_form\"> <input type=\"text\" class=\"input-small\" name=\"pid\" placeholder=\"pid\"> <input type=\"text\" name=\"bibrefrec\" class=\"input-small\" placeholder=\"bibrefrec\"> <select id=\"action1\" class=\"input-small\"><option selected=\"selected\" value=\"assign\">assign</option><option value=\"reject\">reject</option></select> <select name=\"on\" class=\"input-small\"><option selected=\"selected\" value=\"user\">user</option><option value=\"autoclaim\">autoclaim</option></select> <button id=\"addButton\">Add</button><button id=\"updateButton\">Update Status</button></form></span>";
    var statstemplate = Handlebars.templates.opsDebugStats;

    Ticket.Operations = Backbone.Collection.extend({
        model: Operation.Model,

        sync: Server.sync,

        initialize: function() {
            this.listenTo(this, 'change', function(){app.debug && console.log("Collection Changed - " + JSON.stringify(this.toJSON()));});
        },

        completed: function() {
            return this.filter(function(operation) {
                return operation.isComplete() || operation.get("ignored");
            });
        },

        incomplete: function() {
            return this.without.apply(this, this.completed());
        },

        committed: function() {
            return typeof this.find(function(op) {
                return op.has("execution_result");
            }) != 'undefined';
        },

        outcome: function() {
            var result = {ticketized: 0, other: 0};
            return this.reduce(function(memo, value) {
                var op = value.get("execution_result");

                if (typeof op != "undefined") {
                  if (op.operation == "ticketized") {
                      memo.ticketized++;
                  } else {
                      memo.other++;
                  }
                }
                return memo;
            }, result);

        }


    });

    // Create global user operations collection.
    app.userops = new Ticket.Operations();


    Ticket.OperationsView = Backbone.View.extend({
        tagName: "div",

        className: "row clearfix",

        attributes: {
            id: "complete"
        },

        initialize: function() {
            this.listenTo(app.userops, 'add', this.addOne);
            this.listenTo(app.userops, 'reset', this.render);
        },

        addOne: function(operation) {
            var view = new Operation.View({model: operation});
            this.$el.append(view.render().el);
            view.$el.show(400);
        },

        render: function() {
            this.$el.html('');
            app.userops.each(this.addOne, this);
            return this;
        }

    });


    Ticket.View = Backbone.View.extend({
        tagName: "div",

        commitModalTemplate: Handlebars.templates.commitModal,

        discardModalTemplate: Handlebars.templates.discardModal,

        className: "alert alert-info",

        attributes: {
            id: "ticket_status"
        },

        events: {
            "click #addButton": "addOp",
            "click #commitButton": "commitModalTriggered",
            "click #abortButton": "discardAllTriggered",
            "click #updateButton": "updateOp"
        },

        initialize: function() {
            this.initSubViews();
            this.hookEvents();
            this.initNodes(this.$el, this);
        },

        initSubViews: function() {
            this.operationsView = new Ticket.OperationsView();
        },


        hookEvents: function() {
            this.listenTo(app.userops, 'change', this.changed);
            this.listenTo(app.userops, 'add', this.changed);
            this.listenTo(app.userops, 'remove', this.removed);
            this.hookTableLinks();
            this.hookBodyModel();
        },

        hookTableLinks: function() {
            var view = this;
            $("#bai_content").on("click", ".op_action", function(event) {
                var href = $(event.target).attr("href");
                var add_result = view.handleTableClickOperation(href);

                if (add_result) {
                    event.preventDefault();
                    return false;
                } else {
                    return true;
                }


            });
        },

        handleTableClickOperation: function(url) {
            if (url) {
                var op_regex = /author\/claim\/action\?(confirm|repeal|reset|to_other_person)=True&selection=(?:(\d+:\d+),)?(?:(\d+))(?:&pid=(\d+))?/;
                var data = url.match(op_regex);

                var model_data = {};

                switch(data[1]) {
                    case "confirm":
                        model_data = _.extend(model_data, {action: "assign"});
                        break;

                    case "repeal":
                        model_data = _.extend(model_data, {action: "reject"});
                        break;

                    case "reset":
                        model_data = _.extend(model_data, {action: "reset"});
                        break;

                    default:
                        return false;
                }

                model_data = _.extend(model_data, {
                            bibref: data[2],
                            op_rec: data[3],
                            pid: data[4],
                            on: "user"
                });

                var model_instance = new Operation.Model(model_data);
                model_instance.save({on: "user"});
                model_instance.set({rec: model_instance.get('op_rec')});
                app.userops.add(model_instance);

                return true;

            } else {
                return false;
            }

        },

        hookBodyModel: function() {
            this.prompted = false;
            this.listenTo(app.userops, 'add', this.handleUserLevel);
            this.listenTo(app.bodyModel, 'change', this.handleUserLevel);

        },

        initNodes: function($el, that) {
          $el.html( Handlebars.templates.ticketBox());
          $el.find("#ticket-buttons").before( this.operationsView.el );

          this.$commitbutton = $el.find( "#commitButton" );
          this.$debugTools = $el.find( "div#debug-dialog .panel-body" );
          this.$ticketModal = $( "#ticket-modal" );

          this.$debugTools.html( statstemplate({total: 0, igcom: 0, incomplete: 0}) );
          this.$stats = this.$debugTools.find("#stats");

          $("#bai_content").before(this.el);
          this.$el.hide();
          this.$debugTools.parent().toggleClass( "hidden", true );
        },

        showDebugTools: function() {

          this.$debugTools.parent().toggleClass( "hidden", false );
          this.$debugTools.toggleClass( "hidden", false );

          this.unbindFormSubmitEvents(this.$debugTools);

        },

        unbindFormSubmitEvents: function($el) {
            $el.submit(function() {
                 $('input[type=submit]', this).attr('disabled', 'disabled');
                return false;
            });
        },

        removeDebugTools: function() {
          this.$debugTools.toggleClass( "hidden", true );
        },

        updateBodyModalUserLevel: function () {
          var userLevel = app.bodyModel.get("userLevel"),
              guestPrompt = app.bodyModel.get("guestPrompt"),
              template = Handlebars.templates.loginPrompt();

          if (userLevel == "guest" && guestPrompt) {
            app.bodyModel.set({
              modal: {
                prompt: true,
                seen: false,
                content: template,
                callbacks: null
              }
            });
            this.prompted = true;
          }
        },

        handleUserLevel: function() {
            if (! this.prompted) {
                if (app.userops.length < 1) {
                    this.updateBodyModalUserLevel();
                }
            }
            if ( app.bodyModel.get("userLevel") == 'admin' && app.debug ) {
              this.showDebugTools();
            } else {
              this.removeDebugTools();
            }
        },

        render: function() {
            if ( ! this.$debugTools.hasClass( "hidden" ) ) {
                this.$stats.html( statstemplate({total: app.userops.length, igcom: _.size(app.userops.completed()), incomplete: _.size(app.userops.incomplete()), committed: app.userops.committed(), outcome: JSON.stringify(app.userops.outcome())}));
            }
        },


        addOne: function(operation) {
            var view = new Operation.View({model: operation});
            this.$el.append(view.render().el);
            this.render();
        },

        addAll: function() {
            this.$el.html('');
            app.userops.each(this.addOne, this);
        },

        toggleCommitBlocking: function() {
            if (_.size(app.userops.completed()) > 0) {
                this.$commitbutton.removeAttr("disabled");
            } else {
                this.$commitbutton.attr("disabled", "disabled");
            }
        },

        changed: function() {
            app.debug && console.log("Switching triggered");
//            if (_.size(app.userops.incomplete()) > 0) {
//                app.debug && console.log("Visible");
//                this.$("#intervention").toggleClass('hidden', false);
//            } else {
//                app.debug && console.log("Hidden");
//                this.$("#intervention").toggleClass('hidden', true);
//
//            }

            if (app.userops.length > 0) {
                this.$el.show(400);
                app.debug && console.log("Ticket System Shown");
            } else {
                this.$el.hide(400);
                app.debug && console.log("Ticket System Hidden");

            }

            this.toggleCommitBlocking();
            this.render();
        },

        removed: function(operation) {
            operation.trigger('removeview');
            if (_.size(app.userops.incomplete()) < 1) {
                this.$("#intervention").toggleClass('hidden', true);
            }

            if (app.userops.length > 0) {
                this.$el.show(400);
            } else {
                this.$el.hide(400);
            }

            this.toggleCommitBlocking();

            this.render();
        },

        addOp: function() {
            var form = this.$("#add_op");

            var params = {
                        pid: form.find("[name='pid']").val(),
                        action: form.find("#action1").val(),
                        on: form.find("[name='on']").val(),
                        bibrefrec: form.find("[name=bibrefrec]").val()
            };

            var options = {
                success: function() {
                    $(this).unbind();
                    app.debug && console.log("Operation Added!");
                    app.userops.fetch();
                },

                error: function() {
                    app.debug && console.error("[ERROR] Operation could not be added!");
                }
            };

            var model = {
                bibrefrec: function() {
                    return params.bibrefrec;
                }
            };
            model.get = function(target) {
                    return params[target];
             };

            Server.sync("create", model, options);

        },

        resizeModal: function() {
            var modal = this.$commitModal;
            var modalBody = modal.find(".modal-body");

            var height = $(window).height();
            var width = $(window).width();

            // Outer box
            if ((width * 0.66) > parseInt(modal.css("min-width").match("(\\d+)")[1])) {
                modal.width(width * 0.66);
            }

            // Inner content
            var fixedHeight = modal.find(".modal-header").outerHeight() + modal.find(".modal-footer").outerHeight();

        },

        commitOp: function( event ) {
            var $form = event.data.form,
                parsleyObj = event.data.parsleyObj,
                view = this;

            if ( parsleyObj.isValid() ) {
                view.immediateCommitOp();
            }

            return event.preventDefault();
        },

        immediateCommitOp: function() {
            this.commitContinueTriggered();
            return false;
        },

        displayCommitStatus: function( content ) {
            var $modal = this.$ticketModal.find( ".modal-content" ).html( content );

            this.modalSpinner.stop();
            $modal.height( "auto" );
            this.committing = false;
            this.complete = true;
        },

        generateCommitTicketizedMessage: function(connectives) {
            if (connectives) {
                return "The other changes will require INSPIRE staff to review them before it will take effect. ";
            } else {
                return "The changes will require INSPIRE staff to review them before it will take effect. ";
            }
        },

        generateCommitOtherMessage: function(connectives) {
            if (connectives) {
                return "The changes you have proposed were submitted and some will appear immediately.";
            } else {
                return "The changes you have proposed were submitted and will appear immediately.";
            }
        },

        commitSuccess: function() {
           var outcome = app.userops.outcome(),
               error = (outcome.other < 1) && (outcome.ticketized < 1),
               connectives = (outcome.other > 0) && (outcome.ticketized > 0),
               isAdmin = app.bodyModel.get("userLevel") == "admin",
               content = null,
               message = "";

          if (error) {
            return this.commitError();

          }

          if (outcome.other > 0) {

            message += this.generateCommitOtherMessage(connectives);
            message += " ";

          }

          if (outcome.ticketized > 0) {

            message += this.generateCommitTicketizedMessage(connectives);

          }

          content = Handlebars.templates.resultModal( {

            error: error,
            admin: isAdmin,
            text: message

          } );

          this.displayCommitStatus( content );
          Server.process("update", "user", {});

          this.$ticketModal.on( "hidden.bs.modal", function( e ) {

            window.location.reload();

          } );
        },

        commitError: function() {
          var content = Handlebars.templates.resultModal( { error: true } );
            this.displayCommitStatus( content );
            Server.process("update", "user", {});

          this.$ticketModal.on( "hidden.bs.modal", function( e ) {

            window.location.reload();

          } );
        },

        commitContinueTriggered: function() {
            var modal = this.$ticketModal.find( ".modal-content" ),
                modalHeader = modal.find( ".modal-header" ),
                modalBody = modal.find( ".modal-body" ),
                modalFooter = modal.find( ".modal-footer" ),
                opts =
                config = null;

            // Indicate committing
            this.committing = true;
            this.complete = false;

            // Preserve modal dimensions.
            modal.height(modal.height());
            modal.width(modal.width());

            // Empty out modal and fix dimensions
            modalHeader.html('');
            modalBody.html('');
            modalFooter.html('');
            modalBody.height("100%");

            // Load spinner
            opts = {

              lines: 22, // The number of lines to draw
              length: 10, // The length of each line
              width: 3, // The line thickness
              radius: 24, // The radius of the inner circle
              corners: 1, // Corner roundness (0..1)
              rotate: 0, // The rotation offset
              direction: 1, // 1: clockwise, -1: counterclockwise
              color: '#69C', // #rgb or #rrggbb or array of colors
              speed: 2.1, // Rounds per second
              trail: 41, // Afterglow percentage
              shadow: false, // Whether to render a shadow
              hwaccel: false, // Whether to use hardware acceleration
              className: 'spinner', // The CSS class to assign to the spinner
              zIndex: 2e9, // The z-index (defaults to 2000000000)
              top: 'auto', // Top position relative to parent in px
              left: 'auto' // Left position relative to parent in px

            };
            this.modalSpinner = new Spinner(opts).spin(modalBody.get(0));

            config = {
                data: this.userDetails,
                success: $.proxy( this.commitSuccess, this ),
                error: $.proxy( this.commitError, this ),
                context: this
            };

            Server.process("commit", "user", config);

        },

        modalCleanup: function( $modal ) {
          $modal.off( "show.bs.modal show.bs.modal" );
          $modal.off( "hide.bs.modal hidden.bs.modal" );
          $modal.off( "loaded.bs.modal" );
        },

        commitModalTriggered: function() {

          var view = this,
              $ticketModal = this.$ticketModal,
              $modalContent = $ticketModal.find( ".modal-content" ),
              discardAll = this.discardAllOp,
              validate = ! ( this.userDetails === undefined ),
              userLevel = app.bodyModel.get( "userLevel" ),
              userDetails =
              updateUserDetails =
              refreshButtonValidation =
              context =
              modals = null;

            this.userDetails = userDetails = this.userDetails || {
                first_name: "",
                last_name: "",
                email: "",
                comments: ""
            };

            context = { userDetails: userDetails };

            updateUserDetails = function( $el ) {

                this.userDetails = {

                    first_name: $el.find("#firstName").val(),
                    last_name: $el.find("#lastName").val(),
                    email: $el.find("#email").val(),
                    comments: $el.find("#comments").val()

                };
            };

            modals = {

              user: function() {
                _.extend( context, { title: "Any Comments?", guest: false } );
                return view.commitModalTemplate( context );
              },

              admin: function() {
                _.extend( context, { title: "Please wait", guest: false } );
                return view.commitModalTemplate( context );
              },

              guest: function() {
                _.extend( context, { title: "Enter Your Details", guest: true } );
                return view.commitModalTemplate( context );
              }

            };

            if ( userLevel in modals ) {

              $modalContent.html( modals[userLevel]() );

            } else {

              $modalContent.html( modals.guest() );

            }

          $ticketModal.on( "show.bs.modal", function( e ){

            var $continueButton = $modalContent.find( ".continue" ),
                $backButton = $modalContent.find( ".back" ),
                $form = $modalContent.find( "form" ),
                modal = $ticketModal,
                parsleyObj = null;

            parsleyObj = $form.parsley({
                            successClass: 'success',
                            errorClass: 'error',
                            errors: {
                                classHandler: function ( elem, isRadioOrCheckbox ) {
                                    return $( elem ).parent().parent();
                                },
                                container: function (element, isRadioOrCheckbox) {
                                    var $container = element.parent().find(".help-block");
                                    if ($container.length === 0) {
                                        $container = $("<span class='help-block'></span>").insertAfter(element);
                                    }
                                    return $container;
                                },
                                errorsWrapper: '<ul class="unstyled"></ul>'
                            }


            });

            // If it is not the first time the form has loaded, validate is true. Display validation status at load.
            if (validate) {

              parsleyObj.validate();

            }

            $continueButton.click( { form: $form, parsleyObj: parsleyObj }, $.proxy( view.commitOp, view ) );

            refreshButtonValidation = function() {

              if ( parsleyObj.isValid() ) {

                $continueButton.toggleClass( "disabled", false );
                $.proxy( updateUserDetails, view )( $form );

              } else {

                $continueButton.toggleClass( "disabled", true );

              }
            };

            // Initial validation of form to update the state of the continue button.
            refreshButtonValidation();

            // Bind button validation state to form change event.
            $form.keyup( refreshButtonValidation );


          } );

          $ticketModal.on( "hide.bs.modal", function( e ) {

            if (view.committing) {
              return e.preventDefault();
            }

            $.proxy( updateUserDetails, view )( $modalContent );

          } );

          $ticketModal.on( "hidden.bs.modal", function( e ) {

            view.modalCleanup( $ticketModal );

          } );

          $ticketModal.modal( {
             show: true
          } );

        },

        discardAllOp: function(event) {
            Server.process("abort", "user", {});
        },

        discardAllTriggered: function() {

          var $ticketModal = this.$ticketModal,
              $modalContent = $ticketModal.find( ".modal-content" ),
              discardAll = this.discardAllOp,
              view = this;

          $modalContent.html( Handlebars.templates.discardModal() );

          $ticketModal.on( "show.bs.modal", function( e ) {

            var continueButton = $ticketModal.find( ".continue" );

            continueButton.click( function( evt ) {

              discardAll();

              $ticketModal.modal('hide');
              return evt.preventDefault();

            } );

          } );

          $ticketModal.on( "hidden.bs.modal", function( e ) {

            view.modalCleanup( $ticketModal );

          } );

          $ticketModal.modal({
             show: true
          });
        }

    });

})(ticketbox, ticketbox.module("ticket"));

/**
 * Body Module
 * Handles general changes applied to the body.
 */
(function(ticketbox, Body) {

    // Shorthands
    var app = ticketbox.app;

    Body.Model = Backbone.Model.extend({
        defaults: {
            userLevel: "unknown",
            modal: {
                prompt: false,
                seen: false,
                content: null,
                callbacks: null
            },
            guestPrompt: false

        },

        validate: function(attrs, options) {
            var userLevels = ["guest","user","admin", "unknown"];
            if (! _.contains(userLevels, attrs.userLevel)) {
                return "Invalid user level!";
            }
            if (attrs.modal) {
                var valid = attrs.modal.hasOwnProperty("prompt") &&
                    attrs.modal.hasOwnProperty("seen") &&
                    attrs.modal.hasOwnProperty("content") &&
                    attrs.modal.hasOwnProperty("callbacks");
                if (! valid) {
                    return "Modal not valid.";
                }
            }
        }
    });

    // Create global body model
    app.bodyModel = new Body.Model();

    Body.View = Backbone.View.extend({
        el: "body",

        resizeModalHandler: function() {
          var modal = this.$modal;
          var height = $(window).height();
          var width = $(window).width();
        },

        handleModal: function() {
          var $ticketModal = this.$el.find( "#ticket-modal" ),
              modalDesc = app.bodyModel.get("modal"),
              $modalContent = $ticketModal.find( ".modal-content" ),
              bodyView = this,
              modalObject = app.bodyModel.get("modal"),
              loginPromptHandlers =
              ensureCleanup =
              modalEventBind = null;

          if (!modalDesc.seen && modalDesc.prompt) {

            this.modalCleanup( $ticketModal );
            $modalContent.html( modalDesc.content );

            modalEventBind = function bindEvents(handlers) {
                _.each(handlers, function(value, key, list) {
                    $ticketModal.on(key, value);
                } );
            };

            ensureCleanup = function forceModalCleanup(func){
                return function(e) {
                    var result = null;
                    if (func) {
                        result = func(e);
                    }
                    bodyView.modalCleanup( $ticketModal );
                    return result;
                };
            };

            loginPromptHandlers = {
                "show.bs.modal": function(e) {
                    var $guestButton = $modalContent.find("a.guest");

                    $guestButton.click( function() {

                        $ticketModal.data( "dismissed", true );
                        $("#ticket-modal").modal( "hide" );

                    });
                },
                "hide.bs.modal": function(e) {
                    if ( ! $("#ticket-modal").data("dismissed") ) {
                        console.log("Oh no you didn't!");
                        return false;
                    }
                },
                "hidden.bs.modal": function() {

                    modalDesc.seen = true;
                    bodyView.modalCleanup( $ticketModal );
                }

            };

            if ( ! (modalObject.callbacks instanceof Object) ) {
                modalEventBind(loginPromptHandlers);
            } else {
                if(modalObject.callbacks.hasOwnProperty("hidden.bs.modal")) {
                    modalObject.callbacks["hidden.bs.modal"] = ensureCleanup(modalObject.callbacks["hidden.bs.modal"]);
                } else {
                   modalObject.callbacks["hidden.bs.modal"] = ensureCleanup();
                }
                modalEventBind(modalObject.callbacks);
            }

            $ticketModal.modal( {
             show: true
            } );

          } else {
            this.closeModal();
          }

        },

        modalCleanup: function( $modal ) {

          $modal.off( "show.bs.modal show.bs.modal" );
          $modal.off( "hide.bs.modal hidden.bs.modal" );
          $modal.off( "loaded.bs.modal" );
          $modal.data( "dismissed", false );

        },

        closeModal: function() {
          var $ticketModal = this.$el.find( "#ticket-modal" );
          this.modalCleanup( $ticketModal );
          $ticketModal.modal( "hide" );
        },

        hookEvents: function() {
            this.listenTo(app.bodyModel, 'change:modal', this.handleModal);
        },

        initialize: function() {
            this.hookEvents();
        }

    });


})(ticketbox, ticketbox.module("body"));

/**
 * Modules for PidSearch
 */
(function(ticketbox, PidSearch) {

    // Shorthands
    var app = ticketbox.app;
    var bodyModel = ticketbox.app.bodyModel;

    //Dependencies
    var Server = ticketbox.module("server");


    PidSearch.Result = Backbone.Model.extend({

        idAttribute: "pid",

        defaults: {
            complete: false
        },

        isPartial: function() {
            return !( this.has("cname") && this.has("name"));
        },

        updateState: function() {
            this.set({complete: ! this.isPartial()});
        },

        initialize: function() {
            this.on("change", this.updateState, this);
        }

    });

    PidSearch.ResultView = Backbone.View.extend({
        tagName: 'li',

        template: Handlebars.compile("{{#complete}}[{{ pid }}] {{ name }} - {{ cname }}{{/complete}}"),

        initialize: function() {
            this.listenTo(this.model, "destroy", this.destroyResult);
            this.listenTo(this.model, "change:complete", this.render);
        },

        render: function() {
            this.$el.html(this.template(this.model.toJSON()));
            return this;
        },

        destroyResult: function() {
            var element = this;
            this.$el.hide(400, function() {
                element.remove();
            });
        }
    });

    PidSearch.Results = Backbone.Collection.extend({
        model: PidSearch.Result,

        partialResults: function() {
            var partialResults = this.filter(function(result) {
                return result.isPartial();
            }, this);

            return partialResults;
        },

        getPartialsLoadList: function(step) {
            var partials = this.partialResults();
            var loadList = [];

            if (partials.length > 0) {
                if (partials.length - step > 0) {
                    loadList = _.first(partials, step);
                } else {
                    loadList = partials;
                }
                return _.map(loadList, function(item, key) {
                    return item.get("pid");
                });
            } else {
                return loadList;
            }

        }
    });

    PidSearch.ResultsListView = Backbone.View.extend({
        tagName: 'div',

        attributes: {
            id: "results-frame"
        },

        initialize: function() {
            this.listenTo(this.model, 'add', this.addOne);
            this.listenTo(this.model, 'reset', this.render);
            this.listenTo(this.model, 'change:complete', this.changed);
            this.createNodes();
        },

        createNodes: function() {
            this.$list = $("<ul></ul>").addClass("pid-list unstyled slidee").appendTo(this.el);
            this.init();
        },

        addOne: function(result) {
            var view = new PidSearch.ResultView({model: result});
            this.$list.append(view.render().el);
            this.changed();
        },

        render: function() {
            this.$list.html('');
            this.init();
            this.model.each(this.addOne, this);
            return this;
        },

        changed: function() {
            this.frame.reload();
        },

        init: function() {
            var panel = this.$el;
            this.frame = new Sly(this.$el, {
                itemNav: 'basic',
                itemSelector: 'li',
                scrollBy: 20,
                scrollSource: panel,
                speed: 100,
                easing: 'easeOutQuart',
                dynamicHandle: 1,
                dragHandle: 1,
                clickBar: 1,
                mouseDragging: 1,
                touchDragging: 1,
                releaseSwing: 1

            }).init();
        }

    });

    PidSearch.SearchModel = Backbone.Model.extend({

        defaults: function() {
            return {
                "results": new PidSearch.Results(),
                "incrementStep": 5,
                "fullyLoaded": false
            };
        },

        initialize: function() {

        },

        searchPerson: function(query) {
            var options = {
                success: this.searchSuccess,
                error: this.searchError,
                context: this
            };
            Server.search("pid", { query: query }, options);
        },

        searchSuccess: function(data, status, jqXHR) {
            var resultsColl = this.get("results");
            if (data instanceof Array && data.length > 0) {
                resultsColl.reset(data);
                this.loadPartials();
                this.set({ fullyLoaded: false });
                app.debug && console.log("[Search Model] Success! Contents of collection: " + JSON.stringify(resultsColl.toJSON()));
            }
        },

        searchError: function(jqXHR, status, error) {
            app.debug && console.error("[Search Model] jqXHR: " + JSON.stringify(jqXHR) + ", status: " + status + ", error: " + error);
        },

        dispatchDetailsRequest: function(loadList) {
            var options = {
                success: this.loadPartialsSuccess,
                error: this.loadPartialsError,
                context: this
            };
            Server.search("pid", { pids: loadList }, options);
        },

        loadPartials: function() {
            var step = this.get("incrementStep");
            var loadList = this.get("results").getPartialsLoadList(step);

            if (loadList.length > 0) {
                this.dispatchDetailsRequest(loadList);
            } else {
                this.set({ fullyLoaded: true });
            }
        },

        loadPartialsSuccess: function(data, status, jqXHR) {
            var resultsColl = this.get("results");
            if (data instanceof Array && data.length > 0) {
                resultsColl.add(data, {merge: true});
                app.debug && console.log("[Search Model] Success, partials loaded: " + JSON.stringify(resultsColl.toJSON()));
            }
        },

        loadPartialsError: function(jqXHR, status, error) {
            app.debug && console.error("[Search Model] ERROR: Partials failed to load - jqXHR: " + JSON.stringify(jqXHR) + ", status: " + status + ", error: " + error);
        }

    });


    PidSearch.SearchInterface = Backbone.View.extend({
        tagName: 'div',

        className: "bsw",

        template: "<div class=\"modal-header\"><h1>Search for a Person</h1></div><form class='form-search'><input type='text' class='input-medium search-query'><button type='submit' class='btn search'>Search People</button></form><div class=\"modal-body\"></div><div class=\"modal-footer\"><button class=\"btn\" data-dismiss=\"modal\">Close</button><button class=\"btn btn-primary\">Save changes</button></div>",

        events: {
            "click .btn.search": "performSearch"
        },

        initialize: function() {
            this.resultsListView = new PidSearch.ResultsListView({model: this.model.get("results")});
            this.$el.html(this.template);
            this.unbindFormSubmitEvents(this.$el);
        },

        unbindFormSubmitEvents: function($el) {
            $el.submit(function() {
                 $('input[type=submit]', this).attr('disabled', 'disabled');
                return false;
            });
        },

        render: function() {
            $(".modal-body").html(this.resultsListView.render().el);
            return this;
        },

        performSearch: function(event) {
            var query = this.$(".search-query").val();
            app.debug && console.log(query);
            if(query.length > 1) {
                this.model.searchPerson(query);

            }

        },

        displaySearchModal: function() {
            this.searchModal = {modal: {
                seen: false,
                prompt: true,
                content: this.render().el,
                callbacks: null
            }};
            bodyModel.set(this.searchModal);
        }

    });

})(ticketbox, ticketbox.module("PidSearch"));


/**
 * On Document Ready
 */
jQuery(function($) {

    var Ticket = ticketbox.module("ticket"),
        Body = ticketbox.module("body"),
        app = ticketbox.app,
        ticketView = new Ticket.View(),
        bodyView = new Body.View(),
        $personalDetails = $("#hepdata"),
        pathSlugs = window.location.pathname.split('/'),
        $contactTrigger = $(".contactTrigger"),
        jsBootstrapper =
        disabledHandler =
        contactModalInit =
        disableLinks =
        updater = null;


    jsBootstrapper = function jsBootstraper($el) {
        // Check if element selected, non-false

        if ($el.html()) {
            var data = JSON.parse(_.unescape($el.html()));
            if (data.hasOwnProperty('backbone')) {
                jQuery.globalEval(data.backbone);
            }
            if (data.hasOwnProperty('other')) {
                jQuery.globalEval(data.other);
            }
        }
    };

    disabledHandler = function disabledHandler(event) {
        event.preventDefault();
        return false;
    };

    disableLinks = function disableLinks($el) {
        $el.attr('disabled', 'disabled');
        $el.live("click", disabledHandler);
    };


    // Bootstrap data from server
    jsBootstrapper($("#jsbootstrap"));

    // Window focus event binding
    updater = (function() {
        app.hasFocus = true;
        $(window).focus(function(event) {
            app.hasFocus = true;
            var successFocus = function() {
                app.debug && console.log("[Focus Update] Update succeeded.");
            };

            var sureUpdate = ticketbox.sureUpdate();
            app.userops.fetch({"on": 'user', "error": sureUpdate, "success": successFocus});
            app.debug && console.log("Focus update triggered.");
        }).blur(function(event) {
            app.hasFocus = false;
            app.debug && console.log("Focus lost.");
        });
    })();

    contactModalInit = function contactModalInit(e) {
        var bodyModel = ticketbox.app.bodyModel,
            modalContent = Handlebars.templates.contactModal(),
            modal =
            callbacks = null;

        callbacks = {
            "show.bs.modal": function(e) {
                var $modal = $("#ticket-modal"),
                    $form = $("form#contactForm"),
                    $submit = $("a.submit"),
                    $successMsg = $(".msg-success"),
                    $errorMsg = $(".msg-error"),
                    $defaultMsg = $(".msg-default"),
                    parsleyObj = null;

                parsleyObj = $form.parsley();

                $submit.click(function (e) {
                    var isValid = parsleyObj.validate(),
                        formSerialised = $form.serializeArray();

                    formSerialised.push({name: "send_message", value: ""});
                    formSerialised.push({name: "last_page_visited", value: window.location.toString()});

                    if (isValid) {
                        $defaultMsg.toggleClass("hidden", true);
                        $form.toggleClass("hidden", true);
                        $.ajax({
                            url: "/author/claim/action",
                            action: "POST",
                            data: formSerialised,
                            success: function() {
                                $successMsg.toggleClass("hidden", false);
                                $errorMsg.toggleClass("hidden", true);
                                $modal.find(".modal-header>.modal-title").text("Thank You");
                            },
                            error: function() {
                                $successMsg.toggleClass("hidden", true);
                                $errorMsg.toggleClass("hidden", false);
                                $modal.find(".modal-header>.modal-title").text("Try again later");
                            },
                            complete: function() {
                                $modal.find(".modal-footer>a.submit").remove();
                                $modal.find(".modal-footer>a.back").text("Close");
                            }
                        });
                    }
                    return e.preventDefault();
                });

            }
        }

        modal = {
          prompt: true,
          shown: false,
          content: modalContent,
          callbacks: callbacks
        };
        bodyModel.set( { modal: modal } );
        return e.preventDefault();
    };

    if ($personalDetails) {
      ticketbox.personalDetails($personalDetails);
    }

    if ($contactTrigger) {
       $contactTrigger.click(contactModalInit);
    }

});

$(document).ready(function() {

    var BoxLoader = function BoxLoader( num, minTime ) {

      var init, callbacks, boxStates, requestAllowed, dispatch, runHook,
          displayLoading;

      this.pid = $( "div[data-box-pid]" ).data( "boxPid" );
      this.boxes = _.toArray( $( "div[data-box-source]" ) );
      this.hooks = {};

      this.minTime = minTime || 5000; // Default to 5 seconds.
      this.concurrentRequests = num || 8; // Default to 8.
      this.baseUrl = "/author/profile/";

      displayLoading = function showLoadingSpinner( box ) {

         var opts = {

           lines: 11, // The number of lines to draw
           length: 3, // The length of each line
           width: 3, // The line thickness
           radius: 8, // The radius of the inner circle
           corners: 1, // Corner roundness (0..1)
           rotate: 0, // The rotation offset
           direction: 1, // 1: clockwise, -1: counterclockwise
           color: '#69C', // #rgb or #rrggbb or array of colors
           speed: 2.1, // Rounds per second
           trail: 41, // Afterglow percentage
           shadow: false, // Whether to render a shadow
           hwaccel: false, // Whether to use hardware acceleration
           className: 'spinner', // The CSS class to assign to the spinner
           zIndex: 2e9, // The z-index (defaults to 2000000000)
           top: 'auto', // Top position relative to parent in px
           left: 'auto' // Left position relative to parent in px

         };

        var spinner = new Spinner( opts ).spin( box );

        $( box ).data("spinner", spinner);

      };

      init = function initBoxData( obj ) {

        _.each( obj.boxes, function( item ) {

          var $item = $( item );
          $item.data( {
            "boxDispatched": false,
            "boxLoaded": false,
            "boxDispatchTimestamp": 0

          } );

          displayLoading( item );

        } );

      };

      runHook = function runHook( $box, obj ) {

        var source = $box.data( "boxSource" );

        if ( obj.hooks.hasOwnProperty( source ) ) {

          obj.hooks[ source ]( $box );

        }

        if ( obj.hooks.hasOwnProperty( "defaultHook" ) ) {
          obj.hooks.defaultHook( $box );
        }

      };

      callbacks = function getBoxCallbacks( $box, loader ) {

        return {

          "success": function ( data, textStatus, jqXHR ) {

            if ( data.hasOwnProperty( "status" ) && data.status ) {

              // Insert HTML into DOM.
              if ( data.hasOwnProperty( "html" ) ) {
                $box.html( data.html );
              }

              // Mark box as loaded.
              $box.data( "boxLoaded", true );

            } else {
              $box.data( "boxLoaded", false );

            }

          },

          "error": function ( jqXHR, textStatus, errorThrown ) {

              $box.data( "boxLoaded", false );


          },

          "complete": function ( jqXHR, textStatus ) {
            var boxStates = loader.loadingState(loader),
                delayedLoad = boxStates.delayedLoad.length > 0 && boxStates.toLoad.length < 1;

            // If the box didn't load, reset the dispatched flag.
            if ( $box.data( "boxLoaded" ) === false ) {
              $box.data( "boxDispatched", false );

            } else {

              runHook( $box, loader );

            }

            // Invoke loader to process any remaining boxes.
            loader.load();

            // Use timer to give rate limited boxes a chance to load.
            if (delayedLoad) {
              setTimeout($.proxy(loader.load, loader), loader.minTime);
            }

          }
        };

      };

      requestAllowed = function checkIfRequestAllowed( box, time ) {

        var $box = $( box ),
            delta = ( new Date() ).getTime() - $box.data( "boxDispatchTimestamp" );

        return delta > time;

      };

      this.loadingState = function getLoadingState( obj ) {

        var inProgress = 0, queue, delayed = null;

        // Generate list of boxes to load
        queue = _.filter( obj.boxes, function( box ) {
          var toLoad = false,
              $box = $( box );

          // Count number requests currently in progress.
          if ( $( box ).data( "boxDispatched" ) && ! $( box ).data( "boxLoaded" ) ) {

            inProgress ++;

          }

          toLoad = ! $box.data( "boxLoaded" ); // Boxes that aren't loaded.
          toLoad &= ! $box.data( "boxDispatched" ); // And boxes that aren't dispatched already.
          toLoad &= requestAllowed( box, obj.minTime ); // And if enough time has passed.

          return toLoad;

        });

        // Generate list of boxes that should load but are time limited
        delayed = _.filter( obj.boxes, function( box ) {
          var toLoad = false,
              $box = $( box );

          // Count number requests currently in progress.
          if ( $( box ).data( "boxDispatched" ) && ! $( box ).data( "boxLoaded" ) ) {

            inProgress ++;

          }

          toLoad = ! $box.data( "boxLoaded" ); // Boxes that aren't loaded.
          toLoad &= ! $box.data( "boxDispatched" ); // And boxes that aren't dispatched already.
          toLoad &= ! requestAllowed( box, obj.minTime );

          return toLoad;

        });

        return {
          "inProgressCount": inProgress,
          "toLoad": queue,
          "delayedLoad": delayed
        };

      };

      dispatch = function requestBoxContents( box, obj ) {

        var $box = $( box ),
            source = $box.data( "boxSource" ),
            requestConfig = callbacks( $box, obj );

        requestConfig.url = obj.baseUrl + source;
        requestConfig.type = "POST";
        requestConfig.data = { jsondata: JSON.stringify( { personId: obj.pid } ) };

        $box.data( {

          "boxDispatchTimestamp": (new Date()).getTime(),
          "boxDispatched": true

        } );

        $.ajax(requestConfig);

      };

      this.addHook = function addSourceHook( mapping ) {

        _.extend( this.hooks, mapping );

      };

      this.load = function loadBoxes() {

        var loader = this,
            state = this.loadingState( this ),
            inProgress = state.inProgressCount,
            queue = state.toLoad,
            qtyToLoad = ( this.concurrentRequests - inProgress ),
            canLoad = qtyToLoad > 0;


        if ( canLoad ) {
          var randSample = _.sample( queue, qtyToLoad );

          _.map( randSample, function(item) {
            dispatch( item, loader );

          });
        }
      };

      init( this );


    };

    var loader = new BoxLoader();
    loader.addHook( {

      "publications-list": function ( $box ) {

        $(".pub-tabs a:first").tab('show');
        MathJax.Hub.Queue( [ "Typeset", MathJax.Hub, $box.get(0) ] );

      },
      "defaultHook": function ( $box ) {
        $box.find('[class^=more-]').hide();
        $box.find('[class^=lmore]').each(function() {
            $(this).click(function () {
              var link_class = $(this).prop("className");
              var content = $("." + "more-" + link_class);
              if (content.hasClass("hidden")) {
                  content.removeClass("hidden").slideDown();
                  $(this).html("<img src='/img/aid_minus_16.png' alt='hide information' width='11' height='11'> less");
              }
              else {
                  content.addClass("hidden").slideUp();
                  $(this).html("<img src='/img/aid_plus_16.png' alt='toggle additional information.' width='11' height='11'> more");
              }
              return false;
            });
        });
      },
      "hepnames": ticketbox.personalDetails
    } );

    loader.load();

	$("#orcid").on("click", "#orcid_suggestion", function(event) {
		var target = $(event.target);
		var data = {
			pid: target.find(".pid").text(),
			orcid: $("#suggested_orcid").val()
		};

		var successCallback = function () {
			alert("Your suggestion was succesfully sent!");
		};

		var errorCallback = function () {
			alert("Your suggestion was not sent! The ORCiD is not valid.");
		};

		$.ajax({
			dataType: 'json',
			type: 'POST',
			url: '/author/manage_profile/suggest_orcid_ajax',
			data: {jsondata: JSON.stringify(data)},
			success: successCallback,
			error: errorCallback,
			async: true
		});

		event.preventDefault();
		return false;
	});

    // Control 'view more info' behavior in search
    $('[class^=more-]').hide();
    $('[class^=mpid]').click(function() {
        var $this = $(this);
        var x = $this.prop("className");
        $('.more-' + x).toggle();
        var toggleimg = $this.find('img').attr('src');

        if (toggleimg == '../img/aid_plus_16.png') {
            $this.find('img').attr({src:'../img/aid_minus_16.png'});
            $this.closest('td').css('padding-top', '15px');
        } else {
            $this.find('img').attr({src:'../img/aid_plus_16.png'});
            $this.closest('td').css('padding-top', '0px');
        }
        return false;
    });

    /////////////////////////////////////////////
    // ** Profile page specific invocation. ** //
    /////////////////////////////////////////////

    if( $("#profile-page").length > 0 ) {

      // Activate tabbing on publications box.
      $("ul.pub-tabs > li > a[data-toggle='tab']").on('shown', function(e) {
        $(e.target).toggleClass("pub-tab-active", true);
        $(e.relatedTarget).toggleClass("pub-tab-active", false);
      });

      $("#recomputeProfile").click( function (e) {

        $.ajax({
            url: window.location.origin + window.location.pathname,
            data: {recompute: 1},
            type: 'POST',
            complete: function( data, textStatus, jqXHR ) {
                setTimeout(function() {
                    location.reload();
                }, 100);
            }
        });

        return e.preventDefault();

      } ).popover({
        html: true,
        placement: "bottom",
        trigger: "hover",
        content: $("#recomputeProfile").data("baiProfileMsg")
      });

      $("#recomputeProfile-disabled").popover({
        html: true,
        placement: "bottom",
        trigger: "hover",
        content: $("#recomputeProfile-disabled").data("baiProfileMsg")
      });


    } else {
        // Initialize DataTable
        $('.paperstable').dataTable({
            "bJQueryUI": true,
            "sPaginationType": "full_numbers",
            "aoColumns": [
                { "bSortable": false,
                  "sWidth": "" },
                { "bSortable": false,
                  "sWidth": "" },
                { "sWidth": "" },
                { "sWidth": "" },
                { "sWidth": "" },
                { "sWidth": "120px" },
                { "sWidth": "320px" }
            ],
            "aLengthMenu": [500],
            'iDisplayLength': 500,
            "fnDrawCallback": function() {
                $('.dataTables_length').css('display','none');
            }
        });

        $('.reviewstable').dataTable({
            "bJQueryUI": true,
            "sPaginationType": "full_numbers",
            "aoColumns": [
                { "bSortable": false,
                  "sWidth": "" },
                { "bSortable": false,
                  "sWidth": "" },
                { "bSortable": false,
                  "sWidth": "120px" }
            ],
            "aLengthMenu": [500],
            'iDisplayLength': 500,
            "fnDrawCallback": function() {
                $('.dataTables_length').css('display','none');
            }
        });

        // search box
        if ( $('#personsTable').length ) {
            // bind retrieve papers ajax request
            $('[class^=mpid]').on('click', function(event){
                if ( !$(this).siblings('.retreived_papers').length) {
                    var pid = $(this).closest('tr').attr('id').substring(3); // e.g pid323
                    var data = { 'requestType': "getPapers", 'personId': pid.toString()};
                    var errorCallback = onRetrievePapersError(pid);
                    $.ajax({
                        dataType: 'json',
                        type: 'POST',
                        url: '/author/claim/search_box_ajax',
                        data: {jsondata: JSON.stringify(data)},
                        success: onRetrievePapersSuccess,
                        error: errorCallback,
                        async: true
                    });
                    event.preventDefault();
                }
            });
            // create ui buttons
            var columns = {};
            $('#personsTable th').each(function(index) {
                columns[$(this).attr('id')] = index;
            });
            var targets = [columns['IDs'], columns['Papers'], columns['Link']];
            if (columns['Action'] !== undefined) {
               targets.push(columns['Action']);
            }
            var pTable = $('#personsTable').dataTable({
                "bJQueryUI": true,
                "sPaginationType": "full_numbers",
                "aoColumnDefs": [
                    { "bSortable": false, "aTargets": targets },
                    { "bSortable": true, "aTargets": [columns['Number'], columns['Identifier'], columns['Names'], columns['Status']] },
                    { "sType": "numeric", "aTargets": [columns['Number']] },
                    { "sType": "string", "aTargets": [columns['Identifier'], columns['Names'], columns['Status']] }
                    ],
                "aaSorting": [[columns['Number'],'asc']],
                "aLengthMenu": [[5, 10, 20, -1], [5, 10, 20 , "All"]],
                "iDisplayLength": 5,
                "oLanguage": {
                    "sSearch": "Filter: "
                }
            });
            // draw first page
            onPageChange();
            // on page change
            $(pTable).bind('draw', function() {
                onPageChange();
            });
        }

        if ( $('.idsAssociationTable').length ) {
            var idTargets = [1,2];
            if ( $('#idsAssociationTableClaim').length ) {
                idTargets.push(3);
            }
            $('.idsAssociationTable').dataTable({
                "bJQueryUI": true,
                "sPaginationType": "full_numbers",
                "aoColumnDefs": [
                    { "bSortable": true, "aTargets": [0] },
                    { "bSortable": false, "aTargets": idTargets },
                    { "sType": "string", "aTargets": [0] }
                    ],
                "aaSorting": [[0,'asc']],
                "iDisplayLength": 5,
                "aLengthMenu": [5, 10, 20, 100, 500, 1000],
                "oLanguage": {
                    "sSearch": "Filter: "
                }
            });
            $('.idsAssociationTable').siblings('.ui-toolbar').css({ "width": "45.4%", "font-size": "12px" });
        }

        if (typeof gMergeProfile !== 'undefined' ) {
            // initiate merge list's html from javascript/session
            $('#primaryProfile').parent().parent().replaceWith('<tr><td><img src=\"' + isProfileAvailable(gMergeProfile[1]).img_src +
             '\" title=\"' + isProfileAvailable(gMergeProfile[1]).message + '\"></td><td><a id=\"primaryProfile\" href=\"profile/' +
            gMergeProfile[0] + '\" target=\"_blank\" title=\"' + isProfileAvailable(gMergeProfile[1]).message + '\" >' +
             gMergeProfile[0] + '</a></td><td id="primaryProfileTd">primary profile</td><td></td><tr>');
            $('.addToMergeButton[name="' + gMergeProfile[0] + '"]').prop('disabled','disabled');
            for(var profile in gMergeList) {
                createProfilesHtml(gMergeList[profile]);
                $('.addToMergeButton[name="' + gMergeList[profile][0] + '"]').prop('disabled','disabled');
            }
            updateMergeButton();
            $('#mergeButton').on('click', function(event){
                $(this).before('<input type="hidden" name="primary_profile" value="' + gMergeProfile[0] + '" />');
                for(var profile in gMergeList) {
                    $(this).before('<input type="hidden" name="selection" value="' + gMergeList[profile][0] + '" />');
                }
            //event.preventDefault();
            });
            $('.addToMergeButton').on('click', function(event) {
                onAddToMergeClick(event, $(this));
            });

            $("form>#mergeButton").parent().on("submit", function(event) {
                var bodyModel = ticketbox.app.bodyModel,
                    $form = $(this),
                    primaryCname = $form.find("input[name='primary_profile']").first().val(),
                    modalContent = Handlebars.templates.mergeConfirmation(),
                    modal =
                    callbacks = null;

                callbacks = {
                    "show.bs.modal": function(e) {
                        var $confirmButton = $(e.currentTarget).find("a.confirm"),
                            $modal = $("#ticket-modal");

                        $confirmButton.click( function() {
                            $.ajax({
                                url: "/author/claim/action",
                                data: $form.serialize(),
                                success: function (data, status, jqXHR) {
                                    $modal.find(".modal-body").html("<p>Profile merge will be processed soon.</p>");
                                    $modal.find(".modal-header>.modal-title").text("Thank You");
                                    $modal.find(".modal-footer>a.confirm").remove();
                                    $modal.find(".modal-footer>a.back").text("Close");
                                    $form.data({"mergeConfirmed": true});
                                },
                                error: function (jqXHR, status, data) {
                                    $modal.modal("hide");
                                }
                            });
                        });
                    },
                    "hidden.bs.modal": function(e) {
                        if ($form.data("mergeConfirmed")) {
                            window.location.pathname = "/author/profile/" + primaryCname;
                        }
                    }
                };

                modal = {
                    prompt: true,
                    shown: false,
                    content: modalContent,
                    callbacks: callbacks
                };
                if (! $form.data("mergeConfirmed")) {
                    bodyModel.set( { modal: modal } );
                    return event.preventDefault();
                }
            });

        }

        // Activate Tabs
        $("#aid_tabbing").tabs();

        // Style buttons in jQuery UI Theme
        //$(function() {
        //	$( "button, input:submit, a", ".aid_person" ).button();
        //	$( "a", ".demo" ).click(function() { return false; });
        //});

        // Show Message
        $(".ui-alert").fadeIn("slow");
        $("a.aid_close-notify").each(function() {
        $(this).click(function() {
                $(this).parents(".ui-alert").fadeOut("slow");
                return false;
            } );
        });

        // Set Focus on last input field w/ class 'focus'
        $("input.focus:last").focus();

        // Select all
        $("A[href='#select_all']").click( function() {
            $('input[name=selection]').attr('checked', true);
            return false;
        });

        // Select none
        $("A[href='#select_none']").click( function() {
            $('input[name=selection]').attr('checked', false);
            return false;
        });

        // Invert selection
        $("A[href='#invert_selection']").click( function() {
            $('input[name=selection]').each( function() {
                $(this).attr('checked', !$(this).attr('checked'));
            });
            return false;
        });

        $("#ext_id").keyup(function(event) {
            var textbox = $(this);

            if (! (event.ctrlKey || event.altKey)) {
                textbox.val(function() {
                    return $(this).val().replace(/\s/g, '');
                });
            }

            var label_text = classifyInput(textbox.val());
            var label_changed = labelChanged(label_text);

            if (label_changed) {
                $("#type-label").fadeOut(500, function() {
                        $(this).text(label_text).fadeIn(500);
                });
            }

            console.log("Performed Client-Side Sanitation Check")
            console.log($(this).val());
            console.log("Orcid: " + isORCID($(this).val()));
            console.log("Inspire: " + isINSPIRE($(this).val()));
        });
    }

});

var orcid_regex = /^((?:https?:\/\/)?(?:www.)?orcid.org\/)?((?:\d{4}-){3}\d{3}[\dX]$)/i;

function isORCID(identifier) {
    return orcid_regex.test(identifier);
}

function isINSPIRE(identifier) {
    var inspire_regex= /^(INSPIRE-)(\d+)$/i;
    return inspire_regex.test(identifier);
}

function classifyInput(identifier) {
    if(isORCID(identifier)) {
        return "ORCID"
    } else if(isINSPIRE(identifier)) {
        return "INSPIRE"
    } else {
        return "?"
    }
}

var last_label;
function labelChanged(current) {
    if (typeof last_label == 'undefined') {
        last_label = current;
        return true;
    } else if (last_label ==  current) {
        return false;
    } else {
        last_label = current;
        return true;
    }
}

function onPageChange() {
    $('[class^="emptyName"]').each( function(index){
                var pid = $(this).closest('tr').attr('id').substring(3); // e.g pid323
                var data = { 'requestType': "getNames", 'personId': pid.toString()};
                var errorCallback = onGetNamesError(pid);
                $.ajax({
                    dataType: 'json',
                    type: 'POST',
                    url: '/author/claim/search_box_ajax',
                    data: {jsondata: JSON.stringify(data)},
                    success: onGetNamesSuccess,
                    error: errorCallback,
                    async: true
                });
        });

    $('[class^="emptyIDs"]').each( function(index){
                var pid = $(this).closest('tr').attr('id').substring(3); // e.g pid323
                var data = { 'requestType': "getIDs", 'personId': pid.toString()};
                var errorCallback = onGetIDsError(pid);
                $.ajax({
                    dataType: 'json',
                    type: 'POST',
                    url: '/author/claim/search_box_ajax',
                    data: {jsondata: JSON.stringify(data)},
                    success: onGetIDsSuccess,
                    error: errorCallback,
                    async: true
                });
    });

    if (typeof gMergeProfile != 'undefined') {
        $('.addToMergeButton[name="' + gMergeProfile[0] + '"]').prop('disabled','disabled');
        $('.addToMergeButton').on('click', function(event) {
            onAddToMergeClick(event, $(this));
        });
    }
}

function updateMergeButton() {
    if (gMergeList.length)
            $('#mergeButton').removeAttr('disabled');
    else
        $('#mergeButton').attr('disabled','disabled');
}

function onAddToMergeClick(event, button) {
    var profile = button.attr('name').toString();
    var profile_availability = button.siblings('[name="profile_availability"]').val();
    for (var ind in gMergeList) {
        if ( profile == gMergeList[ind][0] ) {
            event.preventDefault();
            return false;
        }
    }

    var data = { 'requestType': "addProfile", 'profile': profile};
    $.ajax({
        dataType: 'json',
        type: 'POST',
        url: '/author/claim/merge_profiles_ajax',
        data: {jsondata: JSON.stringify(data)},
        success: addToMergeList,
        async: true
    });
    event.preventDefault();
}

function addToMergeList(json) {
    if(json['resultCode'] == 1) {
        var profile = json['addedPofile'];
        var profile_availability = json['addedPofileAvailability'];
        var inArray = -1;
        for ( var index in gMergeList ){
            if (profile == gMergeList[index][0] ) {
                inArray = index;
            }
        }
        if ( inArray == -1 && gMergeProfile[0] !== profile) {
            gMergeList.push([profile, profile_availability]);
            createProfilesHtml([profile, profile_availability]);
            $('.addToMergeButton[name="' + profile + '"]').prop('disabled','disabled');
            updateMergeButton();
        }
    }
}

function removeFromMergeList(json) {
    if(json['resultCode'] == 1) {
        var profile = json['removedProfile'];
        var ind = -1;
        for ( var index in gMergeList ){
            if (profile == gMergeList[index][0] ) {
                ind = index;
            }
        }
        if( ind !== -1) {
            gMergeList.splice(ind,1);
        }
        removeProfilesHtml(profile);
        $('.addToMergeButton[name="' + profile + '"]').removeAttr('disabled');
        updateMergeButton();
    }
}

function setAsPrimary(json) {
    if(json['resultCode'] == 1) {
        var profile = json['primaryProfile'];
        var profile_availability = json['primaryPofileAvailability'];
        removeFromMergeList({'resultCode' : 1, 'removedProfile' : profile});
        var primary = gMergeProfile;
        gMergeProfile = [profile, profile_availability];
        $('.addToMergeButton[name="' + profile + '"]').prop('disabled','disabled');
        addToMergeList({'resultCode' : 1, 'addedPofile' : primary[0], 'addedPofileAvailability': primary[1]});
        $('#primaryProfile').parent().parent().replaceWith('<tr><td><img src=\"' + isProfileAvailable(profile_availability).img_src +
         '\" title=\"' + isProfileAvailable(profile_availability).message + '\"></td><td><a id=\"primaryProfile\" href=\"profile/' +
         profile + '\" target=\"_blank\" title=\"' + isProfileAvailable(profile_availability).message + '\"  >' +
          profile + '</a></td><td id="primaryProfileTd" >' +
          'primary profile</td><td></td></tr>');
    }
}

function createProfilesHtml(profile) {
    var $profileHtml = $('<tr><td><img src=\"' + isProfileAvailable(profile[1]).img_src + '\" title=\"' +
     isProfileAvailable(profile[1]).message + '\"></td><td><a href=\"profile/' + profile[0] + '\" target=\"_blank\"  title=\"' +
     isProfileAvailable(profile[1]).message + '\">' + profile[0] +
     '</a></td><td><a class=\"setPrimaryProfile\" href=\"\" >Set as primary</a></td><td><a class=\"removeProfile\" href=\"\" >'+
     '<img src="/img/wb-delete-item.png" title="Remove profile"></a></td></tr>');
        $('#mergeList').append($profileHtml);
        $profileHtml.find('.setPrimaryProfile').on('click', { pProfile: profile[0]}, function(event){
            var data = { 'requestType': "setPrimaryProfile", 'profile': event.data.pProfile};
            $.ajax({
                dataType: 'json',
                type: 'POST',
                url: '/author/claim/merge_profiles_ajax',
                data: {jsondata: JSON.stringify(data)},
                success: setAsPrimary,
                async: true
            });
            event.preventDefault();
        });
        $profileHtml.find('.removeProfile').on('click', { pProfile: profile[0]}, function(event){
            var data = { 'requestType': "removeProfile", 'profile': event.data.pProfile};
            $.ajax({
                dataType: 'json',
                type: 'POST',
                url: '/author/claim/merge_profiles_ajax',
                data: {jsondata: JSON.stringify(data)},
                success: removeFromMergeList,
                async: true
            });
            event.preventDefault();
        });
}

function isProfileAvailable(availability){
    if( availability === "0"){
        return { img_src : "/img/circle_orange.png",
                 message : 'This profile is associated to a user'
               };
    }
    else{
        return { img_src : "/img/circle_green.png",
                 message : 'This profile is not associated to a user'
               };
    }
}

function removeProfilesHtml(profile) {
    $('#mergeList').find('a[href="profile/' + profile + '"][id!="primaryProfile"]').parent().parent().remove();
}

function onGetIDsSuccess(json){
    if(json['resultCode'] == 1) {
        $('.emptyIDs' + json['pid']).html(json['result']).addClass('retreivedIDs').removeClass('emptyIDs' + json['pid']);

    }
    else {
        $('.emptyIDs' + json['pid']).text(json['result']);
    }
}

function onGetIDsError(pid){
  /*
   * Handle failed 'getIDs' requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var pID = pid;
      $('.emptyIDs' + pID).text('External ids could not be retrieved');
    };
}

function onGetNamesSuccess(json){
    if(json['resultCode'] == 1) {
        $('.emptyName' + json['pid']).html(json['result']).addClass('retreivedName').removeClass('emptyName' + json['pid']);
    }
    else {
        $('.emptyName' + json['pid']).text(json['result']);
    }
}

function onGetNamesError(pid){
  /*
   * Handle failed 'getNames' requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var pID = pid;
      $('.emptyName' + pID).text('Names could not be retrieved');
    };
}

function onRetrievePapersSuccess(json){
    if(json['resultCode'] == 1) {
        $('.more-mpid' + json['pid']).html(json['result']).addClass('retreived_papers');
        $('.mpid' + json['pid']).append('(' + json['totalPapers'] + ')');
    }
    else {
        $('.more-mpid' + json['pid']).text(json['result']);
    }
}

function onRetrievePapersError(pid){
  /*
   * Handle failed 'getPapers' requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var pID = pid;
      $('.more-mpid' + pID).text('Papers could not be retrieved');
    };
}

function onRetrieveAutoClaimedPapersSuccess(json) {
    if(json['resultCode'] == 1) {
        $('#autoclaim').replaceWith(json['result']);
    }
    else {
        $('#autoclaim').replaceWith(json['result']);
    }
}

function onRetrieveAutoClaimedPapersError(pid) {
    return function (XHR, textStatus, errorThrown) {
      var pID = pid;
      $('#autoclaim').replaceWith('<span>Error occured while retrieving papers</span>');
    };
}

function showPage(pageNum) {
    $(".aid_result:visible").hide();
    var results = $(".aid_result");
    var resultsNum = results.length;
    var start = (pageNum-1) * gResultsPerPage;
    results.slice( start, start+gResultsPerPage).show();
    var pagesNum = Math.floor(resultsNum/gResultsPerPage) + 1;
    $(".paginationInfo").text("Page " + pageNum + " of " + pagesNum);
    generateNextPage(pageNum, pagesNum);
    generatePreviousPage(pageNum, pagesNum);
}

function generateNextPage(pageNum, pagesNum) {
    if (pageNum < pagesNum ) {
        $(".nextPage").attr("disabled", false);
        $(".nextPage").off("click");
        $(".nextPage").on("click", function(event) {
            gCurPage = pageNum+1;
            showPage(gCurPage);
        });
    }
    else {
        $(".nextPage").attr("disabled", true);
    }
}

function generatePreviousPage(pageNum, pagesNum) {
    if (pageNum > 1 ) {
        $(".previousPage").attr("disabled", false);
        $(".previousPage").off("click");
        $(".previousPage").on("click", function(event) {
            gCurPage = pageNum-1;
            showPage(gCurPage);
        });
    }
    else {
        $(".previousPage").attr("disabled", true);
    }
}

function toggle_claimed_rows() {
    $('img[alt^="Confirmed."]').parents("tr").toggle()

    if ($("#toggle_claimed_rows").attr("alt") == 'hide') {
        $("#toggle_claimed_rows").attr("alt", 'show');
        $("#toggle_claimed_rows").html("Show successful claims");
    } else {
        $("#toggle_claimed_rows").attr("alt", 'hide');
        $("#toggle_claimed_rows").html("Hide successful claims");
    }
}
