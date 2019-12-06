# -*- coding: utf-8 -*-
import logging

from nameko.rpc import rpc
from nameko.events import event_handler
import os
import shutil

logger = logging.getLogger(__name__)


class EchoService(object):
    name = 'echo'

    @rpc
    def echo(self, *attrs):
        return tuple(attrs)

    @event_handler("echo", "touch")
    def handle_event_touch(self, payload):
        logger.debug("service echo received:%s", payload)
        if 'path' in payload and os.path.exists(payload['path']):
            os.unlink(payload['path'])

    @event_handler("echo", "clone")
    def handle_event_clone1(self, payload):
        logger.debug("service echo received:%s", payload)
        if 'path' in payload and os.path.exists(payload['path']):
            shutil.copy(payload['path'], payload['path'] + '.copy')

    @event_handler("echo", "clone")
    def handle_event_clone2(self, payload):
        logger.debug("service echo received:%s", payload)
        if 'path' in payload and os.path.exists(payload['path']):
            os.link(payload['path'], payload['path'] + '.link')
