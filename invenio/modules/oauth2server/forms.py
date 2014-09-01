# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Forms for generating access tokens and clients."""

from oauthlib.oauth2.rfc6749.errors import InsecureTransportError, \
    InvalidRedirectURIError
from wtforms_alchemy import model_form_factory
from wtforms import fields, validators, widgets
from invenio.utils.forms import InvenioBaseForm

from .models import Client
from .validators import validate_redirect_uri


#
# Widget
#
def scopes_multi_checkbox(field, **kwargs):
    """ Render multi checkbox widget. """
    kwargs.setdefault('type', 'checkbox')
    field_id = kwargs.pop('id', field.id)

    html = ['<div class="row">']

    for value, label, checked in field.iter_choices():
        choice_id = u'%s-%s' % (field_id, value)

        options = dict(
            kwargs,
            name=field.name,
            value=value,
            id=choice_id,
            class_=' ',
        )

        if checked:
            options['checked'] = 'checked'

        html.append(u'<div class="col-md-3">')
        html.append(u'<label for="%s" class="checkbox-inline">' % field_id)
        html.append(u'<input %s /> ' % widgets.html_params(**options))
        html.append("%s <br/><small class='text-muted'>%s</small>" % (
            value, label.help_text)
        )
        html.append(u'</label></div>')
    html.append(u'</div>')

    return u''.join(html)


#
# Redirect URI field
#
class RedirectURIField(fields.TextAreaField):

    """ Process redirect URI field data. """

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = "\n".join([
                x.strip() for x in
                filter(lambda x: x, "\n".join(valuelist).splitlines())
            ])

    def process_data(self, value):
        self.data = "\n".join(value)


class RedirectURIValidator(object):

    """ Validate if redirect URIs. """

    def __call__(self, form, field):
        errors = []
        for v in field.data.splitlines():
            try:
                validate_redirect_uri(v)
            except InsecureTransportError:
                errors.append(v)
            except InvalidRedirectURIError:
                errors.append(v)

        if errors:
            raise validators.ValidationError(
                "Invalid redirect URIs: %s" % ", ".join(errors)
            )


#
# Forms
#
class ClientFormBase(model_form_factory(InvenioBaseForm)):
    class Meta:
        model = Client
        exclude = [
            'client_secret',
            'is_internal',
            'is_confidential',
        ]
        strip_string_fields = True
        field_args = dict(website=dict(
            validators=[validators.Required(), validators.URL()],
            widget=widgets.TextInput(),
        ))


class ClientForm(ClientFormBase):
    # Trick to make redirect_uris render in the bottom of the form.
    redirect_uris = RedirectURIField(
        label="Redirect URIs (one per line)",
        description="One redirect URI per line. This is your applications"
                    " authorization callback URLs. HTTPS must be used for all "
                    "hosts except localhost (for testing purposes).",
        validators=[RedirectURIValidator(), validators.Required()],
        default='',
    )


class TokenForm(InvenioBaseForm):
    name = fields.TextField(
        description="Name of personal access token.",
        validators=[validators.Required()],
    )
    scopes = fields.SelectMultipleField(
        widget=scopes_multi_checkbox,
        choices=[],  # Must be dynamically provided in view.
        description="Scopes assigns permissions to your personal access token."
                    " A personal access token works just like a normal OAuth "
                    " access token for authentication against the API."
    )
