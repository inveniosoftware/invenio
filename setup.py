# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Digital Library Framework."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'pytest-invenio>=1.3.2,<1.4.0',
]

db_version = '>=1.0.5,<1.1.0'
search_version = '>=1.3.1,<1.4.0'

extras_require = {
    # Bundles
    'base': [
        'invenio-admin>=1.2.1,<1.3.0',
        'invenio-assets>=1.2.3,<1.3.0',
        'invenio-formatter>=1.1.0a1,<1.2.0',
        'invenio-logging>=1.3.0,<1.4.0',
        'invenio-mail>=1.0.2,<1.1.0',
        'invenio-rest>=1.2.1,<1.3.0',
        'invenio-theme>=1.3.0a6,<1.4.0',
    ],
    'auth': [
        'invenio-access>=1.4.1,<1.5.0',
        'invenio-accounts>=1.4.0a4,<1.5.0',
        'invenio-oauth2server>=1.2.0,<1.3.0',
        'invenio-oauthclient>=1.3.0,<1.4.0',
        'invenio-userprofiles>=1.2.0a2,<1.3.0',
    ],
    'metadata': [
        'invenio-indexer>=1.1.1,<1.2.0',
        'invenio-jsonschemas>=1.1.0,<1.2.0',
        'invenio-oaiserver>=1.2.0,<1.3.0',
        'invenio-pidstore>=1.2.0,<1.3.0',
        'invenio-records-rest>=1.7.1,<1.8.0',
        'invenio-records-ui>=1.2.0a1,<1.3.0',
        'invenio-records>=1.3.1,<1.4.0',
        'invenio-search-ui>=2.0.0a2,<2.1.0',
    ],
    'files': [
        'invenio-files-rest>=1.2.0,<1.3.0',
        'invenio-iiif>=1.1.0,<1.2.0',
        'invenio-previewer>=1.2.1,<1.3.0',
        'invenio-records-files>=1.2.1,<1.3.0',
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
    'elasticsearch5': [
        'invenio-search[elasticsearch5]{}'.format(search_version),
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]{}'.format(search_version),
    ],
    'elasticsearch7': [
        'invenio-search[elasticsearch7]{}'.format(search_version),
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
    'invenio-app>=1.3.0,<1.4.0',
    'invenio-base>=1.2.3,<1.3.0',
    'invenio-cache>=1.1.0,<1.2.0',
    'invenio-celery>=1.2.0,<1.3.0',
    'invenio-config>=1.0.3,<1.1.0',
    'invenio-i18n>=1.3.0a1,<1.4.0',
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
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 5 - Production/Stable',
    ],
)
