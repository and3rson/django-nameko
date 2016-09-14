from __future__ import absolute_import

import logging
import weakref
from threading import Lock

from six.moves import xrange as xrange_six, queue as queue_six

from nameko.standalone.rpc import ClusterRpcProxy
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_logger = logging.getLogger(__name__)


class ClusterRpcProxyPool(object):
    """ Connection pool for Nameko RPC cluster.

    Pool size can be customized by passing `pool_size` kwarg to constructor.
    Default size is 4.

    *Usage*

        pool = ClusterRpcProxyPool(config)
        pool.start()

        # ...

        with pool.next() as rpc:
            rpc.mailer.send_mail(foo='bar')

        # ...

        pool.stop()

    This class is thread-safe and designed to work with GEvent.
    """
    class RpcContext(object):
        def __init__(self, pool, config):
            self.pool = weakref.proxy(pool)
            self.proxy = ClusterRpcProxy(config)
            self.rpc = self.proxy.start()

        def stop(self):
            self.proxy.stop()
            self.proxy = None
            self.rpc = None

        def __enter__(self):
            return self.rpc

        def __exit__(self, *args, **kwargs):
            try:
                self.pool._put_back(self)
            except ReferenceError:  # pragma: no cover
                # We're detached from the parent, so this context
                # is going to silently die.
                self.stop()

    def __init__(self, config, pool_size=None):
        if pool_size is None:
            pool_size = getattr(settings, 'NAMEKO_POOL_SIZE', 4)
        self.config = config
        self.pool_size = pool_size

    def start(self):
        """ Populate pool with connections.
        """
        self.queue = queue_six.Queue()
        for i in xrange_six(self.pool_size):
            ctx = ClusterRpcProxyPool.RpcContext(self, self.config)
            self.queue.put(ctx)

    def next(self, timeout=False):
        """ Fetch next connection.

        This method is thread-safe.
        """
        return self.queue.get(timeout=False)

    def _put_back(self, ctx):
        self.queue.put(ctx)

    def stop(self):
        """ Stop queue and remove all connections from pool.
        """
        while True:
            try:
                ctx = self.queue.get_nowait()
                ctx.stop()
            except queue_six.Empty:
                break
        self.queue.queue.clear()
        self.queue = None


pool = None
create_pool_lock = Lock()


def get_pool():
    """
    Use this method to acquire connection pool.

    Example usage:

        from coreservices.core.rpc import get_pool
        # ...
        with get_pool().next() as rpc:
            rpc.mailer.send_mail(foo='bar')
    """
    create_pool_lock.acquire()
    global pool
    if not pool:
        # Lazy instantiation
        if not hasattr(settings, 'NAMEKO_CONFIG') or not settings.NAMEKO_CONFIG:
            raise ImproperlyConfigured('NAMEKO_CONFIG must be specified and should include at least "AMQP_URL" key.')
        pool = ClusterRpcProxyPool(settings.NAMEKO_CONFIG)
        pool.start()
    create_pool_lock.release()
    return pool


def destroy_pool():
    global pool
    pool = None
