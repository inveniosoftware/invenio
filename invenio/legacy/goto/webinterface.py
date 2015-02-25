# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Implements persistent URLs
"""

import inspect

from invenio.config import CFG_SITE_URL
from invenio.ext.legacy.handler import WebInterfaceDirectory
from invenio.ext.logging import register_exception
from invenio.legacy.webuser import collect_user_info
from invenio.modules.redirector.api import get_redirection_data
from invenio.modules.redirector.registry import get_redirect_method
from invenio.utils.apache import SERVER_RETURN, HTTP_NOT_FOUND
from invenio.utils.url import redirect_to_url


class WebInterfaceGotoPages(WebInterfaceDirectory):
    def _lookup(self, component, path):
        try:
            redirection_data = get_redirection_data(component)
            goto_plugin = get_redirect_method(redirection_data['plugin'])
            args, dummy_varargs, dummy_varkw, defaults = inspect.getargspec(goto_plugin)
            args = args and list(args) or []
            args.reverse()
            defaults = defaults and list(defaults) or []
            defaults.reverse()
            params_to_pass = {}
            for arg, default in map(None, args, defaults):
                params_to_pass[arg] = default

            def goto_handler(req, form):
                ## Let's put what is in the GET query
                for key, value in dict(form).items():
                    if key in params_to_pass:
                        params_to_pass[key] = str(value)

                ## Let's override the params_to_pass to the call with the
                ## arguments in the configuration
                configuration_parameters = redirection_data['parameters'] or {}
                params_to_pass.update(configuration_parameters)

                ## Let's add default parameters if the plugin expects them
                if 'component' in params_to_pass:
                    params_to_pass['component'] = component
                if 'path' in params_to_pass:
                    params_to_pass['path'] = path
                if 'user_info' in params_to_pass:
                    params_to_pass['user_info'] = collect_user_info(req)
                if 'req' in params_to_pass:
                    params_to_pass['req'] = req
                try:
                    new_url = goto_plugin(**params_to_pass)
                except Exception as err:
                    register_exception(req=req, alert_admin=True)
                    raise SERVER_RETURN(HTTP_NOT_FOUND)
                if new_url:
                    if new_url.startswith('/'):
                        new_url = CFG_SITE_URL + new_url
                    redirect_to_url(req, new_url)
                else:
                    raise SERVER_RETURN(HTTP_NOT_FOUND)
            return goto_handler, []
        except ValueError:
            return None, []
