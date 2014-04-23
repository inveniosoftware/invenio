(function() {
  var template = Handlebars.template, templates = Handlebars.templates = Handlebars.templates || {};
templates['commitModal'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, options, functionType="function", escapeExpression=this.escapeExpression, self=this, blockHelperMissing=helpers.blockHelperMissing;

function program1(depth0,data) {
  
  
  return "Please provide your details to submit your suggestions.<br>";
  }

function program3(depth0,data) {
  
  var buffer = "", stack1;
  buffer += "\n\n        <div class=\"form-group\">\n\n            <div class=\"col-sm-3\"><label class=\"control-label\" for=\"firstName\">First Name</label></div>\n\n            <div class=\"col-sm-9\">\n                <input class=\"form-control\" data-parsley-required=\"true\" data-parsley-trigger=\"change keyup focusin focusout\"\n                       data-parsley-required-message=\"This field is required.\" data-parsley-minlength=\"2\"\n                       data-parsley-minlength-message=\"Your input is too short.\" type=\"text\"\n                       id=\"firstName\" placeholder=\"First Name\" value=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.userDetails)),stack1 == null || stack1 === false ? stack1 : stack1.first_name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\"/>\n            </div>\n\n        </div>\n        <div class=\"form-group\">\n            <div class=\"col-sm-3\"><label class=\"control-label\" for=\"lastName\">Last Name</label></div>\n\n            <div class=\"col-sm-9\">\n                <input class=\"form-control\" data-parsley-required=\"true\" data-parsley-trigger=\"change keyup focusin focusout\"\n                       data-parsley-required-message=\"This field is required.\" data-parsley-minlength=\"2\"\n                       data-parsley-minlength-message=\"Your input is too short.\" type=\"text\"\n                       id=\"lastName\" placeholder=\"Last Name\" value=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.userDetails)),stack1 == null || stack1 === false ? stack1 : stack1.last_name)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\"/>\n            </div>\n\n        </div>\n        <div class=\"form-group\">\n            <div class=\"col-sm-3\"><label class=\"control-label\" for=\"email\">Email</label></div>\n\n            <div class=\"col-sm-9\">\n                <input class=\"form-control\" data-parsley-required=\"true\" data-parsley-trigger=\"change keyup focusin focusout\"\n                       data-parsley-required-message=\"This field is required.\" data-parsley-minlength=\"1\"\n                       data-parsley-type-message=\"Please enter a valid email address.\" type=\"email\"\n                       id=\"email\" placeholder=\"Email\" value=\""
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.userDetails)),stack1 == null || stack1 === false ? stack1 : stack1.email)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\" />\n            </div>\n\n        </div>\n        ";
  return buffer;
  }

  buffer += "<div class=\"modal-header\">\n    <h2 class=\"modal-title\">";
  if (helper = helpers.title) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.title); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</h2>\n</div>\n\n<div class=\"modal-body\">\n\n    <span class=\"confirm-text\">\n        <p>";
  options={hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data}
  if (helper = helpers.guest) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.guest); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.guest) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n            If you have any comments, please fill in the comments box below.\n        </p>\n    </span>\n\n    <form class=\"form-horizontal\" role=\"form\" novalidate=\"novalidate\">\n        ";
  options={hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data}
  if (helper = helpers.guest) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.guest); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.guest) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n        <div class=\"form-group\">\n            <div class=\"col-sm-3\">\n                <label class=\"control-label\" for=\"comments\">\n                    Comments\n                </label>\n            </div>\n\n            <div class=\"col-sm-9\">\n                <textarea\n                          class=\"form-control\" data-parsley-trigger=\"change keyup focusin focusout\"\n                          data-parsley-minlength=\"1\" data-parsley-maxlength=\"10000\"\n                          rows=\"4\" id=\"comments\" placeholder=\"Comments\">\n\n                    "
    + escapeExpression(((stack1 = ((stack1 = (depth0 && depth0.userDetails)),stack1 == null || stack1 === false ? stack1 : stack1.comments)),typeof stack1 === functionType ? stack1.apply(depth0) : stack1))
    + "\n\n                </textarea>\n            </div>\n        </div>\n\n    </form>\n\n</div>\n\n\n<div class=\"modal-footer\">\n    <a href=\"#\" data-dismiss=\"modal\" class=\"btn btn-default back\">Go Back</a>\n    <a href=\"#\" class=\"btn btn-primary continue\">Continue</a>\n</div>\n";
  return buffer;
  });
