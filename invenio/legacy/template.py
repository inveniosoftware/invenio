# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

from __future__ import print_function

"""Invenio templating framework."""

from __future__ import nested_scopes
import os, sys, inspect, getopt, new, cgi, warnings

try:
    # This tool can be run before Invenio is installed:
    # invenio files might then not exist.
    from invenio.base.globals import cfg
except ImportError:
    pass

#FIXME Change it if you want skin support for legacy modules :)
CFG_WEBSTYLE_PYLIBDIR = None
CFG_WEBSTYLE_TEMPLATE_SKIN = 'default'

# List of deprecated functions
# Eg. {'webstyle': {'tmpl_records_format_other':"Replaced by .."}}
CFG_WEBSTYLE_DEPRECATED_FUNCTIONS = {'webstyle': \
                            {'tmpl_records_format_other': "Replaced by " + \
                             "websearch_templates.tmpl_detailed_record_metadata(..), " + \
                             "websearch_templates.tmpl_detailed_record_references(..), " + \
                             "websearch_templates.tmpl_detailed_record_statistics(..), " + \
                             "webcomment_templates.tmpl_get_comments(..), " + \
                             "webcomment_templates.tmpl_mini_review(..)," + \
                             "websubmit_templates.tmpl_filelist(..) and " + \
                             "HDFILE + HDACT + HDREF output formats",
                             'detailed_record_container': "Replaced by " + \
                             "detailed_record_container_top and " + \
                             "detailed_record_container_bottom"},
                                     'websearch': \
                            {'tmpl_detailed_record_citations': "Replaced by " + \
                             "tmpl_detailed_record_citations_prologue" + \
                             "tmpl_detailed_record_citations_epilogue" + \
                             "tmpl_detailed_record_citations_citing_list" + \
                             "tmpl_detailed_record_citations_citation_history" + \
                             "tmpl_detailed_record_citations_cociting" + \
                             "tmpl_detailed_record_citations_self_cited"}
                            }

# List of deprecated parameter
# Eg. {'webstyle': {'get_page':{'header': "replaced by 'title'"}}}
CFG_WEBSTYLE_DEPRECATED_PARAMETERS = {}

# Thanks to Python CookBook for this!
def enhance_method(module, klass, method_name, replacement):
    old_method = getattr(klass, method_name)
    try:
        if type(old_method) is not new.instancemethod or old_method.__name__ == 'new_method':
            ## not a method or Already wrapped
            return
    except AttributeError:
        raise '%s %s %s %s' % (module, klass, method_name, old_method)
    def new_method(*args, **kwds):
        return replacement(module, old_method, method_name, *args, **kwds)
    setattr(klass, method_name, new.instancemethod(new_method, None, klass))

def method_wrapper(module, old_method, method_name, self, *args, **kwds):
    def shortener(text):
        if len(text) > 205:
            return text[:100] + ' ... ' + text[-100:]
        else:
            return text
    ret = old_method(self, *args, **kwds)
    if ret and type(ret) is str:
        params = ', '.join([shortener(repr(arg)) for arg in args] + ['%s=%s' % (item[0], shortener(repr(item[1]))) for item in kwds.items()])
        signature = '%s_templates/%s(%s)' % (module, method_name, params)
        signature_q = '%s_templates/%s' % (module, method_name)
        return '<span title="%(signature)s" style="border: thin solid red;"><!-- BEGIN TEMPLATE %(signature_q)s BEGIN TEMPLATE --><span style="color: red; font-size: xx-small; font-style: normal; font-family: monospace; float: both">*</span>%(result)s<!-- END TEMPLATE %(signature_q)s END TEMPLATE --></span>' % {
            'signature_q' : cgi.escape(signature_q),
            'signature' : cgi.escape(signature, True),
            'result' : ret
            }
    else:
        return ret

