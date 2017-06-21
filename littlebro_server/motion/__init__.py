#!/usr/bin/python3

import os
import socket
import asyncio
from datetime import datetime, timedelta
import importlib
import shutil

from ..config import conf


exit_flag = False
loop = asyncio.get_event_loop()


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
    command = conf['ffmpeg_path'] + ' -y -loglevel warning -i ' + camera['hls_path'] + ' -ss 4 -bsf:a aac_adtstoasc -c copy -movflags faststart ' + output_path
    process = await asyncio.create_subprocess_exec(*command.split(), stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    limit_recording_timer = asyncio.ensure_future(asyncio.sleep(60*30))
    wait_process = asyncio.ensure_future(process.wait())
    while True:
        camera['stop_recording_timer'] = asyncio.ensure_future(asyncio.sleep(30))
        stop_conditions = [camera['stop_recording_timer'], limit_recording_timer, wait_process]
        done, pending = await asyncio.wait(stop_conditions, return_when=asyncio.FIRST_COMPLETED)
        if camera['stop_recording_timer'].cancelled() and not exit_flag:
            continue
        for t in pending:
            t.cancel()
        # await asyncio.wait(pending)
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
    disk_quota = conf.get('disk_quota', 0.95)
    if stat.f_bavail / stat.f_blocks > 1 - disk_quota:
        return

    try:
        dirs = next(os.walk(conf['archive_path']))[1]
        dirs.sort()
        first_dir_name = dirs[0]
        shutil.rmtree(os.path.join(conf['archive_path'], first_dir_name))
    except IndexError: pass

def check_free_space_in_executor():
    loop.run_in_executor(None, check_free_space)


cameras = conf['cameras']
for camera in cameras:
    camera['stop_recording_timer'] = None

    if camera.get('streams', {}).get('main'):
        stream = 'main'
    else:
        stream = 'extra'
    camera['hls_path'] = os.path.join(conf['hls_dir'], camera['id'] + '_%s.m3u8' % stream)

    if conf.get('host_prefix') and not camera.get('host'):
        camera['host'] = conf['host_prefix'] + camera['id']

    if not camera.get('ip') and camera.get('host'):
        camera['ip'] = socket.gethostbyname(camera['host'])


def main():
    for method_conf in conf.get('motion_methods', []):
        module = importlib.import_module('.methods.' + method_conf['type'], __package__)
        module.start(method_conf, cameras, handle_motion)

    check_free_space_in_executor()

    print('Motion monitoring started')
    try:
        loop.run_forever()
    except KeyboardInterrupt: pass

    global exit_flag
    exit_flag = True

    for method_conf in conf.get('motion_methods', []):
        module = importlib.import_module('.methods.' + method_conf['type'], __package__)
        module.stop()

    for camera in cameras:
        if camera['stop_recording_timer']:
            camera['stop_recording_timer'].cancel()

    loop.run_until_complete(asyncio.wait(asyncio.Task.all_tasks()))
    loop.close()
