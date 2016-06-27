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
        self.set_config()

    def set_config(self, opts=None):
        if not opts:
            opts = dict()

        self._janus_proto = opts.get("janus_proto", "http")
        self._janus_uri = opts.get("janus_hostname", "localhost")
        self._janus_port = opts.get("janus_port", "8088")
        self._janus_base = opts.get("janus_base", "janus")

        self._janus_api_root = "{0}://{1}:{2}/{3}".format(self._janus_proto,
                                                          self._janus_uri,
                                                          self._janus_port,
                                                          self._janus_base)

    def _random_token(self):
        return "%008x" % random.getrandbits(64)

    def _create_instance(self, config):
        self.set_config(config)
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
        resp = requests.post(plugin_uri, json.dumps(data))
        return resp.json()


janus = JanusSession()

def list_videorooms(config=None):
    '''
    List the current list of videorooms availables in Janus service instance

    CLI example:

    .. code-block:: bash

        salt '*' janus.list_videorooms
    '''
    try:
        instance = janus._create_instance(config)
        plugin = janus._attach_plugin(instance['id'], "janus.plugin.videoroom")
        message = {"request": "list"}
        resp = janus._message_request(instance['id'], plugin['id'], message)
        return resp
    except requests.exceptions.ConnectionError as exc:
        raise CommandExecutionError(
            'Error encountered while listing Janus videorooms: {0}'
            .format(exc)
        )


def create_videoroom(name, publishers=20, bitrate=64, id=None, config=None):
    '''
    Create a new videoroom in Janus service instance

    CLI example:

    .. code-block:: bash

        salt '*' janus.create_videoroom "my tests videoroom"
        salt '*' janus.create_videoroom testvideoroom bitrate=128 publishers=50
    '''
    try:
        instance = janus._create_instance(config)
        plugin = janus._attach_plugin(instance['id'], "janus.plugin.videoroom")
        message = {"request": "create", "id": id, "description": name, "bitrate": bitrate, "publishers": publishers}
        resp = janus._message_request(instance['id'], plugin['id'], message)
        return resp
    except requests.exceptions.ConnectionError as exc:
        raise CommandExecutionError(
            'Error encountered while listing Janus videorooms: {0}'
            .format(exc)
        )