def load(module='', prefix=''):
    """ Load and returns a template class, given a module name (like
        'websearch', 'webbasket',...).  The module corresponding to
        the currently selected template model (see invenio.conf,
        variable CFG_WEBSTYLE_TEMPLATE_SKIN) is tried first. In case it does
        not exist, it returns the default template for that module.
    """
    local = {}
    # load the right template based on the CFG_WEBSTYLE_TEMPLATE_SKIN and the specified module
    if CFG_WEBSTYLE_TEMPLATE_SKIN == "default":
        try:
            mymodule = __import__("invenio.%s_%stemplates" % (module, prefix), local,
                                  local, ["invenio.legacy.%s.templates" % (module)])
        except ImportError:
            mymodule = __import__("invenio.legacy.%s.%stemplates" % (module, prefix),
                                  local, local,
                                  ["invenio.legacy.%s.templates" % (module)])
    else:
        try:
            mymodule = __import__("invenio.legacy.%s.templates_%s" % (module, CFG_WEBSTYLE_TEMPLATE_SKIN), local, local,
                                  ["invenio.legacy.%s.templates" % (module, CFG_WEBSTYLE_TEMPLATE_SKIN)])
        except ImportError:
            mymodule = __import__("invenio.legacy.%s.templates" % (module), local, local,
                                  ["invenio.legacy.%s.templates" % (module)])
    if 'inspect-templates' in cfg.get('CFG_DEVEL_TOOLS', []):
        for method_name in dir(mymodule.Template):
            if method_name.startswith('tmpl_'):
                enhance_method(module, mymodule.Template, method_name, method_wrapper)

    return mymodule.Template()

# Functions to check that customized templates functions conform to
# the default templates functions
#

def check(default_base_dir=None, custom_base_dir=None):
    """
    Check that installed customized templates are conform to the
    default templates interfaces.

    Result of the analysis is reported back in 'messages' object
    (see 'messages' structure description in print_messages(..) docstring)
    """
    messages = []

    if CFG_WEBSTYLE_PYLIBDIR is None:
        # Nothing to check, since Invenio has not been installed
        messages.append(('C', "Nothing to check. Run 'make install' first.",
                         '',
                         None,
                         0))
        return messages

    # Iterage over all customized templates
    for (default_template_path, custom_template_path) in \
        get_custom_templates(get_default_templates(default_base_dir), custom_base_dir):

        # Load the custom and default templates
        default_tpl_path, default_tpl_name = os.path.split(default_template_path)
        if default_tpl_path not in sys.path:
            sys.path.append(default_tpl_path)
        custom_tpl_path, custom_tpl_name = os.path.split(custom_template_path)
        if custom_tpl_path not in sys.path:
            sys.path.append(custom_tpl_path)

        default_template = __import__(default_tpl_name[:-3],
                                      globals(),
                                      locals(),
                                      [''])
        custom_template = __import__(custom_tpl_name[:-3],
                                     globals(),
                                     locals(),
                                     [''])

        # Check if Template class is in the file
        classes = inspect.getmembers(custom_template, inspect.isclass)
        if 'Template' not in [possible_class[0] for possible_class in classes]:
            messages.append(('E', "'Template' class missing",
                             custom_template.__name__,
                             None,
                             0))
            continue

        # Check customized functions parameters
        for (default_function_name, default_function) in \
                inspect.getmembers(default_template.Template, inspect.isroutine):
            if default_function_name in custom_template.Template.__dict__:
                # Customized function exists
                custom_function = custom_template.Template.__dict__[default_function_name]

                (deft_args, deft_varargs, deft_varkw, deft_defaults) = \
                            inspect.getargspec(default_function.im_func)
                (cust_args, cust_varargs, cust_varkw, cust_defaults) = \
                            inspect.getargspec(custom_function)
                deft_args.reverse()
                if deft_defaults is not None:
                    deft_defaults_list = list(deft_defaults)
                    deft_defaults_list.reverse()
                else:
                    deft_defaults_list = []

                cust_args.reverse()
                if cust_defaults is not None:
                    cust_defaults_list = list(cust_defaults)
                    cust_defaults_list.reverse()
                else:
                    cust_defaults_list = []

                arg_errors = False
                # Check for presence of missing parameters in custom template
                for deft_arg in deft_args:
                    if deft_arg not in cust_args:
                        arg_errors = True
                        messages.append(('E', "missing '%s' parameter" % \
                                         deft_arg,
                                         custom_tpl_name,
                                         default_function_name,
                                         inspect.getsourcelines(custom_function)[1]))

                # Check for presence of additional parameters in custom template
                for cust_arg in cust_args:
                    if cust_arg not in deft_args:
                        arg_errors = True
                        messages.append(('E', "unknown parameter '%s'" % \
                                         cust_arg,
                                         custom_tpl_name,
                                         custom_function.__name__,
                                         inspect.getsourcelines(custom_function)[1]))
                        # If parameter is deprecated, report it
                        module_name = default_tpl_name.split("_")[0]
                        if module_name in CFG_WEBSTYLE_DEPRECATED_PARAMETERS and \
                               default_function_name in CFG_WEBSTYLE_DEPRECATED_PARAMETERS[module_name] and \
                               cust_arg in CFG_WEBSTYLE_DEPRECATED_PARAMETERS[module_name][default_function_name]:
                            messages.append(('C', CFG_WEBSTYLE_DEPRECATED_PARAMETERS[module_name][default_function_name][cust_arg],
                                             custom_tpl_name,
                                             custom_function.__name__,
                                             inspect.getsourcelines(custom_function)[1]))

                # Check for same ordering of parameters.
                # Only raise warning if previous parameter tests did
                # not generate errors
                if not arg_errors:
                    for cust_arg, deft_arg in map(None, cust_args, deft_args):
                        if deft_arg != cust_arg:
                            arg_errors = True
                            messages.append(('W', "order of parameters is not respected",
                                             custom_tpl_name,
                                             custom_function.__name__,
                                             inspect.getsourcelines(custom_function)[1]))
                            break

                # Check for equality of default parameters values
                # Only raise warning if previous parameter tests did
                # not generate errors or warnings
                if not arg_errors:
                    i = 0
                    for cust_default, deft_default in \
                            map(None, cust_defaults_list, deft_defaults_list):
                        if deft_default != cust_default:
                            messages.append(('W', "default value for parameter '%s' is not respected" % \
                                             cust_args[i],
                                             custom_tpl_name,
                                             default_function_name,
                                             inspect.getsourcelines(custom_function)[1]))
                        i += 1

            else:
                # Function is not in custom template. Generate warning?
                pass

        # Check for presence of additional functions in custom template
        for (custom_function_name, custom_function) in \
                inspect.getmembers(custom_template.Template, inspect.isroutine):

            if custom_function_name not in default_template.Template.__dict__:
                messages.append(('W', "unknown function",
                                 custom_tpl_name,
                                 custom_function_name,
                                 inspect.getsourcelines(custom_function)[1]))

                # If the function was deprecated, report it
                module_name = default_tpl_name.split("_")[0]
                if module_name in CFG_WEBSTYLE_DEPRECATED_FUNCTIONS and \
                       custom_function_name in CFG_WEBSTYLE_DEPRECATED_FUNCTIONS[module_name]:
                    messages.append(('C', CFG_WEBSTYLE_DEPRECATED_FUNCTIONS[module_name][custom_function_name],
                                 custom_tpl_name,
                                 custom_function_name,
                                 inspect.getsourcelines(custom_function)[1]))

    return messages

