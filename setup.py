# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Invenio is a framework for digital libraries and data repositories.

Invenio enables you to run your own digital library or document
repository on the web.  Invenio covers all aspects of digital library
management, from document ingestion, through classification, indexing
and further processing, to curation, archiving, and dissemination.
The flexibility and performance of Invenio make it a comprehensive
solution for management of document repositories of moderate to large
sizes (several millions of records).

Links
-----

* `website <http://invenio-software.org/>`_
* `documentation <http://invenio.readthedocs.org/en/latest/>`_
* `development <https://github.com/inveniosoftware/invenio>`_

"""

import os
import sys

from setuptools import find_packages, setup

install_requires = [
    "Babel>=1.3",
    "backports.lzma>=0.0.3",
    "bagit>=1.5.1",
    "BeautifulSoup>=3.2.1",
    "BeautifulSoup4>=4.3.2",
    "celery>=3.1.8",
    # Cerberus>=0.7.1 api changes and is not yet supported
    "Cerberus>=0.7,<0.7.1",
    "chardet>=2.3.0",
    "dictdiffer>=0.0.3",
    "elasticsearch>=1.3.0",
    "feedparser>=5.1",
    "fixture>=1.5",
    "Flask>=0.10.1",
    "Flask-Admin>=1.1.0",
    "Flask-Assets>=0.10",
    "Flask-Babel>=0.9",
    "Flask-Breadcrumbs>=0.2",
    "Flask-Cache>=0.12",
    "Flask-Collect>=1.1.1",
    "Flask-Email>=1.4.4",
    "Flask-Gravatar>=0.4.2",
    "Flask-IIIF>=0.2.0",
    "Flask-Login>=0.2.7",
    "Flask-Menu>=0.2",
    "Flask-OAuthlib>=0.6.0,<0.7",  # quick fix for issue #2158
    "Flask-Principal>=0.4",
    "Flask-Registry>=0.2",
    "Flask-RESTful>=0.2.12",
    "Flask-Script>=2.0.5",
    "Flask-SQLAlchemy>=2.0",
    "Flask-WTF>=0.10.2",
    "cryptography>=0.6",
    "fs>=0.4",
    "idutils>=0.1.0",
    "intbitset>=2.0",
    "invenio-access>=0.1.0",
    "invenio-accounts>=0.1.2",
    "invenio-base>=0.2.1",
    "invenio-client>=0.1.0",
    "invenio-formatter>=0.2.0",
    "invenio-groups>=0.1.0",
    "invenio-search>=0.1.3",
    "invenio-collections>=0.1.2",
    "invenio-records>=0.3.3",
    "invenio-comments>=0.1.1",
    "invenio-oauthclient>=0.1.0",
    "invenio-oauth2server>=0.1.0",
    # TODO "invenio-messages>=0.1.0",
    "invenio-webhooks>=0.1.0",
    "invenio-knowledge>=0.1.0",
    "invenio-pidstore[datacite]>=0.1.0",
    "invenio-previewer>=0.1.0",
    "invenio-workflows>=0.1.0",
    "invenio-deposit>=0.1.0",
    "invenio-documents>=0.1.0.post2",
    "invenio-upgrader>=0.1.0",
    "invenio-unapi>=0.1.0",
    "invenio-utils>=0.1.0",
    "invenio-ext>=0.1.0",
    "itsdangerous>=0.24",
    "jellyfish>=0.3.2",
    "Jinja2>=2.7",
    "libmagic>=1.0",
    "lxml>=3.3",
    "mechanize>=0.2.5",
    "mistune>=0.4.1",
    "msgpack-python>=0.3",
    "MySQL-python>=1.2.5",
    "nydus>=0.10.8",
    # FIXME new oauthlib release after 0.7.2 has some compatible problems with
    # the used Flask-Oauthlib version.
    "oauthlib==0.7.2",
    "passlib>=1.6.2",
    # pyparsing>=2.0.2 has a new api and is not compatible yet
    "pyparsing>=2.0.1,<2.0.2",
    "python-twitter>=2.0",
    "pyPDF>=1.13",
    "pyPDF2>=1.17",
    "PyLD>=0.5.2",
    "pyStemmer>=1.3",
    "python-dateutil>=1.5",
    "python-magic>=0.4.6",
    "pytz>=2014.1",
    "rauth>=0.7.0",
    "raven>=5.0.0",
    "rdflib>=4.1.2",
    "redis>=2.8.0",
    "reportlab>=2.7,<3.2",
    "requests>=2.4",
    "setuptools>=2.2",
    "simplejson>=3.7",
    "six>=1.7.2",
    "toposort>=1.4",
    "Sphinx>=1.3",
    "SQLAlchemy>=1.0",
    "SQLAlchemy-Utils[encrypted]>=0.30.1",
    "toposort>=1.4",
    "unidecode>=0.04.1",
    "WTForms>=2.0.1",
    "WTForms-Alchemy>=0.13.1",
    "WTForms-SQLAlchemy>=0.1",
    "pyyaml>=3.11",
]


extras_require = {
    "docs": [
        "sphinx_rtd_theme>=0.1.7"
    ],
    "development": [
        "Flask-DebugToolbar==0.9.0",
        "watchdog==0.8.3",
    ],
    "dropbox": [
        "dropbox>=2.1.0"
    ],
    "elasticsearch": [
    ],
    "googledrive": [
        "google-api-python-client>=1.2",
        "apiclient>=1.0.0",
        "oauth2client>=1.4.0",
        "urllib3>=1.8.3"
    ],
    "iiif": [
        # promoted to required dependenies in 2.1
    ],
    "img": [
        "qrcode>=5.1",
        "Pillow>=2.7.0"
    ],
    "mongo": [
    ],
    "misc": [  # was requirements-extras
        "gnuplot-py==1.8",
        "flake8>=2.0.0",  # extra=kwalitee?
        "pychecker==0.8.19",  # extra=kwalitee?
        "pylint>=1.4.0",  # extra=kwalitee?
        "nosexcover>=1.0.0",  # test?
        "python-onedrive>=15.0.0",  # extra=cloud?
        "python-openid>=2.2.0",  # extra=sso?
    ],
    "mixer": [
        "mixer>=5.1.0",
    ],
    "sso": [
        "Flask-SSO>=0.2"
    ],
    "pages": [
        "invenio-pages>=0.1.0"
    ],
    "postgresql": [
        "psycopg2>=2.5",
    ],
    # Alternative XML parser
    #
    # For pyRXP, the version on PyPI many not be the right one.
    #
    # $ pip install
    # >    https://www.reportlab.com/ftp/pyRXP-1.16-daily-unix.tar.gz#egg=pyRXP
    #
    "pyrxp": [
        # Any other versions are not supported.
        "pyRXP==1.16-daily-unix"
    ],
    "rabbitmq": [
        "amqp>=1.4.5",
    ],
    "github": [
        "github3.py>=0.9"
    ],
}

extras_require["docs"] += extras_require["elasticsearch"]
extras_require["docs"] += extras_require["img"]
extras_require["docs"] += extras_require["mongo"]
extras_require["docs"] += extras_require["sso"]
extras_require["docs"] += extras_require["github"]
# FIXME extras_require["docs"] += extras_require["dropbox"]
# FIXME extras_require["docs"] += extras_require["googledrive"]

tests_require = [
    "httpretty>=0.8.10",
    "Flask-Testing>=0.4.1",
    "mock>=1.0.0",
    "nose>=1.3.0",
    "selenium>=2.45.0",
    "unittest2>=0.5",
]

setup_requires = [
    'Babel>=1.3',
]

# Add `tests` dependencies to `extras_require` so that developers
# could install test dependencies also with pip:
extras_require["tests"] = tests_require

# Compatibility with Python 2.6
if sys.version_info < (2, 7):
    install_requires += [
        "argparse>=1.3.0",
        "importlib>=1.0.0"
    ]


# Get the version string.  Cannot be done with import!
g = {}
with open(os.path.join("invenio", "version.py"), "rt") as fp:
    exec(fp.read(), g)
version = g["__version__"]

packages = find_packages(exclude=['docs'])
packages.append('invenio_docs')

setup(
    name='invenio',
    version=version,
    url='https://github.com/inveniosoftware/invenio',
    license='GPLv2',
    author='CERN',
    author_email='info@invenio-software.org',
    description='Invenio digital library framework',
    long_description=__doc__,
    packages=packages,
    package_dir={'invenio_docs': 'docs'},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    entry_points={
        'console_scripts': [
            # Legacy
            'dbexec = invenio.legacy.miscutil.scripts.dbexec:main',
        ],
    },
    setup_requires=setup_requires,
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2'
        ' or later (GPLv2+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    test_suite='invenio.testsuite.suite',
    tests_require=tests_require,
)
