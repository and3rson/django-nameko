#!/usr/bin/env python2

from setuptools import setup

setup(
    name='django-nameko',
    version='0.5.1',
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
