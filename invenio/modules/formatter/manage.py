# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""
Perform template migration operations.

Migrate output formats and output templates found in
``CFG_BIBFORMAT_OUTPUTS_PATH`` and ``CFG_BIBFORMAT_TEMPLATES_PATH``
respectively. It creates backup of each output format with name
``<FORMAT>_legacy.bfo`` and generates new Jinja2 templates in
``CFG_BIBFORMAT_JINJA_TEMPLATE_PATH``.
"""

from __future__ import print_function

import os
import re
import shutil

from six import iteritems

from invenio.ext.script import Manager

manager = Manager(usage="Perform template migration operations.")


@manager.option('--rewrite-existing-templates',
                dest='rewrite_existing_templates',
                action='store_true', default=False)
@manager.option('-t', '--template',
                dest='only_template_re', default=None,
                help="only templates matching regular expression")
@manager.option('--verbose', dest='verbose')
def bft2tpl(rewrite_existing_templates=False, only_template_re=None,
            verbose=0):
    """Convert *bft* templates to Jinja2 *tpl* templates."""
    # Import all invenio modules inside to avoid side-efects ouside
    # Flask application context.
    from invenio.modules.formatter.config import CFG_BIBFORMAT_OUTPUTS_PATH, \
        CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION, \
        CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION, \
        CFG_BIBFORMAT_FORMAT_JINJA_TEMPLATE_EXTENSION, \
        CFG_BIBFORMAT_JINJA_TEMPLATE_PATH
    from invenio.modules.formatter.engine import get_format_element, \
        get_output_formats, \
        pattern_function_params, \
        pattern_tag, pattern_lang, \
        translation_pattern, \
        ln_pattern, get_format_templates
    from invenio.legacy.bibformat.adminlib import \
        update_output_format_rules

    only_template = re.compile(only_template_re) \
        if only_template_re is not None else None

    def rename_template(template):
        if template[-3:] == CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION and \
                (only_template is None or only_template.match(template)):
            return template[:-3] + \
                CFG_BIBFORMAT_FORMAT_JINJA_TEMPLATE_EXTENSION
        return template

    def update_rule(rule):
        rule['template'] = rename_template(rule['template'])
        print('        ...', rule['template'], 'to', end=' ')
        print(rename_template(rule['template']))
        print('           ', rule)
        return rule

    def eval_format_template_elements(format_template, bfo, verbose=0):

        def insert_element_code(match):
            error = []
            function_name = match.group("function_name")
            try:
                format_element = get_format_element(function_name, verbose)
            except Exception:
                error.append('Invalid function name %s' % (function_name, ))

            params_str = []
            if format_element is not None:
                params = {}
                # Look for function parameters given in format template code
                all_params = match.group('params')
                if all_params is not None:
                    function_params_iterator = pattern_function_params.\
                        finditer(all_params)
                    for param_match in function_params_iterator:
                        sep = param_match.group('sep')
                        name = param_match.group('param')
                        value = param_match.group('value')
                        params[name] = value
                        params_str.append(name + '=' + sep + value + sep)

                # Replace element with function call with params.
                result = '{{ bfe_%s(bfo, %s) }}' % (function_name.lower(),
                                                    ', '.join(params_str))
                return result

            print('\n'.join(error))

        # Substitute special tags in the format by our own text.
        # Special tags have the form
        # <BFE_format_element_name [param="value"]* />
        format = pattern_tag.sub(insert_element_code, format_template)
        return format

    def translate(match):
        """Translate matching values."""
        word = match.group("word")
        translated_word = '{{ _("' + word + '") }}'
        return translated_word

    def filter_languages(format_template):
        """Filter languages in format template."""
        def search_lang_tag(match):
            """Searche for the <lang>...</lang> tag."""
            ln_tags = {}

            def clean_language_tag(match):
                """Return tag text content.

                It contains if statement block to match output language.
                It is called by substitution in 'filter_languages(...)'.

                @param match: a match object corresponding to the special tag
                              that must be interpreted
                """
                ln_tags[match.group(1)] = match.group(2)
                return '{% if g.ln == "' + match.group(1) + '" %}' + \
                    match.group(2) + '{% endif %}'

                # End of clean_language_tag

            lang_tag_content = match.group("langs")
            return '{% lang %}' + lang_tag_content + '{% endlang %}'
            cleaned_lang_tag = ln_pattern.sub(clean_language_tag,
                                              lang_tag_content)
            # FIXME no traslation for current language
            # if len(ln_tags) > 0:
            #    cleaned_lang_tag += '{% if not g.ln in ["' + \
            #        '", "'.join(ln_tags.keys()) + '"] %}' + \
            #        ln_tags.get(CFG_SITE_LANG, '') + '{% endif %}'
            return cleaned_lang_tag
            # End of search_lang_tag

        filtered_format_template = pattern_lang.sub(search_lang_tag,
                                                    format_template)
        return filtered_format_template

    skip_templates = lambda (name, key): name[-3:] != 'xsl'
    format_templates = filter(skip_templates,
                              iteritems(get_format_templates(True)))

    print('>>> Going to migrate %d format template(s) ...' % (
        len(format_templates), ))

    if not os.path.exists(CFG_BIBFORMAT_JINJA_TEMPLATE_PATH):
        os.makedirs(CFG_BIBFORMAT_JINJA_TEMPLATE_PATH)

    for name, template in format_templates:

        if not (only_template is None or only_template.match(name)):
            continue

        new_name = os.path.join(CFG_BIBFORMAT_JINJA_TEMPLATE_PATH,
                                rename_template(name))

        if os.path.exists(new_name):
            print('    [!] File', new_name, 'already exists.', end=' ')
            if not rewrite_existing_templates:
                print('Skipped.')
                continue
            else:
                shutil.copy2(new_name, new_name + '.backup')
                print('Rewritten.')

        print('    ... migrating', name, 'to', new_name)

        with open(new_name, 'w+') as f:
            code = template['code']
            ln_tags_format = filter_languages(code)
            localized_format = translation_pattern.sub(translate,
                                                       ln_tags_format)
            evaled = eval_format_template_elements(localized_format, None)
            f.write(evaled)

    print()

    skip_legacy = lambda (name, key): name[-11:] != '_legacy.' + \
        CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION
    output_formats = filter(
        skip_legacy, iteritems(get_output_formats(with_attributes=True)))
    print('>>> Going to migrate %d output format(s) ...' % (
        len(output_formats)))

    for name, output_format in output_formats:
        if not any(map(lambda rule: rule['template'][-3:] ==
                       CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION,
                       output_format['rules'])):
            print('    [!]', name, 'does not contain any', end=' ')
            print(CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION, 'template', end=' ')
            if only_template is not None:
                print('or does not match', only_template_re, end=' ')
            print('.')
            continue

        new_name = name[:-4] + \
            '_legacy.' + CFG_BIBFORMAT_FORMAT_OUTPUT_EXTENSION
        if os.path.exists(os.path.join(CFG_BIBFORMAT_OUTPUTS_PATH, new_name)):
            print('    [!] File', new_name, 'already exists. Skipped.')
            continue
        shutil.copy2(
            os.path.join(CFG_BIBFORMAT_OUTPUTS_PATH, name),
            os.path.join(CFG_BIBFORMAT_OUTPUTS_PATH, new_name))
        # rename template names
        print('    ... migrating', name, 'to', new_name)
        update_output_format_rules(name,
                                   map(update_rule, output_format['rules']),
                                   rename_template(output_format['default']))

    print()
    print('>>> Please re-run `bibreformat` for all cached output formats.')
    print('    $ bibreformat -oHB,HD -a')


@manager.option('-o', '--output-format', dest='output_format',
                default="HB", help="Specify output format/s (default HB)")
def expunge(output_format="HB"):
    """Remove static output formats from cache."""
    from invenio.ext.sqlalchemy import db
    from invenio.modules.formatter.models import Bibfmt

    # Make it uppercased as it is stored in database.
    output_format = output_format.upper()
    print(">>> Cleaning %s cache..." % (output_format, ))
    # Prepare where expression.
    filter_format = (
        Bibfmt.format == output_format if ',' not in output_format else
        Bibfmt.format.in_(map(lambda x: x.strip(), output_format.split(',')))
    )
    Bibfmt.query.filter(filter_format).delete(synchronize_session=False)
    db.session.commit()


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
