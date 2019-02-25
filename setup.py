#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

__location__ = os.path.join(os.getcwd(), os.path.dirname(inspect.getfile(inspect.currentframe())))


def read_version(package):
    with open(os.path.join(package, '__init__.py'), 'r') as fd:
        for line in fd:
            if line.startswith('__version__ = '):
                return line.split()[-1].strip().strip("'")


version = read_version('specific')

install_requires = [
    'clickclick>=1.2',
    'jsonschema>=2.5.1,<3.0.0',
    'PyYAML>=3.13',
    'requests>=2.9.1',
    'six>=1.9',
    'inflection>=0.3.1',
    'pathlib>=1.0.1; python_version < "3.4"',
    'typing>=3.6.1; python_version < "3.6"',
    'openapi-spec-validator>=0.2.4',
    'flask>=0.10.1',
    'swagger-ui-bundle>=0.0.2'
]

tests_require = [
    'decorator',
    'mock',
    'pytest',
    'pytest-cov',
    'testfixtures'
]


class PyTest(TestCommand):

    user_options = [('cov-html=', None, 'Generate junit html report')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.pytest_args = ['--cov', 'specific', '--cov-report', 'term-missing', '-v']

        if sys.version_info < (3, 5, 3):
            self.pytest_args.append('--cov-config=py2-coveragerc')
            self.pytest_args.append('--ignore=tests/aiohttp')
        else:
            self.pytest_args.append('--cov-config=py3-coveragerc')

        self.cov_html = False

    def finalize_options(self):
        TestCommand.finalize_options(self)
        if self.cov_html:
            self.pytest_args.extend(['--cov-report', 'html'])
        self.pytest_args.extend(['tests'])

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def readme():
    try:
        return open('README.md', encoding='utf-8').read()
    except TypeError:
        return open('README.md').read()


setup(
    name='specific',
    packages=find_packages(),
    version=version,
    description='Specific - spec-first web framework',
    long_description=readme(),
    author='Daniel Grossmann-Kavanagh',
    url='https://github.com/dtkav/specific',
    keywords='openapi oai rest api oauth flask microservice framework',
    license='Apache License Version 2.0',
    setup_requires=['flake8'],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
    },
    cmdclass={'test': PyTest},
    test_suite='tests',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ],
    include_package_data=True,  # needed to include swagger-ui (see MANIFEST.in)
    entry_points={'console_scripts': ['specific = specific.cli:main']}
)