# Utility functions
#

def get_default_templates(base_dir=None):
    """
    Returns the paths to all default Invenio templates.

    base_dir - path to where templates should be recursively searched
    """
    # If base_dir is not specified we assume that this template.py
    # file is located in modules/webstyle/lib, which allows
    # us to guess where base Invenio modules dir is.
    # Note that by luck it also works if file is installed
    # in /lib/python/invenio/

    if base_dir is None:
        # Retrieve path to Invenio 'modules' dir
        this_pathname = os.path.abspath(sys.argv[0])
        #this_pathname = inspect.getsourcefile(get_default_templates)
        this_dir, this_name = os.path.split(this_pathname)
        base_dir =  this_dir + os.sep + os.pardir + \
                   os.sep + os.pardir
    else:
        base_dir = os.path.abspath(base_dir)

    templates_path = []
    for (dirpath, dirnames, filenames) in os.walk(base_dir):
        for filename in filenames:
            if filename.endswith("templates.py"):
                templates_path.append(os.path.join(dirpath, filename))

    return templates_path

def get_custom_templates(default_templates_paths, base_dir=None):
    """
    Returns the paths to customized templates among the given list of
    templates paths.
    """
    return [(default, get_custom_template(default, base_dir)) \
            for default in default_templates_paths \
            if get_custom_template(default, base_dir) is not None]

