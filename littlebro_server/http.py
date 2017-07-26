#!/usr/bin/python3

import os
import json

import aiohttp
from aiohttp import web
from aiohttp.web import HTTPForbidden

from .config import conf


def getCameraByName(name):
    return next(c for c in conf['cameras'] if c['id'] == name)


def check_user_access(request, camera):
    if not camera.get('groups'):
        return True
    for g in camera['groups']:
        if g in request['user_groups']:
            return True

async def cameras(request):
    result = []
    for c in conf['cameras']:
        if check_user_access(request, c):
            result.append({'id': c['id'], 'name': c['name']})
    return web.json_response(result)


async def overview(request):
    file = request.match_info['file']
    stream = file.split('.', 1)[0]
    cameraName = stream.split('_', 1)[0]
    camera = getCameraByName(cameraName)
    if not check_user_access(request, camera):
        raise HTTPForbidden()
    return web.Response(headers={'X-Accel-Redirect': '/overview/' + file})


async def archive(request):
    d = request.match_info['date']
    f = open(os.path.join(conf['archive_path'], d, 'archive.json'))
    result = json.load(f)
    f.close()
    for name in list(result):
        camera = getCameraByName(name)
        if not check_user_access(request, camera):
            del result[name]
    return web.json_response(result)


async def record(request):
    params = request.match_info
    camera = getCameraByName(params['camera'])
    if not check_user_access(request, camera):
        raise HTTPForbidden()
    return web.Response(headers={'X-Accel-Redirect': '/archive/{}/{}/{}'.format(params['date'], params['camera'], params['file'])})


async def middleware(app, handler):
    async def middleware_handler(request):
        connector = aiohttp.TCPConnector(ttl_dns_cache=None)
        async with aiohttp.ClientSession(connector=connector) as client:
            for url in conf['viewers']:
                if request.headers['Referer'].startswith(url):
                    break
            else:
                raise HTTPForbidden()

            url += '/check-access?url=' + str(request.url)

            async with client.get(url, timeout=30) as r:
                if r.status != 200:
                    raise HTTPForbidden()
                try:
                    request['user_groups'] = await r.json()
                except:
                    request['user_groups'] = []

        response = await handler(request)
        if request.headers.get('Origin'):
            response.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
        return response
    return middleware_handler


app = web.Application(middlewares=[middleware])
app.router.add_get('/{sid}/archive/cameras.json', cameras)
app.router.add_get('/{sid}/overview/{file}', overview)
app.router.add_get('/{sid}/archive/{date:\d{4}-\d\d-\d\d}/archive.json', archive)
app.router.add_get('/{sid}/archive/{date:\d{4}-\d\d-\d\d}/{camera}/{file}', record)


def main():
    web.run_app(app, path=conf['http_listen'], print=lambda x: None)
