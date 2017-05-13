import asyncio

from littlebro_server.config import conf
from .. import cameras, handle_motion


async def handle_motion_server_connection(reader, writer):
    data = await reader.read()
    writer.close()
    try:
        if conf['motion_detection'] == 'id':
            message = data.decode()
            camera = next(c for c in cameras if c['id'] == message)
        else:
            addr = writer.get_extra_info('peername')
            camera = next(c for c in cameras if c['ip'] == addr[0])
    except StopIteration:
        return
    await handle_motion(camera)


def start():
    return asyncio.start_server(handle_motion_server_connection, '0.0.0.0', conf['motion_port'])
