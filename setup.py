#!/usr/bin/env python2

from setuptools import setup

setup(
    name='django-nameko',
    version='0.2',
    description=' Django wrapper for nameko microservice framework.',
    url='http://github.com/and3rson/django-nameko',
    author='Andrew Dunai',
    author_email='andrew@dun.ai',
    license='GPLv2',
    packages=['django_nameko'],
    zip_safe=False,
    install_requires=[
        'nameko',
        'django'
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
)
