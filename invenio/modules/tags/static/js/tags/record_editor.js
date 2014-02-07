/*
 * This file is part of Invenio.
 * Copyright (C) 2013 CERN.
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

/* Script for 'Edit Tags' modal window

Suggested HTML:
<div id="..." class="modal hide fade"
 data-webtageditor-element="editor"
 data-webtageditor-recid="{{id_bibrec}}">

    <input type="text" data-webtageditor-element="tokenInput"  />

    <div data-webtageditor-element="errorArea"></div>
</div>

Suggested contructor:

new webTagEditor('[data-webtageditor-element="editor"][data-webtageditor-recid="{{id_bibrec}}"]',
    {tags: {{tags}},
    url_tokenize: {{url_for()}},

);
*/

function webTagEditor(element, options)
{
    // $element should be the modal window
    this.$element = $(element).first();
    // $tokenInput is the input which will be converted to tokenInput
    this.$tokenInput = this.$element.find('[data-webtageditor-element="tokenInput"]').first();
    // $errorArea is a div which will hold error messages
    this.$errorArea = this.$element.find('[data-webtageditor-element="errorArea"]').first();

    // Arguments
    this.options = $.extend({}, webTagEditor.DEFAULTS, options);

    // Check for id_bibrec
    // id_bibrec provided in options has precendece over the one provided in html
    if(this.options.id_bibrec == 0)
    {
        var recid = this.$element.attr('data-webtageditor-recid');

        if(recid)
        {
            this.options.id_bibrec = recid;
        }
        else
        {
            console.log('webTagEditor: missing id_bibrec');
        }
    }

    // Prepare pre-populated items
    var pre_populated = Array();

    for(var i = 0; i < this.options.tags.length; ++i)
    {
        item = options.tags[i];

        item.status = 'stable';
        item.readonly = !(item.can_remove);

        pre_populated.push(item);
    }

    // Pass 'this' inside closures
    var editor = this;

    // Initialise tokenInput
    this.$tokenInput.tokenInput(
        this.options.url_tokenize,
        {
            jsonContainer: "results",
            preventDuplicates: true,
            searchDelay: 175,
            zindex: 11100,

            prePopulate: pre_populated,
            onResult: this.tokenInput_onResult,
            resultsFormatter: this.tokenInput_resultsFormatter,
            tokenFormatter: this.tokenInput_tokenFormatter,

            onAdd: function (item) {
                //Send requests

                if(item.status == 'adding')
                {
                    var arguments = {id_tag: item.id,
                                     id_bibrec: editor.options.id_bibrec};

                    $.getJSON(editor.options.url_attach,
                         arguments,
                         function (data)
                         {
                            editor.onServerResponse(item, 'attach', arguments, data);
                         }).fail(function()
                         {
                            editor.onServerError(item, 'attach', arguments, null);
                         });
                }
                else if(item.status == 'creating')
                {
                    var arguments = {name: item.name,
                                     id_bibrec: editor.options.id_bibrec};

                    $.getJSON(editor.options.url_create,
                         arguments,
                         function (data)
                         {
                            editor.onServerResponse(item, 'create', arguments, data);
                         }).fail(function()
                         {
                            editor.onServerError(item, 'create', arguments, null);
                         });
                }
            },
            onDelete: function (item) {
                if(item.status == 'stable')
                // new items are replaced by onAdd, so it is not deletion
                // a 'removing' item is deleted when server completed
                //      the request, so can be removed finally
                {
                    item.status = 'removing';
                    item.readonly = true;
                    editor.$tokenInput.tokenInput('add', item);

                    arguments = {id_tag: item.id,
                                 id_bibrec: editor.options.id_bibrec};

                    $.getJSON(editor.options.url_detach,
                         arguments,
                         function (data)
                         {
                            editor.onServerResponse(item, 'detach', arguments, data);
                         }).fail(function()
                         {
                            editor.onServerError(item, 'detach', arguments, null);
                         });
                }
            }

        });

    //Reload when modal is closed
    this.$element.on('hidden', function () {
        location.reload();
    })
}

