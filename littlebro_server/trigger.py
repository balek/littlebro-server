#!/usr/bin/python3

import sys
import socket

from .config import conf


def main():
    if len(sys.argv) < 2:
        print('Usage: %s <camera_id>' % sys.argv[0], file=sys.stderr)
        exit(1)


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for method in conf['motion_methods']:
        if method['type'] == 'tcp':
            port = method['port']
            break
    else:
        raise Exception('motion method "tcp" not found')
    s.connect(('127.0.0.1', port))
    s.send(sys.argv[1].encode())
    s.close()