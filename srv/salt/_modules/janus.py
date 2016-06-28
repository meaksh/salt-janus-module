# -*- coding: utf-8 -*-
'''
Module to manage Janus WebRTC Gateway

:codeauthor:    Pablo Suarez Hernandez <psuarezhernandez@suse.de>
:depends: - ``janus`` https://janus.conf.meetecho.com/
'''

from ConfigParser import ConfigParser
from salt.exceptions import CommandExecutionError
import salt.utils
import jinja2
import json
import logging
import os
import random
import requests


__virtualname__ = 'janus'

log = logging.getLogger(__name__)

JANUS_API_PROTO = "http"
JANUS_API_HOSTNAME = "localhost"
JANUS_API_PORT = "8088"
JANUS_API_BASE = "janus"
JANUS_CFG_BASE = "/etc/janus/"
JANUS_VIDEOROOM_CFG = os.path.join(JANUS_CFG_BASE, "janus.plugin.videoroom.cfg")
JANUS_AUDIOROOM_CFG = os.path.join(JANUS_CFG_BASE, "janus.plugin.audiobridge.cfg")


def __virtual__():
    if not salt.utils.which('janus'):
        return (False, 'The Janus WebRTC module cannot be loaded:'
                ' missing janus')
    return __virtualname__


class JanusSession(object):
    class JanusException(Exception):
        pass

    def __init__(self, *args, **kwargs):
        self.set_config()

    def set_config(self, opts=None):
        if not opts:
            opts = dict()

        self._janus_proto = opts.get("janus_proto", JANUS_API_PROTO)
        self._janus_uri = opts.get("janus_hostname", JANUS_API_HOSTNAME)
        self._janus_port = opts.get("janus_port", JANUS_API_PORT)
        self._janus_base = opts.get("janus_base", JANUS_API_BASE)

        self._janus_api_root = "{0}://{1}:{2}/{3}".format(self._janus_proto,
                                                          self._janus_uri,
                                                          self._janus_port,
                                                          self._janus_base)

        self._janus_videoroom_cfg = opts.get("janus_videoroom_cfg",
                                             JANUS_VIDEOROOM_CFG)
        self._janus_audioroom_cfg = opts.get("janus_audiobridge_cfg",
                                             JANUS_AUDIOROOM_CFG)

    def _random_token(self):
        return "%008x" % random.getrandbits(64)

    def _get_server_info(self, config):
        self.set_config(config)
        resp = requests.get(self._janus_api_root + "/info")
        return resp.json()

    def _create_instance(self, config):
        self.set_config(config)
        data = {"janus": "create", "transaction": self._random_token()}
        resp = requests.post(self._janus_api_root, json.dumps(data))
        return resp.json().get("data")

    def _attach_plugin(self, session_id, plugin_name):
        session_uri = self._janus_api_root + "/" + str(session_id)
        data = {"janus": "attach", "plugin": plugin_name,
                "transaction": self._random_token()}
        resp = requests.post(session_uri, json.dumps(data))
        if not resp.json().get("data"):
            raise self.JanusException(resp.json()['error']['reason'])
        return resp.json().get("data")
        
    def _message_request(self, session_id, plugin_id, message):
        plugin_uri = (self._janus_api_root + "/" + str(session_id) +
                     "/" + str(plugin_id))
        data = {"janus": "message", "body": message,
                "transaction": self._random_token()}
        resp = requests.post(plugin_uri, json.dumps(data))
        return resp.json()

    def _parse_rooms_list_response(self, response):
        item = response['plugindata']['data']['list']
        ret = {}
        for attr in item:
            name = attr.pop('room')
            ret[name] = attr
        return ret

    def _parse_config_file(self, filename):
        if __salt__['file.file_exists'](filename):
            config = ConfigParser()
            config.readfp(salt.utils.fopen(filename))
            ret = {}
            for sect in config.sections():
                ret[sect] = dict(config.items(sect))
            return ret
        else:
            raise self.JanusException("Config file '{0}' does not exist" % filename)

    def _update_config_file(self, config, filename):
        if __salt__['file.file_exists'](filename):
            pconfig = ConfigParser()
            for sect in config:
                section_dict = config.get(sect)
                pconfig.add_section(sect)
                [pconfig.set(sect, key, section_dict[key]) for key in section_dict]
            pconfig.write(salt.utils.fopen(filename, "wb"))
        else:
            raise self.JanusException("Config file '{0}' does not exist" % filename)

    def _save_rooms_in_file(self, rooms, filename):
        config = self._parse_config_file(filename)
        for room in rooms:
            if room is not str(room):
                item = rooms.pop(room)
                rooms[str(room)] = item
        config.update(rooms)
        self._update_config_file(config, filename)


