from mock import patch, call
from django_nameko import rpc, get_pool, destroy_pool
from nose import tools
from six.moves import queue as queue_six
from django.test.utils import override_settings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import logging

settings.configure()
logger = logging.getLogger(__name__)


@override_settings(NAMEKO_CONFIG=dict(AMQP_URL='amqp://'))
def test_cluster_proxy_pool():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = rpc.ClusterRpcProxyPool(dict(), pool_size=2)
        pool.start()
        assert pool.queue.qsize() == 2

        with pool.next() as client:
            assert pool.queue.qsize() == 1

            client.foo.bar()
            assert call().start().foo.bar() in FakeClusterRpcProxy.mock_calls

            with pool.next():
                assert pool.queue.qsize() == 0

                tools.assert_raises(queue_six.Empty, pool.next, timeout=1)

            assert pool.queue.qsize() == 1
        assert pool.queue.qsize() == 2

        pool.stop()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URL='amqp://'))
def test_get_pool():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        with pool.next() as client:
            client.foo.bar()
            assert call().start().foo.bar() in FakeClusterRpcProxy.mock_calls
        destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URL='amqp://'), NAMEKO_POOL_SIZE=5)
def test_custom_pool_size():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        assert pool.queue.qsize() == 5
    destroy_pool()


@override_settings(NAMEKO_CONFIG=None)
def test_no_settings():
    tools.assert_raises(ImproperlyConfigured, get_pool)
    destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URL='amqp://'), NAMEKO_CONTEXT_DATA={"data": 123})
def test_context_data():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        assert pool.context_data.get("data") == 123
        # ctx = pool.queue.get_nowait()
        # context_data = ctx.proxy._worker_ctx.data
        # assert context_data.get("data") == 123
        # ctx.stop()
    destroy_pool()


@override_settings(NAMEKO_CONFIG={
    'default': {
        'AMQP_URL': 'amqp://'
    },
    'pool1': {
        'POOL_SIZE': 8,
    },
    'pool2': {
        'AMQP_URL': 'amqp://pool2'
    }
})
def test_multi_pool():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool_default = get_pool('default')
        pool_0 = get_pool()
        pool1 = get_pool('pool1')
        pool2 = get_pool('pool2')
        assert pool1 != pool2
        assert pool1.is_started and pool2.is_started
        assert pool_0.is_started and pool_default == pool_0
        assert pool1.config == pool_0.config
        assert pool1.queue.qsize() == 8
        assert pool2.config != pool_0.config
        tools.assert_raises(ImproperlyConfigured, lambda: get_pool('pool3'))

    destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URL='amqp://'))
def test_multi_pool_no_config():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        tools.assert_raises(ImproperlyConfigured, lambda: get_pool('pool1'))
    destroy_pool()


@override_settings(NAMEKO_CONFIG={
    'default': {
        'AMQP_URL': 'amqp://',
        'POOL_SIZE': 4,
        'POOL_CONTEXT_DATA': {"common": "multi"},
        'POOL_TIMEOUT': None
    },
    'pool1': {
        'AMQP_URL': 'amqp://pool2',
        'POOL_CONTEXT_DATA': {"name": "pool1", "data": 123},
    },
    'pool2': {
        'AMQP_URL': 'amqp://pool3',
        'POOL_CONTEXT_DATA': {"name": "pool2", "data": 321},
        'POOL_TIMEOUT': 60
    },
    'pool3': {
        'POOL_SIZE': 8,
        'POOL_TIMEOUT': 60
    }
})
def test_multi_pool_context_data():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool1 = get_pool('pool1')
        pool2 = get_pool('pool2')
        assert pool1.context_data.get("common") == "multi"
        assert pool2.context_data.get("common") == "multi"
        assert pool1.context_data.get("name") == "pool1"
        assert pool2.context_data.get("name") == "pool2"
        assert pool1.context_data.get("data") == 123
        assert pool2.context_data.get("data") == 321
        pool3 = get_pool('pool3')
        assert pool3.context_data.get("common") == "multi"
        assert pool3.context_data.get("name") is None
        assert pool3.queue.qsize() == 8
        assert pool1.is_started and pool2.is_started and pool3.is_started
        tools.assert_raises(ImproperlyConfigured, lambda: get_pool('pool4'))

    destroy_pool()

@override_settings(NAMEKO_CONFIG=dict(AMQP_URL='amqp://'))
def test_pool_call_rpc_out_of_with_statement():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        with pool.next() as client:
            client.foo.bar()
            assert call().start().foo.bar() in FakeClusterRpcProxy.mock_calls
        # try to call RPC out of with statement
        tools.assert_raises(AttributeError, lambda: client.foo.bar())
        try:
            client.bar.foo()
        except AttributeError:
            pass
        else:
            raise AssertionError("AttributeError is expected when call rpc out of with statement")
        # try again inside with statement
        with pool.next() as client:
            client.bar.foo()
            assert call().start().bar.foo() in FakeClusterRpcProxy.mock_calls

        destroy_pool()