## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

from invenio.base.factory import with_app_context


@with_app_context()
def main():
    """Main that construct all the bibtask."""
    from invenio.bibtask import task_init
    from invenio.websearch_webcoll import (
        task_submit_elaborate_specific_parameter, task_submit_check_options,
        task_run_core, __revision__)

    task_init(authorization_action="runwebcoll",
            authorization_msg="WebColl Task Submission",
            description="""Description:
    webcoll updates the collection cache (record universe for a
    given collection plus web page elements) based on invenio.conf and DB
    configuration parameters. If the collection name is passed as an argument,
    only this collection's cache will be updated. If the recursive option is
    set as well, the collection's descendants will also be updated.\n""",
            help_specific_usage="  -c, --collection\t Update cache for the given "
                     "collection only. [all]\n"
                    "  -r, --recursive\t Update cache for the given collection and all its\n"
                    "\t\t\t descendants (to be used in combination with -c). [no]\n"
                    "  -q, --quick\t\t Skip webpage cache update for those collections whose\n"
                    "\t\t\t reclist was not changed. Note: if you use this option, it is advised\n"
                    "\t\t\t to schedule, e.g. a nightly 'webcoll --force'. [no]\n"
                    "  -f, --force\t\t Force update even if cache is up to date. [no]\n"
                    "  -p, --part\t\t Update only certain cache parts (1=reclist,"
                    " 2=webpage). [both]\n"
                    "  -l, --language\t Update pages in only certain language"
                    " (e.g. fr,it,...). [all]\n",
            version=__revision__,
            specific_params=("c:rqfp:l:", [
                    "collection=",
                    "recursive",
                    "quick",
                    "force",
                    "part=",
                    "language="
                ]),
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_submit_check_options_fnc=task_submit_check_options,
            task_run_fnc=task_run_core)
