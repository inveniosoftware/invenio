# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015, 2016 CERN.
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

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.35',
    'coverage>=4.4.1',
    'isort>=4.3',
    'pydocstyle>=2.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=2.5.1',
    'pytest-pep8>=1.0.6',
    'pytest>=3.3.1',
    'pytest-invenio>=1.0.0a1,<1.1.0',
]

db_version = '>=1.0.0b9,<1.1.0'
search_version = '>=1.0.0b5,<1.1.0'

extras_require = {
    # Bundles
    'base': [
        'invenio-admin>=1.0.0b4,<1.1.0',
        'invenio-assets>=1.0.0b7,<1.1.0',
        'invenio-formatter>=1.0.0b3,<1.1.0',
        'invenio-logging>=1.0.0b3,<1.1.0',
        'invenio-mail>=1.0.0b1,<1.1.0',
        'invenio-rest>=1.0.0b2,<1.1.0',
        'invenio-theme>=1.0.0b4,<1.1.0',
    ],
    'auth': [
        'invenio-access>=1.0.0b1,<1.1.0',
        'invenio-accounts>=1.0.0b12,<1.1.0',
        'invenio-oauth2server>=1.0.0b4,<1.1.0',
        'invenio-oauthclient>=1.0.0b5,<1.1.0',
        'invenio-userprofiles>=1.0.0b2,<1.1.0',
    ],
    'metadata': [
        'invenio-indexer>=1.0.0b2,<1.1.0',
        'invenio-jsonschemas>=1.0.0a7,<1.1.0',
        'invenio-oaiserver>=1.0.0b2,<1.1.0',
        'invenio-pidstore>=1.0.0b2,<1.1.0',
        'invenio-records-rest>=1.0.0b6,<1.1.0',
        'invenio-records-ui>=1.0.0b2,<1.1.0',
        'invenio-records>=1.0.0b4,<1.1.0',
        'invenio-search-ui>=1.0.0a9,<1.1.0',
    ],
    # Database version
    'postgresql': [
        'invenio-db[postgresql,versioning]{}'.format(db_version),
    ],
    'mysql': [
        'invenio-db[mysql,versioning]{}'.format(db_version),
    ],
    'sqlite': [
        'invenio-db[versioning]{}'.format(db_version),
    ],
    # Elasticsearch version
    'elasticsearch2': [
        'invenio-search[elasticsearch2]{}'.format(search_version),
    ],
    'elasticsearch5': [
        'invenio-search[elasticsearch5]{}'.format(search_version),
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]{}'.format(search_version),
    ],
    # Docs and test dependencies
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('sqlite', 'mysql', 'postgresql') \
            or name.startswith('elasticsearch'):
        continue
    extras_require['all'].extend(reqs)


setup_requires = [
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask>=0.11.1',
    'invenio-app>=1.0.0b2,<1.1.0'
    'invenio-base>=1.0.0b1,<1.1.0',
    'invenio-celery>=1.0.0b3,<1.1.0',
    'invenio-config>=1.0.0b4,<1.1.0',
    'invenio-i18n>=1.0.0b4,<1.1.0',
]

packages = find_packages()

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
    author_email='info@inveniosoftware.org',
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
        'Programming Language :: Python :: 3.5',
        'Development Status :: 3 - Alpha',
    ],
)