def get_custom_template(default_template_path, base_dir=None):
    """
    Returns the path to the customized template of the default
    template given as parameter. Returns None if customized does not
    exist.
    """
    default_tpl_path, default_tpl_name = os.path.split(default_template_path)

    if base_dir is None:
        custom_path = CFG_WEBSTYLE_PYLIBDIR + \
                      os.sep + "invenio" + os.sep + \
                      default_tpl_name[:-3] + '_' + \
                      CFG_WEBSTYLE_TEMPLATE_SKIN + '.py'
    else:
        custom_path = os.path.abspath(base_dir) + os.sep + \
                      default_tpl_name[:-3] + '_' + \
                      CFG_WEBSTYLE_TEMPLATE_SKIN + '.py'

    if os.path.exists(custom_path):
        return custom_path
    else:
        return None

def print_messages(messages,
                   verbose=2):
    """
    Report errors and warnings to user.

    messages - list of tuples (type, message, template, function, line)
               where:  - type : One of the strings:
                                 - 'E': Error
                                 - 'W': Warning
                                 - 'C': Comment
                       - message : The string message
                       - template : template name where message occurred
                       - function : function name where message occurred
                       - line : line number where message occurred

    verbose  - int specifying the verbosity of the output.
               0 - summary only
               1 - summary + errors
               2 - summary + errors + warnings
               3 - summary + errors + warnings + comments
    """
    last_template = '' # Remember last considered template in order to
                       # print separator between templates

    for message in messages:
        if message[0] == 'F' and verbose >= 0 or \
           message[0] == 'E' and verbose >= 1 or \
           message[0] == 'W' and verbose >= 2 or \
           message[0] == 'C' and verbose >= 3:

            # Print separator if we have moved to another template
            if last_template != message[2]:
                print("************* Template %s" % message[2])
                last_template = message[2]

            print('%s:%s:%s%s' % \
                  (message[0],
                   message[4],
#                   message[2].endswith('.py') and message[2][:-3] or \
#                   message[2],
                   message[3] and ("%s(): " % message[3]) or ' ',
                   message[1]))

    # Print summary
    if verbose >= 0:
        nb_errors   = len([message for message in messages \
                           if message[0] == 'E'])
        nb_warnings = len([message for message in messages \
                           if message[0] == 'W'])
        nb_comments = len([message for message in messages \
                           if message[0] == 'C'])

        if len(messages) > 0:
            print('\nFAILED')
        else:
            print('\nOK')

        print("%i error%s, %i warning%s, %i comment%s." % \
              (nb_errors,   nb_errors   > 1 and 's' or '',
               nb_warnings, nb_warnings > 1 and 's' or '',
               nb_comments, nb_comments > 1 and 's' or ''))

def usage(exitcode=1):
    """
    Print usage of the template checking utility
    """

    print("""Usage: python templates.py --check-custom-templates [options]
Options:
  -v, --verbose                Verbose level (0=min, 2=default, 3=max).
  -d, --default-templates-dir  path to a directory with the default
                               template(s) (default: Invenio install
                               dir if run from Invenio install dir, or
                               Invenio source if run from Invenio sources)
  -c, --custom-templates-dir   path to a directory with your custom
                               template(s) (default: Invenio install dir)
  -h, --help                   Prints this help
Check that your custom templates are synchronized with default Invenio templates.
Examples: $ python templates.py --check-custom-templates
          $ python templates.py --check-custom-templates -c~/webstyle_template_ithaca.py
""")
    sys.exit(exitcode)

if __name__ == "__main__" and \
       '--check-custom-templates' in sys.argv:
    default_base_dir = None
    custom_base_dir = None
    verbose = 2
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:d:c:",
                                   ["help",
                                    "verbose=",
                                    "default-templates-dir=",
                                    "custom-templates-dir=",
                                    "check-custom-templates"])
    except getopt.GetoptError as err:
        usage(1)
    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage()
            elif opt[0] in ["-v", "--verbose"]:
                verbose = opt[1]
            elif opt[0] in ["-d", "--default-templates-dir"]:
                default_base_dir = opt[1]
            elif opt[0] in ["-c", "--custom-templates-dir"]:
                custom_base_dir = opt[1]

    except StandardError as e:
        usage(1)

    messages_ = check(default_base_dir, custom_base_dir)
    print_messages(messages_, verbose=verbose)
