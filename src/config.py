import json


conf = json.load(open('/etc/littlebro.conf'))
conf.setdefault('ffmpeg_path', '/usr/bin/ffmpeg')
conf.setdefault('archive_path', '/srv/littlebro')
conf.setdefault('hls_path', '/tmp/littlebro')
conf.setdefault('motion_detection', 'ip')
conf.setdefault('motion_port', 6321)
conf.setdefault('smtp_port', 1025)
conf.setdefault('domain_prefix', 'cam-')