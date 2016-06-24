# -*- coding: utf-8 -*-
'''
Module to manage Janus WebRTC Gateway

:codeauthor:    Pablo Suarez Hernandez <psuarezhernandez@suse.de>
:depends: - ``janus`` https://janus.conf.meetecho.com/
'''

import salt.utils
from salt.exceptions import CommandExecutionError
import logging
import random
import json
import requests

__virtualname__ = 'janus'

log = logging.getLogger(__name__)


def __virtual__():
    if not salt.utils.which('janus'):
        return (False, 'The Janus WebRTC module cannot be loaded:'
                ' missing janus')
    return __virtualname__


class JanusSession(object):
    def __init__(self, *args, **kwargs):
        self._janus_proto = kwargs.get("janus_proto", "http")
        self._janus_uri = kwargs.get("janus_hostname", "localhost")
        self._janus_port = kwargs.get("janus_port", "8088")
        self._janus_base = kwargs.get("janus_base", "janus")

        self._janus_api_root = "{0}://{1}:{2}/{3}".format(self._janus_proto,
                                                          self._janus_uri,
                                                          self._janus_port,
                                                          self._janus_base)

    def _random_token(self):
        return "%008x" % random.getrandbits(64)

    def _create_instance(self):
        data = {"janus": "create", "transaction": self._random_token()}
        resp = requests.post(self._janus_api_root, json.dumps(data))
        return resp.json().get("data")

    def _attach_plugin(self, session_id, plugin_name):
        session_uri = self._janus_api_root + "/" + str(session_id)
        data = {"janus": "attach", "plugin": plugin_name, "transaction": self._random_token()}
        resp = requests.post(session_uri, json.dumps(data))
        return resp.json().get("data")
        
    def _message_request(self, session_id, plugin_id, message):
        plugin_uri = self._janus_api_root + "/" + str(session_id) + "/" + str(plugin_id)
        data = {"janus": "message", "body": message, "transaction": self._random_token()}
        log.warning("--> FINAL: %s" % plugin_uri)
        log.warning(data)
        resp = requests.post(plugin_uri, json.dumps(data))
        return resp.json()


janus = JanusSession()

def list_rooms(config=None):
    instance = janus._create_instance()
    plugin = janus._attach_plugin(instance['id'], "janus.plugin.videoroom")
    message = {"request": "list"}
    resp = janus._message_request(instance['id'], plugin['id'], message)
    return resp

def create_room(config=None):
    instance = janus._create_instance()
    plugin = janus._attach_plugin(instance['id'], "janus.plugin.videoroom")
    message = {"request": "create", "id": "11234", "description": "WOOOS AHORA SI", "bitrate": 64, "publishers": 10}
    resp = janus._message_request(instance['id'], plugin['id'], message)
    return resp
