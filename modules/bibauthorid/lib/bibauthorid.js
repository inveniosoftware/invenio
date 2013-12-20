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
                return modules[name]
            }

            return modules[name] = { Views : {} }
        };
    }(),

    app: { debug: false, hasFocus: false },

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
                    }
                },
                get_status: function() {
                    return {
                        'on': model.get('on')
                    }
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
                    params.url = "/author/search_ajax/list/" + _.escape(data["query"]);
                    Backbone.ajax(params);
                } else if (data.hasOwnProperty("pids")) {
                    params.url = "/author/search_ajax/details";
                    params.data.jsondata = JSON.stringify({pids: data["pids"]});
                    Backbone.ajax(params);
                } else {
                    app.debug && console.error("[Server Search] ERROR: No search configuration data.")
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

    var opsource = "<div class=\"row-fluid\">{{#action}}" +
        "<div class=\"span2 action {{ classes }}\">{{ action }}</div>" +
        "<div class=\"span9\">{{/action}}<div class=\"title\"><a href=\"{{ rec_link }}\" target=\"_blank\">{{rec_title}}</a></div>For profile <a href=\"{{ profile_link }}\">{{ profile }}</a>{{#editable}}, known by: <select>{{#bibrefs}}<option value=\"{{ bibref }}\">{{ sig }}</option>{{/bibrefs}}<option class=\"nobibref\" value=\"\">I don't know</option></select>{{/editable}}</div>" +
        "<div class=\"span1\"><div class=\"op-buttons btn-group btn-group-vertical\"><button class=\"btn btn-small op-btn removeOp\" type=\"button\">Discard</button></div></div>" +
        "</div>";
    var template = Handlebars.compile(opsource);

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
            this.set({complete: this.isComplete() });
            this.listenTo(this, "change", function() { app.debug && console.log(this.id + " has changed!"); this.set({complete: this.isComplete() }); });

        },

