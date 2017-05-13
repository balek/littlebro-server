import asyncio
import xml.etree.ElementTree as ET

import aiohttp

from littlebro_server.config import conf


ns = { 'hik': 'http://www.hikvision.com/ver20/XMLSchema' }

async def main():
    auth = aiohttp.BasicAuth(conf['motion_username'], conf['motion_password'])
    async with aiohttp.ClientSession(auth=auth) as client:
        async with client.get(conf['motion_url']) as resp:
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
                print(ET.tostring(root, encoding='unicode'), '\n\n')

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
