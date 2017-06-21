#!/usr/bin/python3

from datetime import datetime
import os
import re
import json
from subprocess import check_output, CalledProcessError

import pyinotify

from .config import conf


RECORD_PATH_FORMAT = re.compile('(\d{4})-(\d\d)-(\d\d)/([^/]+)/(\d\d)-(\d\d)-(\d\d)\.mp4$')


def dump_archive(archive, date=None):
    cameras_file = os.path.join(conf['archive_path'], 'cameras.json')
    f = open(cameras_file, 'w')
    for c in conf['cameras']:
        c['archive'] = []
        for d in archive:
            if archive[d].get(c['id']):
                c['archive'].append(d)
    json.dump(conf['cameras'], f)
    f.close()
    for d in archive:
        if date and d != date:
            continue
        f = open(os.path.join(conf['archive_path'], d, 'archive.json'), 'w')
        json.dump(archive[d], f)
        f.close()


def parse_path(path):
    relpath = os.path.relpath(path, conf['archive_path'])
    match = RECORD_PATH_FORMAT.match(relpath)
    if not match:
        raise Exception
    groups = list(match.groups())
    camera = groups.pop(3)
    dt = datetime(*map(int, groups))
    date = dt.strftime('%Y-%m-%d')
    time = dt.strftime('%H:%M:%S')
    return date, camera, time


def walk_archive(archive, date, camera):
    date_archive = archive.setdefault(date, {})
    camera_archive = date_archive.setdefault(camera, {})
    return date_archive, camera_archive


def add_record(path, archive, old_archive={}):
    try:
        date, camera, time = parse_path(path)
    except Exception as e:
        return False

    date_archive, camera_archive = walk_archive(archive, date, camera)

    if time in old_archive.get(date, {}).get(camera, {}):
        camera_archive[time] = old_archive[date][camera][time]
        return False

    try:
        ffprobe_output = check_output(['ffprobe', '-loglevel', 'quiet', '-show_entries', 'stream=duration', '-select_streams', 'v', path])
        duration = ffprobe_output.decode().split('\n')[1].split('=')[1].split('.')[0]
    except (CalledProcessError, IndexError) as e:
        print(e)
        return False
    camera_archive[time] = int(duration)
    return date


def rm_record(path, archive):
    try:
        date, camera, time = parse_path(path)
    except Exception: return

    date_archive, camera_archive = walk_archive(archive, date, camera)

    camera_archive.pop(time, None)
    if not camera_archive:
        del date_archive[camera]
    if not date_archive:
        del archive[date]
    return date


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CLOSE_WRITE(self, event):
        date = add_record(event.pathname, archive)
        if date:
            dump_archive(archive, date)

    def process_IN_DELETE(self, event):
        date = rm_record(event.pathname, archive)
        dump_archive(archive, date)


old_archive = {}
for date in os.listdir(conf['archive_path']):
    try:
        f = open(os.path.join(conf['archive_path'], date, 'archive.json'))
        old_archive[date] = json.load(f)
        f.close()
    except: pass

archive = {}


def main():
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_CLOSE_WRITE #| pyinotify.IN_DELETE
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(conf['archive_path'], mask, rec=True, auto_add=True)

    for path, dirs, files in os.walk(conf['archive_path']):
        for f in files:
            add_record(os.path.join(path, f), archive, old_archive)

    dump_archive(archive)

    notifier.loop()