templates['discardModal'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  


  return "<div class=\"modal-header\">\n    <h2 class=\"modal-title\">Are you sure?</h2>\n</div>\n\n<div class=\"modal-body\">\n  <p>You will lose the suggestions you have made so far, are you sure that you want to discard them?</p>\n</div>\n\n<div class=\"modal-footer\">\n  <a href=\"#\" class=\"btn back btn-primary\" data-dismiss=\"modal\">No</a><a href=\"#\" class=\"btn btn-default continue\">Yes, discard them</a>\n</div>\n";
  });
templates['hepConfirmation'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<div class=\"modal-header\">\n    <h2 class=\"modal-title\">\n        This One?\n    </h2>\n</div>\n\n<div class=\"modal-body\">\n	<p>\n	Please confirm that you want to suggest this HepName for <strong>";
  if (helper = helpers.cname) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.cname); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</strong>.<br>\n	It will take a few days for INSPIRE to review your suggestion.\n	</p>\n\n	<div class=\"list-group confirmation-preview\">\n	</div>\n\n</div>\n\n<div class=\"modal-footer\">\n	<a href=\"#\" class=\"btn back btn-primary\" data-dismiss=\"modal\">No</a>\n	<a href=\"#\" class=\"btn btn-default confirm\">Yes, go ahead</a>\n</div>\n";
  return buffer;
  });
templates['loginPrompt'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  


  return "<div class=\"modal-header\">\n    <h2 class=\"modal-title\">\n        Do you want to login?\n    </h2>\n</div>\n\n<div class=\"modal-body\">\n    <p>\n        <strong>Login is strongly recommended but not necessary. You can still continue as a guest.</strong><br>\n        <br>That means you can manage your profile but your edits will not be visible right away.\n        It will take time for your changes to appear as they will be managed manually by one of our administrators.\n    </p>\n</div>\n\n<div class=\"modal-footer\">\n\n    <div class=\"list-group text-left\" id=\"login-prompt-buttons\">\n        <a class=\"list-group-item list-group-item-danger\" href=\"https://arxiv.org/inspire_login\">\n            <h4 class=\"list-group-item-heading\">Login via arXiv</h4>\n            <p class=\"list-group-item-text\">Your changes will be applied immediately.</p>\n        </a>\n\n        <a class=\"list-group-item guest\" href=\"#\">\n            <h4 class=\"list-group-item-heading\">Continue as a guest</h4>\n            <p class=\"list-group-item-text\">Your changes will be checked by one of our administrators.</p>\n        </a>\n    </div>\n\n</div>\n";
  });
templates['mergeConfirmation'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  


  return "<div class=\"modal-header\">\n    <h2 class=\"modal-title\">\n        Are you sure?\n    </h2>\n</div>\n\n<div class=\"modal-body\">\n    <p>\n    You are going to merge multiple profiles together.<br>\n    Please confirm that you want to merge those profiles.\n    </p>\n</div>\n\n<div class=\"modal-footer\">\n  <a href=\"#\" class=\"btn back btn-primary\" data-dismiss=\"modal\">Go back</a>\n  <a href=\"#\" class=\"btn btn-default confirm\">Yes, merge them</a>\n</div>\n";
  });
