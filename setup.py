# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2026 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Digital Library Framework."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'pytest-invenio>=4.0.0,<5.0.0',
]

db_version = '>=2.0.0,<3.0.0'
search_version = '>=3.0.0,<4.0.0'

extras_require = {
    # Bundles
    'base': [
        'invenio-admin>=1.6.0,<2.0.0',
        'invenio-assets>=4.0.0,<5.0.0',
        'invenio-formatter>=4.0.0,<5.0.0',
        'invenio-logging>=4.0.0,<5.0.0',
        'invenio-mail>=2.0.0,<3.0.0',
        'invenio-rest>=3.0.0,<4.0.0',
        'invenio-theme>=4.0.0,<5.0.0',
    ],
    'auth': [
        'invenio-access>=5.0.0,<6.0.0',
        'invenio-accounts>=7.0.0,<8.0.0',
        'invenio-oauth2server>=4.0.0,<5.0.0',
        'invenio-oauthclient>=7.0.0,<8.0.0',
        'invenio-userprofiles>=5.0.0,<6.0.0',
    ],
    'metadata': [
        'invenio-indexer>=4.0.0,<5.0.0',
        'invenio-jsonschemas>=2.0.0,<3.0.0',
        'invenio-oaiserver>=4.0.0,<5.0.0',
        'invenio-pidstore>=3.0.0,<4.0.0',
        'invenio-records-rest>=4.0.0,<5.0.0',
        'invenio-records-ui>=3.0.0,<4.0.0',
        'invenio-records>=4.0.0,<5.0.0',
        'invenio-search-ui>=4.0.0,<5.0.0',
    ],
    'files': [
        'invenio-files-rest>=4.0.0,<5.0.0',
        'invenio-previewer>=4.0.0,<5.0.0',
        'invenio-records-files>=2.0.0,<3.0.0',
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
    # Search engine version
    'elasticsearch7': [
        'invenio-search[elasticsearch7]{}'.format(search_version),
    ],
    'opensearch1': [
        'invenio-search[opensearch1]{}'.format(search_version),
    ],
    'opensearch2': [
        'invenio-search[opensearch2]{}'.format(search_version),
    ],
    # Docs and test dependencies
    'docs': [
        'Sphinx>=4.2.0,<5',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('sqlite', 'mysql', 'postgresql') \
            or name.startswith('elasticsearch') \
            or name.startswith('opensearch'):
        continue
    extras_require['all'].extend(reqs)


install_requires = [
    'invenio-app>=3.0.0,<4.0.0',
    'invenio-base>=2.1.0,<3.0.0',
    'invenio-cache>=3.0.0,<4.0.0',
    'invenio-celery>=2.0.0,<3.0.0',
    'invenio-config>=1.0.3,<2.0.0',
    'invenio-i18n>=3.0.0,<4.0.0',
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
    long_description=readme,
    keywords='Invenio digital library framework',
    license='MIT',
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
    tests_require=tests_require,
    python_requires='>=3.9',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Development Status :: 5 - Production/Stable',
    ],
)
