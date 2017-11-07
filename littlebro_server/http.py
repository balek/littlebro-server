#!/usr/bin/python3

import os
import json
import uuid
import time

from aiohttp import web
import aiohttp_session
import jwt

from .config import conf


def getCameraByName(name):
    return next(c for c in conf['cameras'] if c['id'] == name)


def check_user_access(request, camera):
    if not camera.get('groups'):
        return True
    for g in camera['groups']:
        if g in request['session']['user_groups']:
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
        raise web.HTTPForbidden()
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
        raise web.HTTPForbidden()
    return web.Response(headers={'X-Accel-Redirect': '/archive/{}/{}/{}'.format(params['date'], params['camera'], params['file'])})


async def authorize(request):
    return web.Response()


async def close_session(request):
    request['session'].invalidate()
    return web.Response()


async def cors_middleware(app, handler):
    async def middleware_handler(request):
        origin = request.headers.get('Origin')
        if request.method == 'OPTIONS':
            response = web.Response()
        else:
            response = await handler(request)
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '')
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    return middleware_handler


async def middleware(app, handler):
    async def middleware_handler(request):
        session = await aiohttp_session.get_session(request)
        token = request.headers.get('X-Access-Token')
        if token:
            try:
                data = jwt.decode(token, conf.secret)
                session['user_groups'] = data.get('groups', [])
                session['expires'] = time.time() + session.max_age
            except jwt.InvalidTokenError: pass

        if session.get('expires', 0) < time.time():
            raise web.HTTPForbidden()

        return await handler(request)

    return middleware_handler


class MemorySessionStorage(aiohttp_session.AbstractStorage):
    def __init__(self, *args,
            key_factory=lambda: uuid.uuid4().hex,
             **kwargs):
        self.sessions = {}
        self._key_factory = key_factory
        super().__init__(*args, **kwargs)

    async def load_session(self, request):
        key = self.load_cookie(request)
        data = self.sessions.get(key)
        if key and data:
            return aiohttp_session.Session(key, data=data, new=False, max_age=self.max_age)
        return aiohttp_session.Session(self._key_factory(), data=None, new=True, max_age=self.max_age)

    async def save_session(self, request, response, session):
        self.sessions[session.identity] = self._get_session_data(session)
        self.save_cookie(response, session.identity, max_age=session.max_age)


aiohttp_session.SESSION_KEY = 'session'
session_middleware = aiohttp_session.session_middleware(MemorySessionStorage(cookie_name='s', max_age=5*60))
app = web.Application(middlewares=[cors_middleware, session_middleware, middleware])
app.router.add_get('/authorize', authorize)
app.router.add_get('/close_session', close_session)
app.router.add_get('/cameras', cameras)
app.router.add_get('/{date:\d{4}-\d\d-\d\d}/archive.json', archive)
app.router.add_get('/{date:\d{4}-\d\d-\d\d}/{camera}/{file}', record)
app.router.add_get('/{file}', overview)


def main():
    web.run_app(app, path=conf['http_listen'], print=lambda x: None)
