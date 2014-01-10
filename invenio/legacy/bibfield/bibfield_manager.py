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

from invenio.ext.script import Manager

manager = Manager(usage="Perform BibField operations")

# Define sub-managers
bibfield_config = Manager(usage="Manipulates BibField config.")
bibfield_cache = Manager(usage="Manipulates BibField cache.")

# Add sub-managers
manager.add_command("config", bibfield_config)
manager.add_command("cache", bibfield_cache)


@bibfield_config.command
def load():
    """Loads BibField config."""
    print ">>> Going to load BibField config..."
    print ">>> Deprecated: use rediscli flushdb until a new version is ready"
    # from invenio.legacy.bibfield.config_engine import BibFieldParser
    # BibFieldParser().write_to_file()
    print ">>> BibField config load successfully."


@bibfield_cache.command
def reset(split_by=1000):
    """Reset record json structure cache."""
    from . import get_record
    from invenio.base.scripts.cache import reset_rec_cache
    reset_rec_cache('recjson', get_record, split_by=split_by)


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
