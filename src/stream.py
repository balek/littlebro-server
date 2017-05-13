#!/usr/bin/python3

import os
import sys
import socket

from .config import conf


def main():
    if len(sys.argv) < 2:
        print('Usage: %s <camera_id>_<stream>' % sys.argv[0], file=sys.stderr)
        exit(1)

    (camera_id, stream) = sys.argv[1].rsplit('_', 1)
    camera = list(filter(lambda c: c['id'] == camera_id, conf['cameras']))[0]
    args = conf['ffmpeg_path'] + ' -loglevel fatal '

    if camera.get('capture'):
        capture = camera['capture']
        args += '-f v4l2 '
        args += '-input_format %s ' % capture['input_format']
        args += '-r %i ' % capture.get('framerate', 10)
        if capture.get('standard'):
            args += '-standard %s ' % capture['standard']
        args += '-s %s ' % capture['size']
        args += '-i %s ' % capture['device']
        if capture['input_format'] == 'h264':
            args += '-c:v copy '
        else:
            args += '-c:v libx264 '
    else:
        if camera.get('use_wallclock_as_timestamps'):
            args += '-use_wallclock_as_timestamps 1 '
        stream_url = camera['streams'][stream]
        if stream_url.startswith('/'):
            ip = camera.get('ip')
            if not ip:
                ip = socket.gethostbyname('cam-' + camera['id'])
            stream_url = 'rtsp://' + camera['credentials']['username'] + ':' + camera['credentials']['password'] + '@' + ip + stream_url
        args += '-i %s -c:v copy -c:a aac -b:a 24k ' % stream_url
    hls_path = os.path.join(conf['hls_path'], sys.argv[1] + '.m3u8')
    args += '-hls_time 2 -hls_flags delete_segments ' + hls_path

    # TODO: rm -f /tmp/littlebro/%i*

    os.execv(conf['ffmpeg_path'], args.split())