templates['opsDebugStats'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function", escapeExpression=this.escapeExpression;


  buffer += "<p id=\"stats\">\n    <b>Total items in collection:</b> ";
  if (helper = helpers.total) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.total); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + ",\n    <b>Ignored/Complete:</b> ";
  if (helper = helpers.igcom) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.igcom); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + ",\n    <b>Incomplete:</b> ";
  if (helper = helpers.incomplete) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.incomplete); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + ",\n    <b>Committed:</b> ";
  if (helper = helpers.committed) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.committed); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + ",\n    <b>Outcome:</b> ";
  if (helper = helpers.outcome) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.outcome); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\n</p>\n";
  return buffer;
  });
templates['resultModal'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, options, self=this, functionType="function", blockHelperMissing=helpers.blockHelperMissing, escapeExpression=this.escapeExpression;

function program1(depth0,data) {
  
  
  return "\n        There has been a problem\n        ";
  }

function program3(depth0,data) {
  
  var buffer = "", stack1, helper, options;
  buffer += "\n\n            ";
  options={hash:{},inverse:self.noop,fn:self.program(4, program4, data),data:data}
  if (helper = helpers.admin) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.admin); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.admin) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(4, program4, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n            ";
  options={hash:{},inverse:self.program(6, program6, data),fn:self.noop,data:data}
  if (helper = helpers.admin) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.admin); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.admin) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.program(6, program6, data),fn:self.noop,data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n        ";
  return buffer;
  }
function program4(depth0,data) {
  
  
  return "\n            Actions Completed\n            ";
  }

function program6(depth0,data) {
  
  
  return "\n            Thank you for your suggestions\n            ";
  }

function program8(depth0,data) {
  
  
  return "\n        Your changes were not submitted. This might be because of a problem with your connection. However, if this problem persists, please let us know at feedback@inspirehep.net.\n        ";
  }

function program10(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "\n        ";
  if (helper = helpers.text) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.text); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\n        ";
  return buffer;
  }

  buffer += "<div class=\"modal-header\">\n    <h2 class=\"modal-title\">\n        ";
  options={hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data}
  if (helper = helpers.error) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.error); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.error) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n        ";
  options={hash:{},inverse:self.program(3, program3, data),fn:self.noop,data:data}
  if (helper = helpers.error) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.error); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.error) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.program(3, program3, data),fn:self.noop,data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n    </h2>\n</div>\n\n<div class=\"modal-body\">\n    <p>\n        ";
  options={hash:{},inverse:self.noop,fn:self.program(8, program8, data),data:data}
  if (helper = helpers.error) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.error); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.error) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(8, program8, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n        ";
  options={hash:{},inverse:self.program(10, program10, data),fn:self.noop,data:data}
  if (helper = helpers.error) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.error); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.error) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.program(10, program10, data),fn:self.noop,data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n    </p>\n</div>\n\n<div class=\"modal-footer\">\n  <a href=\"#\" class=\"btn back btn-primary\" data-dismiss=\"modal\">Close</a>\n</div>\n";
  return buffer;
  });
templates['singleOperation'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, options, functionType="function", escapeExpression=this.escapeExpression, self=this, blockHelperMissing=helpers.blockHelperMissing;

function program1(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "\n          <div class=\"col-xs-2\">\n              <h2><span class=\"label ";
  if (helper = helpers.classes) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.classes); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\">";
  if (helper = helpers.action) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.action); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</span></h2>\n          </div>\n          ";
  return buffer;
  }

function program3(depth0,data) {
  
  
  return "8";
  }

function program5(depth0,data) {
  
  
  return "12";
  }

function program7(depth0,data) {
  
  var buffer = "", stack1, helper, options;
  buffer += ", known by:\n\n                  <select>\n                      ";
  options={hash:{},inverse:self.noop,fn:self.program(8, program8, data),data:data}
  if (helper = helpers.bibrefs) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.bibrefs); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.bibrefs) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(8, program8, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n                      <option class=\"nobibref\" value=\"\">I don't know</option>\n                  </select>\n\n              ";
  return buffer;
  }
