# -*- coding: utf-8 -*-
import logging

from nameko.rpc import rpc
from nameko.events import event_handler
import os

logger = logging.getLogger(__name__)


class EchoService(object):
    name = 'echo'

    @rpc
    def echo(self, *attrs):
        return tuple(attrs)

    @event_handler("echo", "touch")
    def handle_event(self, payload):
        logger.debug("service echo received:%s", payload)
        if 'path' in payload and os.path.exists(payload['path']):
            os.unlink(payload['path'])