janus = JanusSession()

def info(config=None):
    '''
    Show current Janus server information

    CLI example:

    .. code-block:: bash

        salt '*' janus.info
    '''
    try:
        return janus._get_server_info(config)
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while getting Janus server information: {0}'
            .format(exc)
        )


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
        return janus._parse_rooms_list_response(resp)
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while listing Janus videorooms: {0}'
            .format(exc)
        )


def list_audiorooms(config=None):
    '''
    List the current list of audiorooms availables in Janus service instance

    CLI example:

    .. code-block:: bash

        salt '*' janus.list_audiorooms
    '''
    try:
        instance = janus._create_instance(config)
        plugin = janus._attach_plugin(instance['id'], "janus.plugin.audiobridge")
        message = {"request": "list"}
        resp = janus._message_request(instance['id'], plugin['id'], message)
        return janus._parse_rooms_list_response(resp)
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while listing Janus audiorooms: {0}'
            .format(exc)
        )


def list_participants(room_id=None, config=None):
    '''
    List the participant of a video or audio room in a Janus service instance

    CLI example:

    .. code-block:: bash

        salt '*' janus.list_participants 12345
    '''
    try:
        instance = janus._create_instance(config)
        room_list = [room_id] if room_id else list_audiorooms().keys() + list_videorooms().keys()
        ret = {}
        for plugin_name in ["janus.plugin.videoroom", "janus.plugin.audiobridge"]:
            ret[plugin_name] = {}
            for room_id in room_list:
                plugin = janus._attach_plugin(instance['id'], plugin_name)
                message = {"request": "listparticipants", "room": room_id}
                resp = janus._message_request(instance['id'], plugin['id'], message)
                room_participants = resp['plugindata']['data'].get("participants", [])
                if room_participants:
                    ret[plugin_name].update({room_id: room_participants})
            ret.pop(plugin_name) if not ret[plugin_name] else None
        return ret
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while listing participants: {0}'
            .format(exc)
        )


def create_audioroom(name, publishers=20, sampling=16000, permanent=True, record=False, config=None):
    '''
    Create a new audioroom in Janus service instance

    CLI example:

    .. code-block:: bash

        salt '*' janus.create_audioroom "my tests videoroom"
        salt '*' janus.create_audioroom testroom publishers=20
    '''
    try:
        instance = janus._create_instance(config)
        plugin = janus._attach_plugin(instance['id'], "janus.plugin.audiobridge")
        message = {"request": "create", "description": name,
                   "sampling": sampling, "permanent": permanent}
        resp = janus._message_request(instance['id'], plugin['id'], message)
        return resp
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while creating Janus audioroom: {0}'
            .format(exc)
        )


def create_videoroom(name, publishers=20, bitrate=64, permanent=True, config=None):
    '''
    Create a new videoroom in Janus service instance
    CLI example:
    .. code-block:: bash
        salt '*' janus.create_videoroom "my tests videoroom"
        salt '*' janus.create_videoroom testroom bitrate=128 publishers=50
    '''
    try:
        instance = janus._create_instance(config)
        plugin = janus._attach_plugin(instance['id'], "janus.plugin.videoroom")
        message = {"request": "create", "description": name,
                   "bitrate": bitrate, "publishers": publishers,
                   "permanent": permanent}
        resp = janus._message_request(instance['id'], plugin['id'], message)
        return resp
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while creating Janus videoroom: {0}'
            .format(exc)
        )


def save_rooms_status(config=None):
    '''
    Save current created audiorooms and videorooms inside the Janus
    plugin config file. It persistent the room setting

    CLI example:

    .. code-block:: bash

        salt '*' janus.save_rooms_status
    '''
    try:
        janus._save_rooms_in_file(list_audiorooms(config), janus._janus_audioroom_cfg)
        janus._save_rooms_in_file(list_videorooms(config), janus._janus_videoroom_cfg)
        return True
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while saving Janus videorooms: {0}'
            .format(exc)
        )


def plugin_message(plugin, message, config=None):
    '''
    Send a custom message to plugin in a Janus service instance

    CLI example:

    .. code-block:: bash

        salt '*' janus.plugin_message "janus.plugin.videoroom" message='{"request": "list"}'
    '''
    try:
        instance = janus._create_instance(config)
        plugin_id = janus._attach_plugin(instance['id'], plugin)['id']
        resp = janus._message_request(instance['id'], plugin_id, message)
        return resp
    except Exception as exc:
        raise CommandExecutionError(
            'Error encountered while sending message to Janus plugin: {0}'
            .format(exc)
        )