//        validate: function(attrs, options) {
//            if (attrs.bibref == null) {
//                return "No bibref!"
//            }
//        },

        getTarget: function() {
            return this.get('on');
        },

        setBibref: function(bibref) {
            var bibrefRegex = /\d+:\d+/;
            if (bibref == "") {
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
                return "Forget"
            } else {
                return "Unknown"
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
        tagName: "li",

        attributes: {
            class: "hidden"
        },

        events: {
            'click .removeOp': 'removeOperation',
            'click select': 'bibrefSelected'
        },

        initialize: function(){
            app.debug && console.log("Operation View Created!");
            this.listenTo(this.model, "change", this.render);
            this.listenTo(this.model, "destroy", this.destroyOp);
            this.listenTo(this.model, "removeview", this.destroyOp);
            this.listenTo(this.model, "invalid", function() {alert("Did not pass validation!")});

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
                    if (operation['operation'] == "ticketized") {
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
            }

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
    var mainBox = "<div id=\"ticket_status\" class=\"alert alert-info hidden\"></div>";
    var add = "<span id=\"add_form\">Testing Feature ONLY: <form class=\"form-inline\" id=\"debug_form\"> <input type=\"text\" class=\"input-small\" name=\"pid\" placeholder=\"pid\"> <input type=\"text\" name=\"bibrefrec\" class=\"input-small\" placeholder=\"bibrefrec\"> <select id=\"action1\" class=\"input-small\"><option selected=\"selected\" value=\"assign\">assign</option><option value=\"reject\">reject</option></select> <select name=\"on\" class=\"input-small\"><option selected=\"selected\" value=\"user\">user</option><option value=\"autoclaim\">autoclaim</option></select> <button id=\"addButton\">Add</button><button id=\"updateButton\">Update Status</button></form></span>";
    var stats = "<p id=\"stats\">DEBUG: <b>Total items in collection:</b> {{ total }}, <b>Ignored/Complete:</b> {{ igcom }}, <b>Incomplete:</b> {{ incomplete }},  <b>Committed:</b> {{ committed }}, <b>Outcome:</b> {{ outcome }}</p>";
    var buttons = "<button id=\"commitButton\" class=\"btn btn-large btn-primary\" disabled=\"disabled\">Confirm</button><button id=\"abortButton\" class=\"btn btn-large\">Discard All</button>";
    var statstemplate = Handlebars.compile(stats);

    Ticket.Operations = Backbone.Collection.extend({
        model: Operation.Model,

        sync: Server.sync,

        initialize: function() {
            this.listenTo(this, 'change', function(){app.debug && console.log("Collection Changed - " + JSON.stringify(this.toJSON()))});
        },

        completed: function() {
            return this.filter(function(operation) {
                return operation.isComplete() || operation.get("ignored");
            })
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
                if (value.has("execution_result")) {
                    var operation = value.get('execution_result');
                    if (operation['operation'] == "ticketized") {
                        memo['ticketized']++;
                    } else {
                        memo['other']++;
                    }
                    return memo;
                }
            }, result);

        }


    });

    // Create global user operations collection.
    app.userops = new Ticket.Operations();


    Ticket.OperationsView = Backbone.View.extend({
        tagName: "ul",

        attributes: {
            id: "complete",
            class: "op-list unstyled"
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

        commitModalTemplate: Handlebars.compile("<div class=\"modal ow-closed\">" +
            "<div class=\"modal-header\"><h1>{{ title }}</h1></div>" +
            "<div class=\"modal-body\">" +
            "<span class=\"confirm-text\"><p>{{#guest}}Please provide your details to submit your suggestions.<br>{{/guest}}If you have any comments, please fill in the comments box below.</p></span>" +
            "<form class=\"form-horizontal\" novalidate>" +
            "{{#guest}}<div class=\"control-group\"><label class=\"control-label\" for=\"firstName\">First Name</label><div class=\"controls\"><input class=\"input-large\" required=\"true\" data-trigger=\"change keyup focusin focusout\" data-notblank=\"true\" data-required-message=\"This field is required.\" data-validation-minlength=\"1\" data-minlength=\"2\" data-minlength-message=\"Your input is too short.\" type=\"text\" id=\"firstName\" placeholder=\"First Name\" value=\"{{ userDetails.first_name }}\"></div></div>" +
            "<div class=\"control-group\"><label class=\"control-label\" for=\"lastName\">Last Name</label><div class=\"controls\"><input class=\"input-large\" required=\"true\" data-trigger=\"change keyup focusin focusout\" data-notblank=\"true\" data-required-message=\"This field is required.\" data-validation-minlength=\"1\" data-minlength=\"2\" data-minlength-message=\"Your input is too short.\" type=\"text\" id=\"lastName\" placeholder=\"Last Name\" value=\"{{ userDetails.last_name }}\"></div></div>" +
            "<div class=\"control-group\"><label class=\"control-label\" for=\"email\">Email</label><div class=\"controls\"><input class=\"input-xlarge\" required=\"true\" data-trigger=\"change keyup focusin focusout\" data-notblank=\"true\" data-required-message=\"This field is required.\" data-validation-minlength=\"1\" data-type-email-message=\"Please enter a valid email address.\" type=\"email\" id=\"email\" placeholder=\"Email\" value=\"{{ userDetails.email }}\"></div></div>{{/guest}}" +
            "<div class=\"control-group\"><label class=\"control-label\" for=\"comments\">Your Comments</label><div class=\"controls\"><textarea class=\"input-xlarge\" data-trigger=\"change keyup focusin focusout\" data-validation-minlength=\"1\" data-maxlength=\"10000\" rows=\"4\" id=\"comments\" placeholder=\"Comments\">{{ userDetails.comments }}</textarea></div></div>" +
            "</form>" +
            "</div>" +
            "<div class=\"modal-footer\"><a href=\"#\" class=\"btn btn-large back\">Go Back</a><a href=\"#\" class=\"btn btn-large btn-primary continue\">Continue</a></div></div>"),

        discardModalTemplate: "<div class=\"modal ow-closed\">" +
            "<div class=\"modal-header\"><h1>Are you sure?</h1></div>" +
            "<div class=\"modal-body\"><p>You will lose the suggestions you have made so far, are you sure that you want to discard them?</p>" +
            "</div>" +
            "<div class=\"modal-footer\"><a href=\"#\" class=\"btn btn-large back btn-primary\">No</a><a href=\"#\" class=\"btn btn-large continue\">Yes, discard them</a></div></div>",

        attributes: {
            id: "ticket_status",
            class: "alert alert-info hidden"
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
            this.initNodes(this.el);
        },

        initSubViews: function() {
            this.complete = new Ticket.OperationsView();
            this.$el.append(this.complete.el);
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

        initNodes: function(el) {
            $("<h2>Your Suggested Changes:</h2>").prependTo(el);
            this.$buttons = $("<div id=\"ticket-buttons\">" + buttons + "</div>").appendTo(el);
            this.$commitbutton = this.$buttons.find("#commitButton");
            $("#bai_content").before(this.el);
        },

        showDebugTools: function(el) {
            if (!this.$debugTools) {
               var debug = $("<div id=\"debug-dialog\"></div>").appendTo(el);
                debug.append(statstemplate({total: 0, igcom: 0, incomplete: 0}));
                debug.append(add);
                this.$stats = debug.find("#stats");

                this.unbindFormSubmitEvents(debug);
                this.$debugTools = debug;
            }

        },

        unbindFormSubmitEvents: function($el) {
            $el.submit(function() {
                 $('input[type=submit]', this).attr('disabled', 'disabled');
                return false;
            });
        },

        removeDebugTools: function() {
            if(this.$debugTools) {
                this.$debugTools.remove();
            }
        },

        updateBodyModalUserLevel: function () {
            var userLevel = app.bodyModel.get("userLevel");
            var guestPrompt = app.bodyModel.get("guestPrompt");
            if (userLevel == "guest" && guestPrompt) {
                var template = "<div class=\"modal-header\"><h1>Do you want to login?</h1></div>" +
            "<div class=\"modal-body\">" +
            "<p><strong>Login is strongly recommended but not necessary. You can still continue as a guest.</strong><br><br> That means you can manage your profile but your edits will not be visible right away. It will take time for your changes to appear as they will be managed manually by one of our administrators.</p>" +
            "" +
            "</div>" +
            "<div class=\"modal-footer\"><ul class=\"login-btns\"><li class=\"login-btn\"><a href=\"https://arxiv.org/inspire_login\"><div class=\"arxiv-btn\"><p class=\"headingText\">Login Via</p><span class=\"innerText\">arXiv</span></div></a></li>" +
                    "<li class=\"login-btn\"><a class=\"guest\" href=\"#\"><div class=\"guest-btn\"><p class=\"headingText\">Continue as a</p><span class=\"innerText\">Guest</span></div></a></li></ul></div>";
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
            if (app.bodyModel.get("userLevel") == 'admin') {
                this.showDebugTools(this.$el);
            } else {
                this.removeDebugTools();
            }
        },

        render: function() {
            if (this.$debugTools) {
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
            if (_.size(app.userops.incomplete()) > 0) {
                app.debug && console.log("Visible");
                this.$("#intervention").toggleClass('hidden', false);
            } else {
                app.debug && console.log("Hidden");
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
            }

            var model = {
                bibrefrec: function() {
                    return params['bibrefrec'];
                }
            }
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

        commitOp: function(event) {
            var $form = event.data.form;
            if ($form.parsley("isValid")) {
                this.immediateCommitOp();
            }
            event.preventDefault();
            return false;
        },

        immediateCommitOp: function() {
            this.commitContinueTriggered();
            return false;
        },

        displayCommitStatus: function(title, message) {
            var modal = this.$commitModal;
            var headfoot = $(".modal>:not(.modal-body)");
            var header = $(".modal-header");
            var footer = $(".modal-footer");
            var modalBody = modal.find(".modal-body");

            this.modalSpinner.stop();
            modal.height("auto");
            modalBody.height("auto");
            header.find("h1").html(title);
            footer.find(".back").html("Close")
            footer.find(".continue").remove();
            headfoot.show();

            modalBody.append(message);
            this.committing = false;
            this.complete = true;
            var modal = this.$commitModal;
        },

        generateCommitErrorMessage: function() {
            return "Your changes were not submitted. This might be because of a problem with your connection. However, if this problem persists, please let us know at feedback@inspirehep.net.";
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
                return "The changes you have proposed were submitted and some will appear immediately."
            } else {
                return "The changes you have proposed were submitted and will appear immediately.";
            }
        },

        commitSuccess: function() {
           var outcome = app.userops.outcome();
           var error = (outcome.other < 1) && (outcome.ticketized < 1);

           var message = "";
           var title = "";
           if (error) {
               this.commitError();
               return;
           } else {
               var connectives = (outcome.other > 0) && (outcome.ticketized > 0);

               if (app.bodyModel.get("userLevel") == "admin") {
                   title = "Actions Completed";
               } else {
                   title = "Thank you for your suggestions";
               }

               if (outcome.other > 0) {
                   message += this.generateCommitOtherMessage(connectives);
                   message += " ";
               }
               if (outcome.ticketized > 0) {
                   message += this.generateCommitTicketizedMessage(connectives);
               }
           }
           this.displayCommitStatus(title, "<p>" + message + "</p>");
           Server.process("update", "user", {});
        },

        commitError: function() {
            var title = "There has been a problem";
            var message = this.generateCommitErrorMessage();
            this.displayCommitStatus(title, "<p>" + message + "</p>");
            Server.process("update", "user", {});
        },

        commitContinueTriggered: function() {
            var modal = this.$commitModal;
            var headfoot = $(".modal>:not(.modal-body)");
            var modalBody = modal.find(".modal-body");

            // Indicate committing
            this.committing = true;
            this.complete = false;

            // Preserve modal dimensions.
            modal.height(modal.height());
            modal.width(modal.width());

            // Empty out modal and fix dimensions
            modalBody.html('');
            headfoot.hide();
            modalBody.height("100%");

            // Load spinner
            var opts = {
              lines: 13, // The number of lines to draw
              length: 14, // The length of each line
              width: 7, // The line thickness
              radius: 30, // The radius of the inner circle
              corners: 1, // Corner roundness (0..1)
              rotate: 0, // The rotation offset
              direction: 1, // 1: clockwise, -1: counterclockwise
              color: '#000', // #rgb or #rrggbb or array of colors
              speed: 2, // Rounds per second
              trail: 60, // Afterglow percentage
              shadow: false, // Whether to render a shadow
              hwaccel: false, // Whether to use hardware acceleration
              className: 'spinner', // The CSS class to assign to the spinner
              zIndex: 2e9, // The z-index (defaults to 2000000000)
              top: 'auto', // Top position relative to parent in px
              left: 'auto' // Left position relative to parent in px
            };
            this.modalSpinner = new Spinner(opts).spin(modalBody.get(0));

            var config = {
                data: this.userDetails,
                success: $.proxy(this.commitSuccess, this),
                error: $.proxy(this.commitError, this),
                context: this
            };

            Server.process("commit", "user", config);

        },

        commitModalTriggered: function() {
            var view = this;
            var $span = $("<span class=\"bsw\"></span>").appendTo("body");

            app.debug && console.dir(this.userDetails);
            var validate = ! (this.userDetails == undefined);
            this.userDetails = this.userDetails || {
                first_name: "",
                last_name: "",
                email: "",
                comments: ""
            };
            var userDetails = this.userDetails;

            var context = { userDetails: userDetails };

            var updateUserDetails = function($el) {
                this.userDetails = {
                    first_name: $el.find("#firstName").val(),
                    last_name: $el.find("#lastName").val(),
                    email: $el.find("#email").val(),
                    comments: $el.find("#comments").val()
                };
            };

            var guestCommitModal = function() {
                _.extend(context, {title: "Enter Your Details", guest: true});
                return $(view.commitModalTemplate(context)).appendTo($span);
            };

            var userCommitModal = function() {
                _.extend(context, {title: "Any Comments?", guest: false});
                return $(view.commitModalTemplate(context)).appendTo($span);
            };

            var adminCommitModal = function() {
                _.extend(context, {title: "Please wait", guest: false});
                return $(view.commitModalTemplate(context)).appendTo($span);
            };


           switch (app.bodyModel.get("userLevel")) {
               case "user":
                   this.$commitModal = userCommitModal();
                   break;
               case "admin":
                   this.$commitModal = adminCommitModal();
                   break;
               default:
                   this.$commitModal = guestCommitModal();
                   break;
           }

            var params = {
                callbacks: {
                    afterShow: function(subjects, internalCallback) {
                        var $continueButton = subjects.modal.find(".continue");
                        var $backButton = subjects.modal.find(".back");
                        var $form = subjects.modal.find("form");
                        var modal = subjects.modal;

                        $continueButton.click({ form: $form }, $.proxy(view.commitOp, view));
                        $backButton.click(function(event) {
                            modal.trigger("hide");
                            event.preventDefault();
                            return false;
                        });

                        $form.parsley({
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
                            $form.parsley("validate");
                        }

                        var refreshButtonValidation = function(event) {
                            var $form = event.data.form;
                            var $button = event.data.button;
                            if ($form.parsley('isValid')) {
                                $button.toggleClass("disabled", false);
                                $.proxy(updateUserDetails, view)($form);
                                app.debug && console.dir(view.userDetails);
                            } else {
                                $button.toggleClass("disabled", true);
                            }
                        };

                        // Initial validation of form to update the state of the continue button.
                        refreshButtonValidation({data: { form: $form, button: $continueButton }});

                        // Bind button validation state to form change event.
                        $form.keyup({ form: $form, button: $continueButton }, refreshButtonValidation);

                        if(app.bodyModel.get("userLevel") == "admin") {
                            $.proxy(view.immediateCommitOp, view) ();
                        }

                        return internalCallback(subjects);
                    },
                    beforeHide: function(subjects, internalCallback) {
                        if (view.committing) {
                            return false;
                        }
                        $.proxy(updateUserDetails, view)(subjects.modal);
                        return internalCallback(subjects);
                    },
                    afterHide: function(subjects, internalCallback) {
                        view.commitModalClose();
                        if(view.complete) {
                            document.location.reload(true);
                        }
                        return internalCallback(subjects);
                    }
                }
            };

            this.$commitModal.omniWindow(params).trigger('show');



        },

        commitModalClose: function() {
            this.$commitModal.remove();

        },

        discardAllOp: function(event) {
            event.data.modal.trigger("hide");
            Server.process("abort", "user", {});
        },

        discardAllTriggered: function() {
            var view = this;
            var $span = $("<span class=\"bsw\"></span>").appendTo("body");

            $discardModal = $(view.discardModalTemplate).appendTo($span);

            var params = {
                callbacks: {
                    afterShow: function(subjects, internalCallback) {
                        var $yesButton = subjects.modal.find(".continue");
                        var $noButton = subjects.modal.find(".back");
                        var modal = subjects.modal;

                        $yesButton.click({modal: subjects.modal}, $.proxy(view.discardAllOp, view));
                        $noButton.click(function(event) {
                            modal.trigger("hide");
                            event.preventDefault();
                            return false;
                        });

                        return internalCallback(subjects);
                    },
                    afterHide: function(subjects, internalCallback) {
                        $span.remove();
                        return internalCallback(subjects);
                    }
                }
            };

            $discardModal.omniWindow(params).trigger('show');
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

        modalTemplate: "<div class=\"modal ow-closed\"></div>",

        resizeModalHandler: function() {
            var modal = this.$modal;
            var height = $(window).height();
            var width = $(window).width();

//            modal.width(width * 0.50);
        },

        handleModal: function() {
            var modalDesc = app.bodyModel.get("modal");
            if (!modalDesc.seen && modalDesc.prompt) {
                $("div.modal").remove();

                this.$modal = $(this.modalTemplate).appendTo(this.$("span.bsw"));
                this.$modal.append(modalDesc.content);
                var modal = this.$modal;

                var params = {
                    callbacks: {
                        afterShow: function(subjects, internalCallback) {
                            subjects.modal.find("a.guest").click(function() {
                                modal.data("dismissed", true);
                                modal.trigger("hide");
                            });
                            return internalCallback(subjects);
                        },
                        beforeHide: function(subjects, internalCallback) {
                            if (modal.data("dismissed")) {
                                return internalCallback(subjects);
                            } else {
                                return false;
                            }
                        },
                        afterHide: function(subjects, internalCallback) {
                            modalDesc.seen = true;
                            return internalCallback(subjects);
                        }
                    }
                };
                params.callbacks = _.extend(params.callbacks, modalDesc.callbacks);

                this.resizeModalHandler();
                this.$modal.omniWindow(params)
                    .trigger('show');
            } else {
                this.destroyModal();
            }

        },

        destroyModal: function() {
            this.$modal.remove();
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
                return result.isPartial()
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
            this.listenTo(this.model, 'reset', this.render)
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

        attributes: {
            class: "bsw"
        },

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

    function jsBootstraper($el) {
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
    }

    var disabledHandler = function(event) {
        event.preventDefault();
        return false;
    };

    function disableLinks($el) {
        $el.attr('disabled', 'disabled');
        $el.live("click", disabledHandler);
    }

    // Dependencies
    var Ticket = ticketbox.module("ticket");
    var Body = ticketbox.module("body");
//    var PidSearch = ticketbox.module("PidSearch");

    // Shorthands
    var app = ticketbox.app;

    // Instantiate
    var ticketView = new Ticket.View();
    var bodyView = new Body.View();

    // Bootstrap data from server
    jsBootstraper($("#jsbootstrap"));

    disableLinks($("#person_menu").find("li.disabled"));

    // Window focus event binding
    var updater = (function() {
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


//    // PidSearch test
//    var searchModel = new PidSearch.SearchModel();
//    var searchInterface = new PidSearch.SearchInterface({model: searchModel});

    // Debugging references
//    app.search = searchModel;
//    app.searchView = searchInterface;


});

$(document).ready(function() {

	$("#hepdata").on("click", "#hepname_connection", function(event) {
		var target = $(event.target);
		var data = {
			cname: target.find(".cname").text(),
			hepname: target.find(".hepname").text()
		};

		var successCallback = function () {
			alert("Your suggestion was succesfully sent!");
		};

		var errorCallback = function () {
			alert("Your suggestion was not sent!");
		};

		$.ajax({
			dataType: 'json',
			type: 'POST',
			url: '/author/manage_profile/connect_author_with_hepname_ajax',
			data: {jsondata: JSON.stringify(data)},
			success: successCallback,
			error: errorCallback,
			async: true
		});

		event.preventDefault();
		return false;
	});

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

    // Handle Comments
    if ( $('#jsonForm').length ) {

        $('#jsonForm').ajaxForm({
            // dataType identifies the expected content type of the server response
            dataType:  'json',

            // success identifies the function to invoke when the server response
            // has been received
            success:   processJson
        });

        $.ajax({
            url: '/author/claim/comments',
            dataType: 'json',
            data: { 'pid': $('span[id^=pid]').attr('id').substring(3), 'action': 'get_comments' },
            success: processJson
        });
    }

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
    }

    if ($('#autoclaim').length) {
            var data = { 'personId': gPID.toString()};
            var errorCallback = onRetrieveAutoClaimedPapersError(gPID);
            $.ajax({
                dataType: 'json',
                type: 'POST',
                url: '/author/claim/generate_autoclaim_data',
                data: {jsondata: JSON.stringify(data)},
                success: onRetrieveAutoClaimedPapersSuccess,
                error: errorCallback,
                async: true
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

//    update_action_links();

});

var orcid_regex = /^((?:https?:\/\/)?(?:www.)?orcid.org\/)?((?:\d{4}-){3}\d{3}[\dX]$)/i;

function isORCID(identifier) {
    return orcid_regex.test(identifier);
}

function isINSPIRE(identifier) {
    var inspire_regex= /^(INSPIRE-)(\d+)$/i;
    return inspire_regex.test(identifier);
}

function isValidORCID(identifier) {


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

    // $('.addToMergeButton').each( function(){
    //     if (-1 !== $.inArray('a', $(this).data('events').click )) {
    //         $(this).on('click', function(event) {
    //             onAddToMergeClick(event, $(this));
    //         });
    //     }
    // });

    // $('[class^=uncheckedProfile]').each( function(index){
    //             var pid = $(this).closest('tr').attr('id').substring(3); // e.g pid323
    //             var data = { 'requestType': "isProfileClaimed", 'personId': pid.toString()};
    //             var errorCallback = onIsProfileClaimedError(pid);
    //             $.ajax({
    //                 dataType: 'json',
    //                 type: 'POST',
    //                 url: '/author/claim/search_box_ajax',
    //                 data: {jsondata: JSON.stringify(data)},
    //                 success: onIsProfileClaimedSuccess,
    //                 error: errorCallback,
    //                 async: true
    //             });
    // });
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
        // error: errorCallback,
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
            // var errorCallback = onIsProfileClaimedError(pid);
            $.ajax({
                dataType: 'json',
                type: 'POST',
                url: '/author/claim/merge_profiles_ajax',
                data: {jsondata: JSON.stringify(data)},
                success: setAsPrimary,
                // error: errorCallback,
                async: true
            });
            event.preventDefault();
        });
        $profileHtml.find('.removeProfile').on('click', { pProfile: profile[0]}, function(event){
            var data = { 'requestType': "removeProfile", 'profile': event.data.pProfile};
            // var errorCallback = onIsProfileClaimedError(pid);
            $.ajax({
                dataType: 'json',
                type: 'POST',
                url: '/author/claim/merge_profiles_ajax',
                data: {jsondata: JSON.stringify(data)},
                success: removeFromMergeList,
                // error: errorCallback,
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

function onIsProfileClaimedSuccess(json){
    if(json['resultCode'] == 1) {
        $('.uncheckedProfile' + json['pid']).html('<span style="color:red;">Profile already claimed</span><br/>' +
            '<span>If you think that this is actually your profile bla bla bla</span>')
        .addClass('checkedProfile').removeClass('uncheckedProfile' + json['pid']);
    }
    else {
        $('.uncheckedProfile' + json['pid']).addClass('checkedProfile').removeClass('uncheckedProfile' + json['pid']);
    }
}

function onIsProfileClaimedError(pid){
  /*
   * Handle failed 'getNames' requests.
   */
   return function (XHR, textStatus, errorThrown) {
      var pID = pid;
      $('.uncheckedProfile' + pID).text('Temporary not available');
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


function confirm_bibref(claimid) {
// Performs the action of confirming a paper through an AJAX request
    var cid = claimid.replace(/\,/g, "\\," )
    var cid = cid.replace(/\:/g, "\\:")
    $('#bibref'+cid).html('<p><img src="../img/loading" style="background: none repeat scroll 0% 0% transparent;"/></p>');
    $('#bibref'+cid).load('/author/claim/status', { 'pid': $('span[id^=pid]').attr('id').substring(3),
                                                'bibref': claimid,
                                                'action': 'confirm_status' } );
//    update_action_links();
}


function repeal_bibref(claimid) {
// Performs the action of repealing a paper through an AJAX request
    var cid = claimid.replace(/\,/g, "\\," )
    var cid = cid.replace(/\:/g, "\\:")
    $('#bibref'+cid).html('<p><img src="../img/loading" style="background: none repeat scroll 0% 0% transparent;"/></p>');
    $('#bibref'+cid).load('/author/claim/status', { 'pid': $('span[id^=pid]').attr('id').substring(3),
                                                'bibref': claimid,
                                                'action': 'repeal_status' } );
//    update_action_links();
}


function reset_bibref(claimid) {
    var cid = claimid.replace(/\,/g, "\\," )
    var cid = cid.replace(/\:/g, "\\:")
    $('#bibref'+cid).html('<p><img src="../img/loading.gif" style="background: none repeat scroll 0% 0% transparent;"/></p>');
    $('#bibref'+cid).load('/author/claim/status', { 'pid': $('span[id^=pid]').attr('id').substring(3),
                                                'bibref': claimid,
                                                'action': 'reset_status' } );
//    update_action_links();
}


function action_request(claimid, action) {
// Performs the action of reseting the choice on a paper through an AJAX request
    $.ajax({
        url: "/author/claim/status",
        dataType: 'json',
        data: { 'pid': $('span[id^=pid]').attr('id').substring(3), 'action': 'json_editable', 'bibref': claimid },
        success: function(result){
            if (result.editable.length > 0) {
                if (result.editable[0] == "not_authorized") {
                    $( "<p title=\"Not Authorized\">Sorry, you are not authorized to perform this action, since this record has been assigned to another user already. Please contact the support to receive assistance</p>" ).dialog({
                        modal: true,
                        buttons: {
                            Ok: function() {
                                $( this ).dialog( "close" );
//                                update_action_links();
                            }
                        }
                    });
                } else if (result.editable[0] == "touched") {
                    $( "<p title=\"Transaction Review\">This record has been touched before (possibly by yourself). Perform action and overwrite previous decision?</p>" ).dialog({
                        resizable: true,
                        height:250,
                        modal: true,
                        buttons: {
                            "Perform Action!": function() {
                                if (action == "assign") {
                                    confirm_bibref(claimid);
                                } else if (action == "reject") {
                                    repeal_bibref(claimid);
                                } else if (action == "reset") {
                                    reset_bibref(claimid);
                                }

                                $( this ).dialog( "close" );
//                                update_action_links();
                            },
                            Cancel: function() {
                                $( this ).dialog( "close" );
//                                update_action_links();
                            }
                        }
                    });

                } else if (result.editable[0] == "OK") {
                    if (action == "assign") {
                        confirm_bibref(claimid);
                    } else if (action == "reject") {
                        repeal_bibref(claimid);
                    } else if (action == "reset") {
                        reset_bibref(claimid);
                    }
//                    update_action_links();
                } else {
//                    update_action_links();
                }

            } else {
                return false;
            }
        }
    });
}


function processJson(data) {
// Callback function of the comment's AJAX request
// 'data' is the json object returned from the server

    if (data.comments.length > 0) {
        if ($("#comments").text() == "No comments yet.") {
            $("#comments").html('<p><strong>Comments:</strong></p>\n');
        }

        $.each(data.comments, function(i, msg) {
            var values = msg.split(";;;")
            $("#comments").append('<p><em>' + values[0] + '</em><br />' + values[1] + '</p>\n');
        })
    } else {
        $("#comments").html('No comments yet.');
    }

    $('#message').val("");
}

//function update_action_links() {
//    // Alter claim links in the DOM (ensures following the non-destructive JS paradigm)
//    $('div[id^=bibref]').each(function() {
//        var claimid = $(this).attr('id').substring(6);
//        var cid = claimid.replace(/\,/g, "\\," );
//        var cid = cid.replace(/\:/g, "\\:");
//        $("#bibref"+ cid +" > #aid_status_details > #aid_confirm").attr("href", "javascript:action_request('"+ claimid +"', 'confirm')");
//        $("#bibref"+ cid +" > #aid_status_details > #aid_reset").attr("href", "javascript:action_request('"+ claimid +"', 'reset')");
//        $("#bibref"+ cid +" > #aid_status_details > #aid_repeal").attr("href", "javascript:action_request('"+ claimid +"', 'repeal')");
//   });
//}
