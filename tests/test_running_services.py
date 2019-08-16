# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import logging
import os
import socket
import subprocess
import time
import unittest
import sys

from amqp import AccessRefused
from django.conf import settings
from django.test.utils import override_settings
from nameko.exceptions import MethodNotFound, UnknownService

from django_nameko import destroy_pool, get_pool
from nose import tools
from tests.services import EchoService

logger = logging.getLogger(__name__)

if not settings.configured:  # pragma: nocover
    settings.configure()

config = {
    'AMQP_URI': 'amqp://guest:guest@localhost',
    'TIMEOUT': 1
}


class RealServiceTest(unittest.TestCase):
    runner = None  # type: subprocess.Popen

    @classmethod
    def setUpClass(cls):
        """
        run the service while in the context
        :return:
        """
        localdir = os.path.dirname(__file__)
        config = os.path.join(localdir, 'config.yaml')
        cls.runner = subprocess.Popen(('nameko', 'run', '--config', config, 'services'), cwd=localdir)
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.runner.kill()

    def test_echo_no_rpc(self):
        assert EchoService().echo(42) == (42,)

    @override_settings(NAMEKO_CONFIG={
        'AMQP_URI': 'amqp://guest:badpassword@localhost'
    })
    def test_pool_call_bad_rabbitmq_cred(self):
        with tools.assert_raises(AccessRefused):
            pool = get_pool()
            with pool.next() as client:
                client.echo.echo(42)

        destroy_pool()

    @unittest.skip("for some reason this test is broken and make tox hang forerver")
    @override_settings(NAMEKO_CONFIG={
        'AMQP_URI': 'amqp://guest:guest@localhost',
        'TIMEOUT': 1
    })
    def test_pool_call_unknown_service(self):
        with tools.assert_raises(UnknownService):
            pool = get_pool()
            with pool.next() as client:
                client.unknown_service.echo(42)

        destroy_pool()

    @override_settings(NAMEKO_CONFIG=config)
    def test_pool_call_method_notdefined(self):
        with tools.assert_raises(MethodNotFound):
            pool = get_pool()
            with pool.next() as client:
                client.echo.unknown_method()

        destroy_pool()

    @override_settings(NAMEKO_CONFIG={
        'AMQP_URI': 'amqp://guest:guest@localhost:6666'
    })
    def test_pool_call_no_rabbitmq_server(self):
        with tools.assert_raises(socket.error):
            pool = get_pool()
            with pool.next() as client:
                client.echo.echo(42)

        destroy_pool()

    @unittest.skipIf(sys.version_info > (3, 6), "currently eventlet is broken on python 3.7+")
    @override_settings(NAMEKO_CONFIG=config)
    def test_pool_call_existing_service(self):
        pool = get_pool()
        with pool.next() as client:
            assert client.echo.echo(42) == [42]

        # try to call RPC out of with statement
        tools.assert_raises(AttributeError, lambda: client.echo.echo(42))
        # try again inside with statement
        with pool.next() as client:
            assert client.echo.echo(42) == [42]

        destroy_pool()

    @override_settings(NAMEKO_CONFIG=config)
    def test_pool_destroy_and_recreate(self):
        pool = get_pool()
        with pool.next() as client:
            assert client.echo.echo(42) == [42]

        destroy_pool()
        pool = get_pool()
        with pool.next() as client:
            assert client.echo.echo(42) == [42]

        destroy_pool()

    @override_settings(NAMEKO_CONFIG=config, NAMEKO_CONTEXT_DATA={"data": 123})
    def test_error_clear_context(self):
        pool = get_pool()
        with tools.assert_raises(Exception):
            with pool.next() as client:
                client.service.method()
                raise Exception("oops")

        destroy_pool()
