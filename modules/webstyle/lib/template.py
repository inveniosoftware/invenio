## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDSware templating framework."""

__version__ = "$Id$"

from cdsware.config import cfg_template_skin

def load(module=''):
    """ Load and returns a template class, given a module name (like
        'websearch', 'webbasket',...).  The module corresponding to
        the currently selected template model (see config.wml,
        variable CFG_TEMPLATE_SKIN) is tried first. In case it does
        not exist, it returns the default template for that module.
    """
    local = {}
    # load the right template based on the cfg_template_skin and the specified module
    if cfg_template_skin == "default":
        mymodule = __import__("cdsware.%s_templates" % (module), local, local,
                              ["cdsware.templates.%s" % (module)])
    else:    
        try:
            mymodule = __import__("cdsware.%s_templates_%s" % (module, cfg_template_skin), local, local,
                                  ["cdsware.templates.%s_%s" % (module, cfg_template_skin)])
        except ImportError:
            mymodule = __import__("cdsware.%s_templates" % (module), local, local,
                                  ["cdsware.templates.%s" % (module)])
    return mymodule.Template()
    
