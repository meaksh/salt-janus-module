# salt-janus-module
A Janus WebRTC execution module for Salt.

Available functions:

- janus.info
- janus.list_videorooms
- janus.list_audiorooms
- janus.list_participants
- janus.create_videoroom
- janus.create_audioroom
- janus.plugin_message
- janus.save_rooms_status

## Custom Salt module installation:
We need to install `salt-janus-module` as a custom Salt module. By default, custom modules for Salt are located in `/srv/salt/_modules/`.

#### 1. Copy the custom module to Salt `base_root`:
Do it in Salt Master. Or in Minion if you have a masterless configuration
```
# git clone https://github.com/meaksh/salt-janus-module
# cd salt-janus-module
# cp -r srv/salt/_modules/ /srv/salt/
```

#### 2. Refresh Salt modules in the Minions:
Salt Master:
```
# salt '*' saltutil.sync_all
```
or if you are using a masterless configuration (run it on the Minion):
```
# salt-call --local saltutil.sync_all
```

## Examples in Masterless configuration (run it on the Minion):
```
# salt-call --local janus.list_videorooms
local:
    ----------
    1234:
        ----------
        audiocodec:
            opus
        bitrate:
            64000
        description:
            Canal SUSE
        fir_freq:
            10
        max_publishers:
            3
        num_participants:
            1
        record:
            false
        videocodec:
            vp8
    3302790623:
        ----------
        audiocodec:
            opus
        bitrate:
            128000
        description:
            Mi nuevo canal HQ
        fir_freq:
            0
        max_publishers:
            3
        num_participants:
            2
        record:
            false
        videocodec:
            vp8
```
```
# salt-call --local janus.list_participants
local:
    ----------
    janus.plugin.videoroom:
        ----------
        1234:
            |_
              ----------
              display:
                  Pablo
              id:
                  2174113600
              publisher:
                  false
        3302790623:
            |_
              ----------
              display:
                  TestUser
              id:
                  101229014
              publisher:
                  true
            |_
              ----------
              display:
                  TestUser2
              id:
                  1550119541
              publisher:
                  false
```
```
# salt-call --local janus.create_videoroom "My test channel" publishers=100
local:
    ----------
    janus:
        success
    plugindata:
        ----------
        data:
            ----------
            room:
                1725484614
            videoroom:
                created
        plugin:
            janus.plugin.videoroom
    sender:
        466218262
    session_id:
        2947397632
    transaction:
        fe49568851523b71
```
```
# salt-call --local janus.plugin_message "janus.plugin.audiobridge" message='{"request": "list"}'
local:
    ----------
    janus:
        success
    plugindata:
        ----------
        data:
            ----------
            audiobridge:
                success
            list:
                |_
                  ----------
                  description:
                      JOSEEETE
                  num_participants:
                      0
                  record:
                      false
                  room:
                      2805501895
                  sampling_rate:
                      16000
        plugin:
            janus.plugin.audiobridge
    sender:
        2575730974
    session_id:
        3196002190
    transaction:
        a681d2202fd6d1a1
```
