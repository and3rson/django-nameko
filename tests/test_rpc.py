from mock import patch, call
from django_nameko import rpc, get_pool, destroy_pool
from nose import tools
from six.moves import queue as queue_six
from django.test.utils import override_settings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


settings.configure()


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
