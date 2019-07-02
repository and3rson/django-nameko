# -*- coding: utf-8 -*-
import logging

from nameko.rpc import rpc

logger = logging.getLogger(__name__)


class EchoService(object):

    name = 'echo'

    @rpc
    def echo(self, *attrs):
        return tuple(attrs)
