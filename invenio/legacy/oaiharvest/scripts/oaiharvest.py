# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""Invenio OAIHarvest Admin Task.
        It launches oaiharvest periodically by reading table oaiHARVEST.

Usage: oaiharvest %s [options]
Examples:
      oaiharvest -r arxiv -s 24h
      oaiharvest -r pubmed -d 2005-05-05:2005-05-10 -t 10m

 Specific options:
 -r, --repository=NAME     name of the OAI repository to be harvested (default=all)

 Scheduling options:
 -u,  --user=USER          user name to store task, password needed
 -s,  --sleeptime=SLEEP    time after which to repeat task (no)
                           e.g.: 1s, 30m, 24h, 7d
 -t,  --time=TIME          moment for the task to be active (now)
                           e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26

 General options:
 -h,  --help               print this help and exit
 -V,  --version            print version and exit
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)
"""


from invenio.base.factory import with_app_context


@with_app_context()
def main():
    from ..daemon import main as oai_main
    return oai_main()

### okay, here we go:
if __name__ == '__main__':
    main()
