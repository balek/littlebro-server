import json
import tempfile
import os


conf = json.load(open('/etc/littlebro.conf'))
conf.setdefault('ffmpeg_path', '/usr/bin/ffmpeg')
conf.setdefault('archive_path', '/srv/littlebro')
conf.setdefault('hls_dir', os.path.join(tempfile.gettempdir(), 'littlebro'))
conf.setdefault('motion_methods', {'type': 'tcp'})
conf.setdefault('host_prefix', 'cam-')
