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

manager = Manager(usage="Perform BibConvert operations")


@manager.command
def update():
    """Updates BibConvert templates.

    Update bibconvert/config/*.tpl files looking for 856
    http://.../CFG_SITE_RECORD lines, replacing URL with CFG_SITE_URL taken
    from conf file.  Note: this edits tpl files in situ, taking a
    backup first.  Use only when you know what you are doing.
    """
    print ">>> Going to update bibconvert templates..."
    import os
    import re
    import shutil
    from invenio.config import CFG_ETCDIR, CFG_SITE_RECORD, CFG_SITE_URL
    ## location where bibconvert/config/*.tpl are:
    tpldir = os.path.join(CFG_ETCDIR, 'bibconvert', 'config')
    ## find all *.tpl files:
    for tplfilename in os.listdir(tpldir):
        if tplfilename.endswith(".tpl"):
            ## change tpl file:
            tplfile = tpldir + os.sep + tplfilename
            shutil.copy(tplfile, tplfile + '.OLD')
            out = ''
            for line in open(tplfile, 'r').readlines():
                match = re.search(r'^(.*)http://.*?/%s/(.*)$' % CFG_SITE_RECORD, line)
                if match:
                    out += "%s%s/%s/%s\n" % (match.group(1),
                                             CFG_SITE_URL,
                                             CFG_SITE_RECORD,
                                             match.group(2))
                else:
                    out += line
            fdesc = open(tplfile, 'w')
            fdesc.write(out)
            fdesc.close()
    print ">>> bibconvert templates updated successfully."


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
