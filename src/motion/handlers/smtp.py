import asyncio
import re
from functools import partial

from aiosmtpd.smtp import SMTP

from littlebro_server.config import conf
from .. import cameras, handle_motion


camera_regex = re.compile('^Alarm input channel No.: ([-\w]+)', re.MULTILINE)


class MessageHandler:
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        id = camera_regex.search(data.decode()).group(1)
        try:
            camera = next(c for c in cameras if c['id'] == id)
        except StopIteration:
            return
        asyncio.ensure_future(handle_motion(camera))


class AuthSmtp(SMTP):
    async def smtp_AUTH(self, arg):
        await self.push('334 asdf')
        await self._reader.readline()
        await self.push('334 asdf')
        await self._reader.readline()
        await self.push('235 ok')


def start():
    loop = asyncio.get_event_loop()
    factory = partial(AuthSmtp, MessageHandler())
    return loop.create_server(factory, '0.0.0.0', conf['smtp_port'])
