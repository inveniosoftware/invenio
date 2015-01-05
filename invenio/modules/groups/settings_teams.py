from flask import Blueprint, render_template, \
    request, flash, url_for, redirect
from flask.ext.login import current_user, login_required
from flask.ext.breadcrumbs import register_breadcrumb
from invenio.ext.sqlalchemy import db
from invenio.base.decorators import wash_arguments
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask.ext.menu import register_menu
from invenio.base.i18n import _
from invenio.ext.sslify import ssl_required

from invenio.modules.accounts.models import User, Usergroup, UserUsergroup
from invenio.modules.accounts.errors import AccountSecurityError, \
    IntegrityUsergroupError

blueprint = Blueprint(
    'settings_teams',
    __name__,
    url_prefix="/account/settings/teams",
    template_folder='../templates',
    static_folder='../static'
)


@blueprint.route("/", methods=['GET'])
@ssl_required
@login_required
@register_menu(
    blueprint, 'settings.teams',
    _('%(icon)s My Teams', icon='<i class="fa fa-users fa-fw"></i>'),
    order=13, # FIXME which order to choose
    active_when=lambda: request.endpoint.startswith("settings_teams.")
)
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.teams', _('Teams')
)
@wash_arguments({
    'page': (int, 1),
    'per_page': (int, 5),
    'p': (unicode, '')
})
def index(page, per_page, p):
    """List user's teams."""
    # FIXME can check be done differently?
    if page <= 0:
        page = 1
    if per_page <= 0:
        per_page = 5

    # TODO use api / improve queries
    if p:
        teams = Usergroup.query.join(
            UserUsergroup).filter(
                (UserUsergroup.id_user == current_user.get_id()) & \
                db.or_(
                    Usergroup.name.like("%" + p + "%"),
                    Usergroup.description.like("%" + p + "%")
                )
            ).paginate(page, per_page=per_page, error_out=False)
    else:
        teams = Usergroup.query.join(
            UserUsergroup).filter(
                UserUsergroup.id_user == current_user.get_id()
            ).paginate(page, per_page=per_page, error_out=False)

    return render_template(
        "teams/settings_teams.html",
        teams=teams,
        page=page,
        p=p,
    )


@blueprint.route("/<int:team_id>/leave", methods=['GET'])
@ssl_required
@login_required
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.teams.members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': Usergroup.query.filter(Usergroup.id == request.view_args['team_id']).first().name},
         {'text': _('Members')}]
)
def leave(team_id):
    """."""

    team = Usergroup.query.get_or_404(team_id)
    user = User.query.get_or_404(current_user.get_id())

    try:
        team.leave(user)
    except IntegrityUsergroupError:
        flash(_(
            'Sorry, user "%(x_nickname)s" can\'t leave the group '
            '"%(x_groupname)s" without admins, please delete the '
            'group if you want to leave.',
            x_nickname=user.nickname, x_groupname=team.name), "error")
        return redirect(url_for('settings_teams.index'))

    try:
        db.session.merge(team)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise

    current_user.reload()
    flash(_('%(user)s left the group "%(name)s".',
            user='You',
            name=team.name), 'success')
    return redirect(url_for('settings_teams.index'))


@blueprint.route("/<int:team_id>/members", methods=['GET'])
@ssl_required
@login_required
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.teams.members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': Usergroup.query.filter(Usergroup.id == request.view_args['team_id']).first().name},
         {'text': _('Members')}]
)
def members(team_id):
    """."""

    team = Usergroup.query.filter(Usergroup.id == request.view_args['team_id']).first()

    return render_template(
        "teams/settings_teams_members.html",
        team=team
    )

@blueprint.route("/<int:team_id>/members/<int:user_id>/remove", methods=['GET'])
@ssl_required
@login_required
@register_breadcrumb(
    blueprint, 'breadcrumbs.settings.teams.members', _('Members'),
    dynamic_list_constructor=lambda:
        [{'text': Usergroup.query.filter(Usergroup.id == request.view_args['team_id']).first().name},
         {'text': _('Members')}]
)
def remove(team_id, user_id):
    """."""

    team = Usergroup.query.get_or_404(team_id)
    user = User.query.get_or_404(user_id)

    try:
        team.leave(user)
    except IntegrityUsergroupError:
        flash(_(
            'Sorry, user "%(x_nickname)s" can\'t leave the group '
            '"%(x_groupname)s" without admins, please delete the '
            'group if you want to leave.',
            x_nickname=user.nickname, x_groupname=team.name), "error")
        return redirect(url_for('settings_teams.index'))

    try:
        db.session.merge(team)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise

    current_user.reload()
    flash(_('%(user)s left the group "%(name)s".',
            user='You',
            name=team.name), 'success')
    return redirect(url_for('settings_teams.index'))
