import logging

from amqp import ConnectionError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from mock import call, patch
from six.moves import queue as queue_six

from django_nameko import destroy_pool, get_pool, rpc
from nose import tools

settings.configure()
logger = logging.getLogger(__name__)


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'))
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


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'))
def test_get_pool():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        with pool.next() as client:
            client.foo.bar()
            assert call().start().foo.bar() in FakeClusterRpcProxy.mock_calls
        destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'), NAMEKO_POOL_SIZE=5)
def test_custom_pool_size():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        assert pool.queue.qsize() == 5
    destroy_pool()


@override_settings(NAMEKO_CONFIG=None)
def test_no_settings():
    tools.assert_raises(ImproperlyConfigured, get_pool)
    destroy_pool()


@override_settings(NAMEKO_CONFIG={'badkey': 'amqp://'})
def test_bad_settings():
    tools.assert_raises(ImproperlyConfigured, get_pool)
    destroy_pool()


@override_settings(NAMEKO_CONFIG={})
def test_abd_settings():
    tools.assert_raises(ImproperlyConfigured, get_pool)
    destroy_pool()


@override_settings(NAMEKO_CONFIG={'pool1': dict(AMQP_URI='amqp://')})
def test_missing_default_settings():
    tools.assert_raises(ImproperlyConfigured, get_pool)
    destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'), NAMEKO_CONTEXT_DATA={"data": 123})
def test_context_data():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        assert pool.context_data.get("data") == 123
        # ctx = pool.queue.get_nowait()
        # context_data = ctx.proxy._worker_ctx.data
        # assert context_data.get("data") == 123
        # ctx.stop()
    destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'))
def test_runtime_error():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        assert pool.queue.qsize() == 4, pool.queue.qsize()
        client = pool.next()
        # getting client out of pool without using context will make 1 connection go missing
        assert pool.queue.qsize() == 3, pool.queue.qsize()

        with client:
            client.foo.bar()
            assert call().start().foo.bar() in FakeClusterRpcProxy.mock_calls
            client._proxy = None  # this line will make this client become unusable as it is stopped

        assert pool.queue.qsize() == 4, pool.queue.qsize()
        with tools.assert_raises(RuntimeError):
            # try to loop through all connection in pool, the last one will failed due to RuntimeError
            for i in range(4):
                with pool.next():
                    assert pool.queue.qsize() == 3, pool.queue.qsize()
        # expect the pool to recover the stopped client
        assert pool.queue.qsize() == 4, pool.queue.qsize()

    destroy_pool()


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'))
def test_connection_error():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        pool = get_pool()
        assert pool.queue.qsize() == 4, pool.queue.qsize()
        client = pool.next()
        assert pool.queue.qsize() == 3, pool.queue.qsize()
        with tools.assert_raises(ConnectionError):
            with pool.next():
                assert pool.queue.qsize() == 2, pool.queue.qsize
                raise ConnectionError("connection closed")
        assert pool.queue.qsize() == 3, pool.queue.qsize
        # this has cleared all 4 proxy since runtimeerror is expected to broke them all
        with client:
            assert pool.queue.qsize() == 3, pool.queue.qsize()
            client.foo.bar()
            assert call().start().foo.bar() in FakeClusterRpcProxy.mock_calls
        assert pool.queue.qsize() == 4, pool.queue.qsize()

    destroy_pool()


@override_settings(NAMEKO_CONFIG={
    'default': {
        'AMQP_URI': 'amqp://'
    },
    'pool1': {
        'POOL_SIZE': 8,
    },
    'pool2': {
        'AMQP_URI': 'amqp://pool2'
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


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'))
def test_multi_pool_no_config():
    with patch('django_nameko.rpc.ClusterRpcProxy') as FakeClusterRpcProxy:
        tools.assert_raises(ImproperlyConfigured, lambda: get_pool('pool1'))
    destroy_pool()


@override_settings(NAMEKO_CONFIG={
    'default': {
        'AMQP_URI': 'amqp://',
        'POOL_SIZE': 4,
        'POOL_CONTEXT_DATA': {"common": "multi"},
        'POOL_TIMEOUT': None
    },
    'pool1': {
        'AMQP_URI': 'amqp://pool2',
        'POOL_CONTEXT_DATA': {"name": "pool1", "data": 123},
    },
    'pool2': {
        'AMQP_URI': 'amqp://pool3',
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


@override_settings(NAMEKO_CONFIG=dict(AMQP_URI='amqp://'))
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
        else:  # pragma: nocover
            raise AssertionError("AttributeError is expected when call rpc out of with statement")
        # try again inside with statement
        with pool.next() as client:
            client.bar.foo()
            assert call().start().bar.foo() in FakeClusterRpcProxy.mock_calls

        destroy_pool()