function program8(depth0,data) {
  
  var buffer = "", stack1, helper;
  buffer += "\n                      <option value=\"";
  if (helper = helpers.bibref) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.bibref); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\">";
  if (helper = helpers.sig) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.sig); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</option>\n                      ";
  return buffer;
  }

  buffer += "<div class=\"panel panel-default\">\n  <div class=\"panel-body\">\n\n      <div class=\"row clearfix\">\n\n          ";
  options={hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data}
  if (helper = helpers.action) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.action); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.action) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(1, program1, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n\n          <div class=\"col-xs-";
  options={hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data}
  if (helper = helpers.action) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.action); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.action) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(3, program3, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  options={hash:{},inverse:self.program(5, program5, data),fn:self.noop,data:data}
  if (helper = helpers.action) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.action); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.action) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.program(5, program5, data),fn:self.noop,data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\">\n              <a href=\"";
  if (helper = helpers.rec_link) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.rec_link); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\" target=\"_blank\">";
  if (helper = helpers.rec_title) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.rec_title); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</a>\n\n              <br>For profile <a href=\"";
  if (helper = helpers.profile_link) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.profile_link); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "\">";
  if (helper = helpers.profile) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.profile); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  buffer += escapeExpression(stack1)
    + "</a>\n\n              ";
  options={hash:{},inverse:self.noop,fn:self.program(7, program7, data),data:data}
  if (helper = helpers.editable) { stack1 = helper.call(depth0, options); }
  else { helper = (depth0 && depth0.editable); stack1 = typeof helper === functionType ? helper.call(depth0, options) : helper; }
  if (!helpers.editable) { stack1 = blockHelperMissing.call(depth0, stack1, {hash:{},inverse:self.noop,fn:self.program(7, program7, data),data:data}); }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n          </div>\n\n          <div class=\"col-xs-2\">\n\n              <div class=\"op-buttons\">\n                  <button class=\"btn btn-default btn-small op-btn removeOp pull-right\" type=\"button\">\n                      <span class=\"glyphicon glyphicon-trash\"></span>&nbspDiscard\n                  </button>\n              </div>\n\n          </div>\n      </div>\n\n  </div>\n</div>";
  return buffer;
  });
templates['ticketBox'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function";


  buffer += "<div id=\"debug-dialog\" class=\"panel panel-default\">\n\n    <div class=\"panel-heading\">Operations Debugging Information</div>\n\n    <div class=\"panel-body\"></div>\n\n</div>\n\n<h2>Your Suggested Changes:</h2>\n\n";
  if (helper = helpers.operations) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.operations); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n<div id=\"ticket-buttons\" class=\"btn-group btn-group-lg\">\n\n    <button id=\"commitButton\" class=\"btn btn-primary\" disabled=\"disabled\">Confirm</button>\n    <button id=\"abortButton\" class=\"btn btn-default\">Discard All</button>\n\n</div>\n";
  return buffer;
  });
templates['ticketModal'] = template(function (Handlebars,depth0,helpers,partials,data) {
  this.compilerInfo = [4,'>= 1.0.0'];
helpers = this.merge(helpers, Handlebars.helpers); data = data || {};
  var buffer = "", stack1, helper, functionType="function";


  buffer += "<div id=\"ticket-modal\" class=\"modal\">\n\n    <div class=\"modal-dialog\">\n\n        <div class=\"modal-content\">\n\n          ";
  if (helper = helpers.modalContent) { stack1 = helper.call(depth0, {hash:{},data:data}); }
  else { helper = (depth0 && depth0.modalContent); stack1 = typeof helper === functionType ? helper.call(depth0, {hash:{},data:data}) : helper; }
  if(stack1 || stack1 === 0) { buffer += stack1; }
  buffer += "\n\n        </div>\n    </div>\n</div>\n";
  return buffer;
  });
})();