webTagEditor.DEFAULTS = {
    id_bibrec: 0,
    tags: [],
    url_tokenize: '/yourtags/tokenize/',
    url_attach:'/yourtags/attach',
    url_detach: '/yourtags/detach',
    url_create: '/yourtags/create'
}

//Processes the server response of attach detach create AJAX requests
webTagEditor.prototype.onServerResponse = function(item, intended_action, arguments, response)
{
    if((!('action' in response)) ||
        response['action'] != intended_action)
    {
        var errors = {'response': ['Response action does not match request action.']};
        this.onServerError(item, intended_action, arguments, bibrec, errors);
        return;
    }

    if(!('success' in response))
    {
        var errors = {'response': ['Incorrect response format.']};
        this.onServerError(item, intended_action, arguments, bibrec,  errors);
        return;
    }

    var success = response['success'];

    if(!success)
    {
        this.onServerError(item, intended_action, arguments, bibrec, response['errors']);
        return;
    }

    if(intended_action == 'create' || intended_action == 'attach')
    {
        this.$tokenInput.tokenInput('remove', item);
        item.readonly = false;
        item.status = 'stable';
        if(intended_action == 'create')
        {
            item.id = response['id_tag'];
        }
        this.$tokenInput.tokenInput('add', item);
    }
    else if(intended_action == 'detach')
    {
        this.$tokenInput.tokenInput('remove', item);
    }
}

//If the attach detach create AJAX request fails, this functions prints a message and
// reverts the editor to pre-request state
webTagEditor.prototype.onServerError = function(item, intended_action, arguments, errors) {
    //Default error = no conncetion
    if(errors == null || errors.length == 0)
    {
        errors = new Array();
        errors['response'] = ['Server not responding.'];
    }

    //Return tokens to original state
    if(intended_action == 'create' || intended_action == 'attach')
    {
        this.$element.tokenInput('remove', item);
    }
    else if(intended_action == 'detach')
    {
        this.$element.tokenInput('remove', item);
        item.readonly = false;
        item.status = 'stable';
        this.$element.tokenInput('add', item);
    }

    //Display errors
    for (var key in errors)
    {
       if (errors.hasOwnProperty(key))
       {
            var messages = errors[key];

            for(var i = 0; i < messages.length; i++)
            {
                this.$errorArea.html('<div class="alert alert-error"><strong>Error:</strong> '+messages[i]+'</div>');
            }
       }
    }
}

// tokenInput formatting and preprocessing functions
// declared here to save memory (one instance of each function for whole class)

webTagEditor.prototype.tokenInput_onResult = function (server_response) {
    var items = server_response.results;
    var query = server_response.query;

    for(var i = 0; i < items.length; ++i)
    {
        item = items[i];
        item.readonly = true;

        if(item.id == 0)
        {
            // Id = 0 means that this is the suggested name for new created tag
            item.status = 'creating';
        }
        else
        {
            item.status = 'adding';
        }

        items[i] = item;
    }

    server_response.results = items;
    return server_response;
}

webTagEditor.prototype.tokenInput_resultsFormatter = function(item) {
    var token_html = item.name;

    if(item.status == 'creating')
    {
        token_html += '<span style="color: blue; float: right;"> (Create new tag)</span>';
    }

    return "<li><p>"+token_html+"</p></li>";
}

webTagEditor.prototype.tokenInput_tokenFormatter = function(item) {
    var token_html = item.name;

    if(item.status == 'removing')
    {
        token_html += ' <p class="text-right text-error">&nbsp;(removing)</p>';
    }
    else if(item.status == 'adding')
    {
        token_html += ' <p class="text-right text-success">&nbsp;(adding)</p>';
    }
    else if(item.status == 'creating')
    {
        token_html += ' <p class="text-right text-info">&nbsp;(creating)</p>';
    }

    return "<li><p>"+token_html+"</p></li>";
}
