# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

"""Cloud Application Blueprint"""


from flask import Blueprint, make_response, g, render_template, session, \
                  request, flash, jsonify, redirect, url_for, current_app
from invenio.webuser_flask import current_user
from invenio.websession_model import User
from invenio.sqlalchemyutils import db
from invenio.cloudutils_factory import CloudServiceFactory
from fs.opener import fsopen
from invenio.cloudutils_config import *
import math
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webinterface_handler import wash_urlargd
from invenio.config import \
     CFG_SITE_LANG
from fs.base import FS
from invenio.cloudutils_config import CFG_SERVICE_PRETTY_NAME
from invenio.cloudutils import CloudRedirectUrl, \
                               ErrorBuildingFS
    

blueprint = InvenioBlueprint('cloudutils', __name__, url_prefix="/cloud",
                breadcrumbs=[(_("Your Cloud Applications"), 'cloudutils.about')],
                menubuilder=[('personalize.cloud',
                             _('Your Cloud Applications'),
                             'cloudutils.about', 10)])


@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def about():
    current_app.config['breadcrumbs_map']["cloudutils"] = \
        [(_("Your Cloud Applications"), 'cloudutils.about')]
        
    return render_template('cloudutils_index.html')


@blueprint.route('/<service>/', methods=['GET', 'POST'])
@blueprint.route('/<service>/index', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def index(service):
    method = 'index'
    service_pretty_name = CFG_SERVICE_PRETTY_NAME.get(service)
    current_app.config['breadcrumbs_map']["cloudutils"] = \
        [(_("Your Cloud Applications"), 'cloudutils.about')] + \
        [(service_pretty_name, url_for('cloudutils.index', service=service))]
    
    try:
        filesystem = _build_file_system(method, service, service_pretty_name)
    except CloudRedirectUrl, e:
        return _build_cloud_connect_page(e, service, service_pretty_name)
    except Exception, e:
        
        return redirect(url_for('cloudutils.index', service=service)) 
      
    if( session.has_key('files_to_upload') ):
        return upload(service)
    
    return _build_page(filesystem, service)

@blueprint.route('/<service>/callback', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def callback(service):
    method = 'callback'
    service_pretty_name = CFG_SERVICE_PRETTY_NAME.get(service)
    try:
        filesystem = _build_file_system(method, service, service_pretty_name)
    except CloudRedirectUrl, e:
        return _build_cloud_connect_page(e, service, service_pretty_name)
    except Exception, e:
        return redirect(url_for('cloudutils.index', service=service)) 
    
    return redirect(url_for('cloudutils.index', service=service)) 


@blueprint.route('/<service>/download', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def download(service):
    method = 'download'
    service_pretty_name = CFG_SERVICE_PRETTY_NAME.get(service)
    current_app.config['breadcrumbs_map']["cloudutils"] = \
        [(_("Your Cloud Applications"), 'cloudutils.about')] + \
        [(service_pretty_name, url_for('cloudutils.index', service=service))]
    
    try:
        filesystem = _build_file_system(method, service, service_pretty_name)
    except CloudRedirectUrl, e:
        return _build_cloud_connect_page(e, service, service_pretty_name)
    except:
        return redirect(url_for('cloudutils.index', service=service)) 
    
    return filesystem.getcontents(request.args.get('path'))

@blueprint.route('/<service>/delete', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def delete(service):
    method = 'delete'
    service_pretty_name = CFG_SERVICE_PRETTY_NAME.get(service)
    current_app.config['breadcrumbs_map']["cloudutils"] = \
        [(_("Your Cloud Applications"), 'cloudutils.about')] + \
        [(service_pretty_name, url_for('cloudutils.index', service=service))]
    
    try:
        filesystem = _build_file_system(method, service, service_pretty_name)
    except CloudRedirectUrl, e:
        return _build_cloud_connect_page(e, service, service_pretty_name)
    except:
        return redirect(url_for('cloudutils.index', service=service)) 
    
    
    if( filesystem.isdir(request.args.get('path')) ):
        filesystem.removedir(request.args.get('path'))
    else:
        filesystem.remove(request.args.get('path'))
    return redirect(url_for('cloudutils.index', service=service))

@blueprint.route('/<service>/upload', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def upload(service):
    method = 'upload'
    service_pretty_name = CFG_SERVICE_PRETTY_NAME.get(service)
    current_app.config['breadcrumbs_map']["cloudutils"] = \
        [(_("Your Cloud Applications"), 'cloudutils.about')] + \
        [(service_pretty_name, url_for('cloudutils.index', service=service))]

    if request.form.has_key('files'):     
        session['return_url'] = request.form['return_url']
        files = request.form['files']
        session['files_to_upload'] = files[2:-2].split("', '")
    
    try:
        filesystem = _build_file_system(method, service, service_pretty_name)
    except CloudRedirectUrl, e:
        return _build_cloud_connect_page(e, service, service_pretty_name)
    except:
        return redirect(url_for('cloudutils.index', service=service)) 

    files = session.pop('files_to_upload')
    from invenio.bibdocfile import bibdocfile_url_to_bibdocfile, \
                                   bibdocfile_url_to_fullpath
          
    try:      
        for one in files:
            file = bibdocfile_url_to_bibdocfile( one )
            f = fsopen(file.get_full_path(), 'r')
            n = filesystem.open(file.get_full_name(), "w")
            n.write(f.read())
            n.close()
        flash("All files uploaded successfully", 'info')
    except:
        flash("Something went wrong, please try again", 'error')
            
    return redirect(session.pop('return_url'))

def _build_file_system(method, service, service_pretty_name):
    service_factory = CloudServiceFactory()
    callback_url = url_for('cloudutils.callback', service=service, _external = True)
    
    if( method == "callback" ):
        req = request
    else:
        req = None
    
    uri = "%s://" % service
    return service_factory.get_fs(uri)    

def _build_page(filesystem, service):
    folder_metadata = filesystem.listdirinfo( request.args.get('path', "") )
    
    number_of_pages = int(math.ceil(float(len(folder_metadata)) / 
                                    CFG_CLOUD_UTILS_ROWS_PER_PAGE))
    current_page = int(request.args.get('page', '1'))
    
    account_info = filesystem.about()
                
    if( current_page == 1 and number_of_pages > 1 ):
        folder_metadata = folder_metadata[0:CFG_CLOUD_UTILS_ROWS_PER_PAGE]
    elif( number_of_pages > 1 and current_page <= number_of_pages ):
        folder_metadata = folder_metadata[
                              CFG_CLOUD_UTILS_ROWS_PER_PAGE * 
                              (current_page-1) : CFG_CLOUD_UTILS_ROWS_PER_PAGE * 
                              current_page ]
    
    return render_template('service_index.html',
                               service_name = [service, filesystem.__name__],
                               parent= "/".join(request.args.get('path', "/").split("/")[:-1]),
                               folder_metadata=folder_metadata,
                               account_info=account_info, 
                               number_of_pages=number_of_pages, 
                               current_page=current_page
                               )
    
def _build_cloud_connect_page(url, service, service_pretty_name):
    prompt = """Click <a href="%s">here</a> to link with %s."""
    out = prompt % (url, service_pretty_name)
    flash(out, 'info')
    return render_template('service_index.html',
                           service_name = [service, service_pretty_name],
                           parent= None,
                           folder_metadata=None,
                           account_info=None, 
                           number_of_pages=1, 
                           current_page=1
                           )