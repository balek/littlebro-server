#!/usr/bin/python3

import os
import socket
import asyncio
from datetime import datetime, timedelta
import shutil

from littlebro_server.config import conf


async def handle_motion(camera):
    if camera['stop_recording_timer']:
        camera['stop_recording_timer'].cancel()
        return

    now = datetime.now() - timedelta(seconds=3)
    date_dir_name = now.strftime('%Y-%m-%d')
    output_dir_path = os.path.join(conf['archive_path'], date_dir_name, camera['id'])
    try:
     os.makedirs(output_dir_path)
    except FileExistsError: pass
    output_path = os.path.join(output_dir_path, now.strftime('%H-%M-%S.mp4'))
    command = conf['ffmpeg_path'] + ' -y -loglevel fatal -i ' + camera['hls_path'] + ' -ss 4 -bsf:a aac_adtstoasc -c copy -movflags faststart ' + output_path
    process = await asyncio.create_subprocess_exec(*command.split(), stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    limit_recording_timer = asyncio.ensure_future(asyncio.sleep(60*30))
    while True:
        camera['stop_recording_timer'] = asyncio.ensure_future(asyncio.sleep(30))
        stop_conditions = [camera['stop_recording_timer'], limit_recording_timer, process.wait()]
        done, pending = await asyncio.wait(stop_conditions, return_when=asyncio.FIRST_COMPLETED)
        if camera['stop_recording_timer'].cancelled():
            continue
        break
    camera['stop_recording_timer'] = None
    try:
        output, errput = await asyncio.wait_for(process.communicate('q'.encode()), 120)
    except asyncio.TimeoutError:
        print('Could not finish ffmpeg with "q"')
        process.terminate()
        return
    if process.returncode:
        print('ffmpeg Stopped with error', process.returncode)
    # else:
    #     print('OK')


def check_free_space():
    loop.call_later(3600, check_free_space_in_executor)

    stat = os.statvfs(conf['archive_path'])
    if stat.f_bavail / stat.f_blocks > 0.2:
        return

    try:
        dirs = next(os.walk(conf['archive_path']))[1]
        dirs.sort()
        first_dir_name = dirs[0]
        shutil.rmtree(os.path.join(conf['archive_path'], first_dir_name))
    except IndexError: pass

def check_free_space_in_executor():
    loop.run_in_executor(None, check_free_space)

loop = asyncio.get_event_loop()

cameras = conf['cameras']
for camera in cameras:
    camera['stop_recording_timer'] = None
    if camera.get('streams', {}).get('main'):
        stream = 'main'
    else:
        stream = 'extra'
    camera['hls_path'] = os.path.join(conf['hls_path'], camera['id'] + '_%s.m3u8' % stream)



def main():
    if conf['motion_detection'] in ['ip', 'id']:
        from .handlers.tcp import start
        server_start = start()

    if conf['motion_detection'] == 'ip':
        for camera in cameras:
            if not camera.get('ip'):
                camera['ip'] = socket.gethostbyname(conf['domain_prefix'] + camera['id'])

    elif conf['motion_detection'] == 'smtp':
        from .handlers.smtp import start
        server_start = start()

    server = loop.run_until_complete(server_start)
    check_free_space_in_executor()

    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
