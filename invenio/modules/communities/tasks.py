# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from __future__ import absolute_import

from datetime import datetime
from invenio.ext.sqlalchemy import db
from invenio.modules.search.models import Collection
from celery.task.base import PeriodicTask

from .models import Community
from invenio.base.globals import cfg


class RankingTask(PeriodicTask):

    """
        Task which will be autodiscovered and run periodically
        if celery worker is up and running (with --beat option).
    """
    run_every = cfg['COMMUNITIES_PERIODIC_TASKS'][
        'ranking_deamon']['run_every']

    def run(*args, **kwargs):
        ranking_deamon()


def calculate_rank_for_community(community, max_recs_cnt):
    """
        Calculate rank for single community. Whole algorithm below.

        Algorithm:
        1. find the highest number of records for any community:
           max_recs_cnt
        2. find the number of records for this community: recs_cnt
        3. calculate how many days have passed since last record
           was accepted for this community: interval
        4. calculate ranking points with formula:
           C*recs_cnt + max_date_ranking - inteval*day_value + fixed_points
           where:
           max_date_ranking = C2*max_recs_cnt
           day_value = max_date_ranking/some_value (some_value example:
           50 [days])
           C, C2 const.
    """
    factor = 5
    period_of_expiration = 50

    recs_cnt = community.collection.nbrecs
    if recs_cnt > 0.3 * max_recs_cnt:
        max_date_ranking = 2 * max_recs_cnt
        day_value = max(max_date_ranking / period_of_expiration, 1)
    else:
        max_date_ranking = max_recs_cnt
        day_value = max(max_date_ranking / period_of_expiration, 1)

    last_record_accepted = community.last_record_accepted or community.created
    interval = (datetime.now() - last_record_accepted).days
    date_ranking = max(max_date_ranking - interval * day_value, 0)
    ranking = factor * recs_cnt + date_ranking + community.fixed_points
    return ranking


def ranking_deamon():
    """
        Ranks communities.
        Task is being run periodically.
    """
    comms = Community.query.all()
    coll = Collection.query.filter(Collection.community).order_by(
        db.desc(Collection.nbrecs)).first()
    if coll:
        max_recs_cnt = coll.nbrecs
    for comm in comms:
        ranking = calculate_rank_for_community(comm, max_recs_cnt)
        comm.ranking = ranking
    db.session.commit()
