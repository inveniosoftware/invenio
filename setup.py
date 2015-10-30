# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio Digital Library Framework."""

import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pep257>=0.7.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    'accounts': [
        'invenio-accounts>=1.0.0a1,<1.1.0',
    ],
    'records': [
        'invenio-pidstore>=1.0.0a1,<1.1.0',
        'invenio-records>=1.0.0a2,<1.1.0',
        'invenio-records-ui>=1.0.0a1,<1.1.0',
        'invenio-records-rest>=1.0.0a2,<1.1.0',
    ],
    'theme': [
        'invenio-assets>=1.0.0a1,<1.1.0',
        'invenio-theme>=1.0.0a3,<1.1.0',
    ],
    'utils': [
        'invenio-mail>=1.0.0a1,<1.1.0',
        'invenio-db>=1.0.0a5,<1.1.0',
        'invenio-rest>=1.0.0a2,<1.1.0',
        'invenio-logging>=1.0.0a1,<1.1.0',
    ],
    'docs': [
        'Sphinx>=1.3',
    ],
    'tests': tests_require,
}

#
# Aliases allow for easy installation of a specific type of Invenio instances.
#   pip install invenio[repository]
#
aliases = {
    'minimal': ['accounts', 'theme', 'utils', ],
    'full': ['accounts', 'records', 'theme', 'utils', ],
}

for name, requires in aliases.items():
    extras_require[name] = []
    for r in requires:
        extras_require[name].extend(extras_require[r])

# All alias to install every possible dependency.
extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)

#
# Minimal required packages for an Invenio instance (basically just the
# Flask application loading).
#
setup_requires = [
    'Babel>=1.3',
]

install_requires = [
    'invenio-base>=1.0.0a2,<1.1.0',
    'invenio-celery>=1.0.0a1,<1.1.0',
    'invenio-config>=1.0.0a1,<1.1.0',
    'invenio-i18n>=1.0.0a1,<1.1.0',
]

packages = find_packages()


class PyTest(TestCommand):
    """PyTest Test."""

    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        """Init pytest."""
        TestCommand.initialize_options(self)
        self.pytest_args = []
        try:
            from ConfigParser import ConfigParser
        except ImportError:
            from configparser import ConfigParser
        config = ConfigParser()
        config.read('pytest.ini')
        self.pytest_args = config.get('pytest', 'addopts').split(' ')

    def finalize_options(self):
        """Finalize pytest."""
        TestCommand.finalize_options(self)
        if hasattr(self, '_test_args'):
            self.test_suite = ''
        else:
            self.test_args = []
            self.test_suite = True

    def run_tests(self):
        """Run tests."""
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='Invenio digital library framework',
    license='GPLv2',
    author='CERN',
    author_email='info@invenio-software.org',
    url='https://github.com/inveniosoftware/invenio',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={},
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
    ],
    cmdclass={'test': PyTest},
)
