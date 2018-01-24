# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION = '0.2'

with open('README.rst') as readme:
    LONG_DESCRIPTION = ''.join(readme.readlines())

DESCRIPTION = """Architect API is server-side of service modeling,
management and visualization platform."""

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
    install_requires=[
        'Django',
        'django_neomodel',
        'django-jsonview',
        'django-yamlfield',
        'django-extensions',
        'django-material',
        'django-viewflow',
        'viewflow-extensions'
    ],
    extras_require={
        'tests': [
            'pytest',
            'flake8'],
        'docs': [
            'sphinx >= 1.4',
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
