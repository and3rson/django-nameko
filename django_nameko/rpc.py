#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#
#  Created by Vincent Anh Tran on 21/03/2018
#  Copyright (c) Vincent Anh Tran - maintain this project since 0.1.1
#
from __future__ import absolute_import

import logging
import weakref
from threading import Lock

from six.moves import xrange as xrange_six, queue as queue_six
from amqp.exceptions import ConnectionError
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
            self.proxy = ClusterRpcProxy(config, context_data=pool.context_data, timeout=pool.timeout)
            self.rpc = self.proxy.start()

        def stop(self):
            self.proxy.stop()
            self.proxy = None
            self.rpc = None

        def __enter__(self):
            return self.rpc

        def __exit__(self, exc_type, exc_value, traceback, **kwargs):
            try:
                if exc_type == RuntimeError and (
                        exc_value == "This consumer has been stopped, and can no longer be used"
                        or exc_value == "This consumer has been disconnected, and can no longer be used"):
                    self.pool._clear()
                    self.pool._reload()  # reload all worker
                    self.stop()
                elif exc_type == ConnectionError:  # maybe check for RpcTimeout, as well
                    # self.pool._clear()
                    self.pool._reload(1)  # reload atmost 1 worker
                    self.stop()
                else:
                    self.pool._put_back(self)
            except ReferenceError:  # pragma: no cover
                # We're detached from the parent, so this context
                # is going to silently die.
                self.stop()

    def __init__(self, config, pool_size=None, context_data=None, timeout=0):
        if pool_size is None:  # keep this for compatiblity
            pool_size = getattr(settings, 'NAMEKO_POOL_SIZE', 4)
        if context_data is None:  # keep this for compatiblity
            context_data = getattr(settings, 'NAMEKO_CONTEXT_DATA', None)
        if timeout <= 0:  # keep this for compatiblity
            timeout = getattr(settings, 'NAMEKO_TIMEOUT', None)
        self.config = config
        self.pool_size = pool_size
        self.context_data = context_data
        self.timeout = timeout
        self.state = 'NOT_STARTED'

    def start(self):
        """ Populate pool with connections.
        """
        self.queue = queue_six.Queue()
        for i in xrange_six(self.pool_size):
            ctx = ClusterRpcProxyPool.RpcContext(self, self.config)
            self.queue.put(ctx)
        self.state = 'STARTED'

    @property
    def is_started(self):
        return self.state != 'NOT_STARTED'

    def _clear(self):
        count = 0
        while self.queue.empty() is False:
            self.next()
            count += 1
        _logger.debug("Clear %d worker", count)

    def _reload(self, num_of_worker=0):
        """ Reload into pool's queue with number of new worker

        :param num_of_worker: 
        :return: 
        """
        if num_of_worker <= 0:
            num_of_worker = self.pool_size
        count = 0
        for i in xrange_six(num_of_worker):
            if self.queue.full() is False:
                ctx = ClusterRpcProxyPool.RpcContext(self, self.config)
                self.queue.put_nowait(ctx)
                count += 1
        _logger.debug("Reload %d worker", count)

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


def mergedicts(dict1, dict2):
    for k in set(dict1.keys()).union(dict2.keys()):
        if k in dict1 and k in dict2:
            if isinstance(dict1[k], dict) and isinstance(dict2[k], dict):
                yield (k, dict(mergedicts(dict1[k], dict2[k])))
            else:
                # If one of the values is not a dict, you can't continue merging it.
                # Value from second dict overrides one in first and we move on.
                yield (k, dict2[k])
                # Alternatively, replace this with exception raiser to alert you of value conflicts
        elif k in dict1:
            yield (k, dict1[k])
        else:
            yield (k, dict2[k])


def get_pool(pool_name=None):
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
    NAMEKO_CONFIG = getattr(settings, 'NAMEKO_CONFIG', {})
    if not NAMEKO_CONFIG:
        raise ImproperlyConfigured('NAMEKO_CONFIG must be specified')
    NAMEKO_MULTI_POOL = [name for name in NAMEKO_CONFIG.keys() if name.islower()]
    if not pool:
        # Lazy instantiation
        if NAMEKO_MULTI_POOL:
            pool = dict()
            if 'default' not in NAMEKO_CONFIG and 'AMQP_URL' not in NAMEKO_CONFIG['default']:
                raise ImproperlyConfigured(
                    'NAMEKO_CONFIG must be specified and should include at least "default" config with "AMQP_URL"')
            default_config = NAMEKO_CONFIG['default']
            # default_context_data = NAMEKO_CONFIG['default']['POOL'].get('CONTEXT_DATA', dict())
            # multi_context_data = getattr(settings, 'NAMEKO_MULTI_CONTEXT_DATA', dict())
            for name, _config in NAMEKO_CONFIG.items():
                # each pool will have different config with default config as default
                if name != 'default':
                    # overide default config with pool config by merging 2 dict
                    pool_config = dict(mergedicts(default_config, _config))
                else:
                    # default pool
                    pool_config = default_config.copy()
                # extract pool config from RpcCluster config
                pool_size = pool_config.pop('POOL_SIZE', None)
                pool_context_data = pool_config.pop('POOL_CONTEXT_DATA', None)
                pool_timeout = pool_config.pop('POOL_TIMEOUT', 0)
                # init pool
                _pool = ClusterRpcProxyPool(pool_config, pool_size=pool_size, context_data=pool_context_data,
                                            timeout=pool_timeout)
                # assign pool to corresponding name
                pool[name] = _pool
            if len(NAMEKO_MULTI_POOL) == 1:
                pool['default'].start()  # start immediately since there is only 1 pool
        else:
            # single pool with old style configuration
            if not hasattr(settings, 'NAMEKO_CONFIG') or not settings.NAMEKO_CONFIG:
                raise ImproperlyConfigured(
                    'NAMEKO_CONFIG must be specified and should include at least "AMQP_URL" key.')
            pool = ClusterRpcProxyPool(settings.NAMEKO_CONFIG)
            pool.start()  # start immediately
    create_pool_lock.release()
    if pool_name is not None:
        if not NAMEKO_MULTI_POOL or pool_name not in pool:
            raise ImproperlyConfigured(
                'NAMEKO_CONFIG must include this pool name "%s" config' % pool_name)
        else:
            _pool = pool[pool_name]
    else:
        if NAMEKO_MULTI_POOL:
            _pool = pool['default']
        else:
            _pool = pool

    if not _pool.is_started:
        _pool.start()
    return _pool


def destroy_pool():
    global pool
    pool = None
