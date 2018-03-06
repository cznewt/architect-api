# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION = '0.4'

with open('README.rst') as readme:
    LONG_DESCRIPTION = ''.join(readme.readlines())

with open('./requirements/base.txt') as _requirements:
    requirements = [r.strip() for r in _requirements.readlines()]

with open('./requirements/test.txt') as _tests_requirements:
    tests_requirements = [r.strip() for r in _tests_requirements.readlines()]

DESCRIPTION = "architect-api is a server API and UI of Architect, the service modeling, management and visualization platform."

setup(
    name='architect-api',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author='Aleš Komárek',
    author_email='ales.komarek@newt.cz',
    license='Apache License, Version 2.0',
    url='https://github.com/cznewt/architect-api/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    tests_require=tests_requirements,
    extras_require={
        'tests': [
            'pytest',
            'flake8'],
        'docs': [
            'sphinx',
            'sphinx_rtd_theme']
    },
    classifiers=[
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
