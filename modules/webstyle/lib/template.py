## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio templating framework."""

__revision__ = "$Id$"

from invenio.config import CFG_WEBSTYLE_TEMPLATE_SKIN

def load(module=''):
    """ Load and returns a template class, given a module name (like
        'websearch', 'webbasket',...).  The module corresponding to
        the currently selected template model (see config.wml,
        variable CFG_TEMPLATE_SKIN) is tried first. In case it does
        not exist, it returns the default template for that module.
    """
    local = {}
    # load the right template based on the CFG_WEBSTYLE_TEMPLATE_SKIN and the specified module
    if CFG_WEBSTYLE_TEMPLATE_SKIN == "default":
        mymodule = __import__("invenio.%s_templates" % (module), local, local,
                              ["invenio.templates.%s" % (module)])
    else:    
        try:
            mymodule = __import__("invenio.%s_templates_%s" % (module, CFG_WEBSTYLE_TEMPLATE_SKIN), local, local,
                                  ["invenio.templates.%s_%s" % (module, CFG_WEBSTYLE_TEMPLATE_SKIN)])
        except ImportError:
            mymodule = __import__("invenio.%s_templates" % (module), local, local,
                                  ["invenio.templates.%s" % (module)])
    return mymodule.Template()
    
