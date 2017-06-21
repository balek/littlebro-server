import asyncio
import xml.etree.ElementTree as ET

import aiohttp


ns = { 'hik': 'http://www.hikvision.com/ver20/XMLSchema' }
tasks = []

async def start_camera(camera):
    username = camera.get('username', '')
    password = camera.get('password', '')
    auth = aiohttp.BasicAuth(username, password)
    async with aiohttp.ClientSession(auth=auth) as client:
        url = 'http://'
        url += camera['ip']
        if conf.get('hikvision_port'):
            url += ':%i' % conf.get('hikvision_port')
        url += '/ISAPI/Event/notification/alertStream'
        while True:
            try:
                async with client.get(url, timeout=10) as resp:
                    reader = aiohttp.MultipartReader.from_response(resp)
                    while True:
                        part = await reader.next()
                        part._length = None
                        if part is None:
                            break
                        root = ET.fromstring(await part.read())
                        eventType = root.find('hik:eventType', ns).text
                        if (eventType != 'VMD'):
                            continue
                        asyncio.ensure_future(handle_motion(camera))
            except asyncio.CancelledError: raise
            except TimeoutError as ex:
                print('TimeoutError')
            except Exception as ex:
                print(type(ex).__name__, ex)
                await asyncio.sleep(10)


def start(c, cams, cb):
    global conf, cameras, handle_motion
    conf = c
    cameras = cams
    handle_motion = cb

    for camera in cameras:
        tasks.append(asyncio.ensure_future(start_camera(camera)))


def stop():
    for t in tasks:
        t.cancel()
