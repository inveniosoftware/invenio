# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2015 CERN.
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

"""Support passing legacy Invenio str objects to Jinja2 templates."""

import warnings

try:
    from markupsafe import Markup as jinja2_Markup, escape as jinja2_escape
except ImportError:
    from jinja2._markupsafe import Markup as jinja2_Markup, \
        escape as jinja2_escape

from invenio.utils.deprecation import RemovedInInvenio22Warning

warnings.warn(
    "Jinja2Hacks will be disabled in 2.1 and removed in 2.2. "
    "Please convert all strings in Jinja2 templates to unicode.",
    RemovedInInvenio22Warning
)


def setup_app(app):
    """Jinja2 require all strings to be unicode objects.

    Invenio however operates with UTF8 encoded str objects. Jinja2 will
    automatically convert non-unicode objects into unicode objects, but via the
    ascii codec. This function replaces the escape function and Markup class in
    Jinja2/MarkupSafe, to use the utf8 codec when converting 8-bit str objects
    into unicode objects.

    Ideally Jinja2/MarkupSafe should allow specifying which default encoding to
    use when decoding strings. Other alternatives is to decode any str object
    into unicode prior to passing the values to Jinja2 methods. This will
    however require large changes over the entire Invenio codebase, with the
    risk of introducing many errors. This runtime hack is unfortunately
    currently the least intrusive way to fix the str to unicode decoding.
    """
    # Jinja2 will try to load escape method and Markup class from a variety of
    # different modules. First it will try from MarkupSafe package, then from
    # jinja2._markupsafe._speedup, then jinja2._markupsafe._native. Ideally, we
    # should only replace the function and class at the implementing module.
    # However, due to Python's package/module loading behaviour, the function
    # and class will be imported into other jinja2 modules as soon as we try to
    # import the module implementing the function and class. Hence, we need to
    # replace the function and class in the modules where it has already been
    # imported.
    import jinja2
    import jinja2.runtime
    import jinja2.utils
    import jinja2.nodes
    import jinja2.filters
    import jinja2.ext
    import jinja2.environment
    import jinja2.compiler

    # Escape function replacement in Jinja2 library
    try:
        jinja2._markupsafe.escape = utf8escape
    except AttributeError:
        pass
    jinja2.runtime.escape = utf8escape
    jinja2.utils.escape = utf8escape
    jinja2.filters.escape = utf8escape
    jinja2.compiler.escape = utf8escape
    jinja2.escape = utf8escape

    # Markup class replacement in Jinja2 library
    try:
        jinja2._markupsafe.Markup = Markup
    except AttributeError:
        pass
    jinja2.runtime.Markup = Markup
    jinja2.utils.Markup = Markup
    jinja2.filters.Markup = Markup
    jinja2.compiler.Markup = Markup
    jinja2.Markup = Markup
    jinja2.nodes.Markup = Markup
    jinja2.ext.Markup = Markup
    jinja2.environment.Markup = Markup

    # Escape/Markup replacement in MarkupSafe library.
    # FIXME causes recursive calls in `Markup.__new__` and `escape`
    # try:
    #    import markupsafe
    #    markupsafe.escape = utf8escape
    #    #markupsafe.Markup = Markup
    # except ImportError:
    #    pass

    return app


def utf8escape(s):
    """UTF8-8-bit-string-friendly replacement for MarkupSafe escape function.

    WARNING: Do not use this method. Use jinja2.escape() instead.
    """
    if isinstance(s, str):
        warnings.warn("Convert string '{0}' in template to unicode.".format(s),
                      DeprecationWarning, stacklevel=3)
        return jinja2_escape(s.decode('utf8'))
    return jinja2_escape(s)
# Ensure function name is identical to replaced function.
utf8escape.__name__ = jinja2_escape.__name__


class Markup(jinja2_Markup):

    """Markup replacement class.

    Forces the use of utf8 codec for decoding 8-bit strings, in case no
    encoding is specified.

    WARNING: Do not use this class. Use jinja2.Markup instead.
    """

    def __new__(cls, base=u'', encoding=None, errors='strict'):
        """Add encoding for base of type str."""
        if encoding is None and isinstance(base, str):
            encoding = 'utf8'
            warnings.warn(
                "Convert string '{0}' in template to unicode.".format(base),
                DeprecationWarning, stacklevel=3)
        return jinja2_Markup.__new__(cls, base=base, encoding=encoding,
                                     errors=errors)
