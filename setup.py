#!/usr/bin/env python2
import os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'django_nameko/VERSION')) as f:
    __version__ = f.read()

from setuptools import setup

setup(
    name='django-nameko',
    version=__version__,
    description=' Django wrapper for nameko microservice framework.',
    url='http://github.com/and3rson/django-nameko',
    author='Andrew Dunai',
    author_email='andrew@dun.ai',
    maintainer='Vincent Anh Tran',
    maintainer_email='tranvietanh1991@gmail.com',
    license='GPLv2',
    packages=['django_nameko'],
    zip_safe=False,
    install_requires=[
        'nameko>=2.11.0',
        'django>=1.10,<2.0'
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
)
