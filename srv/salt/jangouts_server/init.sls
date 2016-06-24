/etc/janus/janus.plugin.videoroom.cfg:
  file.managed:
    - source: salt://jangouts_server/janus.plugin.videoroom.cfg.template
    - user: root
    - group: root
    - mode: 644
    - template: jinja

restart_janus_service:
  module.run:
    - name: service.reload
    - m_name: janus
