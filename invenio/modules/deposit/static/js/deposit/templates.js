var tpl_webdeposit_status_saved = Hogan.compile('Saved <i class="glyphicon glyphicon-ok"></i>');
var tpl_webdeposit_status_saved_with_errors = Hogan.compile('<span class="text-warning">Saved, but with errors <i class="glyphicon glyphicon-warning-sign"></i></span>');
var tpl_webdeposit_status_saving = Hogan.compile('Saving <img src="/img/loading.gif" />');
var tpl_webdeposit_status_error = Hogan.compile('<span class="text-danger">Not saved due to server error. Please try to reload your browser <i class="glyphicon glyphicon-warning-sign"></i></span>');
var tpl_field_message = Hogan.compile('{{#messages}}<div>{{{.}}}</div>{{/messages}}');
var tpl_required_field_message = Hogan.compile('{{{label}}} is required.');
var tpl_flash_message = Hogan.compile('<div class="alert alert-{{state}}"><a class="close" data-dismiss="alert" href="#"">&times;</a>{{{message}}}</div>');
var tpl_message_success = Hogan.compile('Successfully saved.');
var tpl_message_errors = Hogan.compile('The form was saved, but there were errors. Please see below.');
var tpl_message_server_error = Hogan.compile('The form could not be saved, due to a communication problem with the server. Please try to reload your browser <i class="glyphicon glyphicon-warning-sign"></i>');
var tpl_loader = Hogan.compile('<img src="/img/loading.gif" />');
var tpl_loader_success = Hogan.compile('<span class="text-success"> <i class="glyphicon glyphicon-ok"></i></span>');
var tpl_loader_failed = Hogan.compile('<span class="text-muted"> <i class="glyphicon glyphicon-warning-sign"></i></span>');
var tpl_file_entry = Hogan.compile('<tr id="{{id}}" class="hide">' +
    '<td id="{{id}}_link">{{#download_url}}<a href="{{download_url}}">{{filename}}</a>{{/download_url}}{{^download_url}}{{filename}}{{/download_url}}</td>' +
    '<td>{{filesize}}</td>' +
    '<td width="30%">{{^completed}}<div class="progress{{#striped}} progress-striped{{/striped}} active"><div class="bar" style="width: {{progress}}%;">{{/completed}}</div></div></td>' +
    '<td><a id="{{id_sort}}" class="sortlink text-muted" rel="tooltip" title="Re-order files"><i class="glyphicon glyphicon-reorder"></i></a>&nbsp;{{#removeable}}<a class="rmlink" rel="tooltip" title="Delete file"><i class="glyphicon glyphicon-trash"></i></a>{{/removeable}}</td>' +
    '</tr>');
var tpl_file_link = Hogan.compile('<a href="{{download_url}}">{{filename}}</a>');
var tpl_error = Hogan.compile('<div class="alert alert-danger"><a class="close" data-dismiss="alert" href="#"">&times;</a><strong>Error:</strong> {{{message}}}</div>');
var tpl_modal_submitting = Hogan.compile('<div align="center">Submitting <img src="/img/loading.gif" /></div>');