# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""nwsToolTip Flask Blueprint."""

from flask import(
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
)
from flask.ext.menu import register_menu

from invenio.ext.sqlalchemy import db

from sqlalchemy.exc import IntegrityError

from .. import config
from ..encoder import Decode, Encode
from ..models import NwsSTORY, NwsTAG, NwsToolTip

blueprint = Blueprint(
    'webnews',
    __name__,
    template_folder='../templates',
    static_folder='../static'
)
# @register_menu(blueprint, 'main.webnews',config.CFG_WEBNEWS_ADMIN_MAIN_NAV)
# @register_menu(blueprint, 'webnews',config.CFG_WEBNEWS_ADMIN_MAIN_NAV)


@blueprint.route(config.CFG_WEBNEWS_MENU_INDEX)
@register_menu(
    blueprint,
    'webnews.menu.search',
    [
        config.CFG_WEBNEWS_SEARCH_NAV_NAME,
        'glyphicon glyphicon-search',
        'general'
    ]
)
def index():
    """index function."""
    try:
        result = NwsSTORY.query.filter_by(
            document_status='SHOW'
        ).limit(5).all()
        return render_template(
            'search.html',
            searchResult=result,
            EncodeStr=Encode
        )
    except Exception:
        db.create_all()
        return redirect(config.CFG_WEBNEWS_MENU_INDEX)


@blueprint.route(config.CFG_WEBNEWS_SEARCH, methods=['GET', 'POST'])
def search():
    """search function."""
    if request.method == 'POST':
        try:
            result = NwsSTORY.query.filter(
                NwsSTORY.title.contains(
                    request.form['keywords']
                ) | NwsSTORY.body.contains(request.form['keywords'])
            ).filter_by(document_status='SHOW').all()
            return render_template(
                'search.html',
                searchResult=result,
                resultshow='block',
                EncodeStr=Encode
            )
        except IntegrityError:
            flash('Error')
            # alert = config.CFG_WEBNEWS_ERROR_ALERT
    try:
        keywords = Decode(request.args.get('keywords', Encode(None)))
        id = int(Decode(request.args.get('id', Encode(0))))
        if keywords == '1':
            result1 = NwsSTORY.query.get(id)
            return render_template(
                'details.html',
                searchResult=result1
            )
        result1 = NwsTAG.query.filter(NwsTAG.tag.contains(keywords)).all()
        result = NwsSTORY.query.filter(
            NwsSTORY.id.in_(appendToListy(result1))
        ).filter_by(document_status='SHOW').all()
        return render_template(
            'search.html',
            searchResult=result,
            resultshow='block',
            EncodeStr=Encode
        )

    except IntegrityError:
        flash('Error')
        # alert = config.CFG_WEBNEWS_ERROR_ALERT


@blueprint.route('/show_tooltips')
def show_tooltips():
    """show tooltips function."""
    targetpage = request.args.get('targetpage', 0, type=str)
    try:
        # session['exclude_ids']=[]
        # targetpage = request.args.get('targetpage', 0, type=str)
        if session['exclude_ids']:
            result1 = NwsToolTip.query.filter(
                (
                    (NwsToolTip.target_page == targetpage) |
                    (NwsToolTip.target_page == '*')
                ) &
                (NwsToolTip.target_element.notin_(excludeList(targetpage)))
            ).all()
        else:
            result1 = NwsToolTip.query.filter(
                (NwsToolTip.target_page == targetpage) |
                (NwsToolTip.target_page == '*')
            ).all()
    except Exception:
        session['exclude_ids'] = []
        result1 = NwsToolTip.query.filter(
            (NwsToolTip.target_page == targetpage) |
            (NwsToolTip.target_page == '*')
        ).all()

    # filter((User.username == name) | (User.email == email))

    return jsonify(tooltip=[i.serialize for i in result1])


def appendToListy(object):
    """appendToListy function."""
    Lst = []
    for result in object:
        Lst.append(result.id_story)
    return Lst


@blueprint.route('/tooltips_exclude')
def exclude_tooltip():
    """exclude_tooltip function."""
    targetpage = request.args.get('targetpage', 0, type=str)
    tooltipElement = request.args.get('tooltipElement', 0, type=str)
    SessionList = []
    if session['exclude_ids']:
        SessionList = session['exclude_ids']
        if UniqueInsert(SessionList, tooltipElement, targetpage):
            SessionList.append({'page': targetpage, 'Element': tooltipElement})
            session['exclude_ids'] = SessionList
    else:
        SessionList = [{'page': targetpage, 'Element': tooltipElement}]
        session['exclude_ids'] = SessionList

    return jsonify(result='added')


def UniqueInsert(Obj, element, page):
    """UniqueInsert function."""
    for item in Obj:
        if item['Element'] == element and item['page'] == page:
            return False
    return True


def excludeList(page):
    """excludeList function."""
    Lst = []
    if session['exclude_ids']:
        for item in session['exclude_ids']:
            if item['page'] == page:
                Lst.append(item['Element'])

    return Lst
