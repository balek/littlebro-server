import asyncio


async def handle_motion_server_connection(reader, writer):
    data = await reader.read()
    writer.close()
    try:
        if conf.get('comparison') == 'id':
            message = data.decode()
            camera = next(c for c in cameras if c['id'] == message)
        else:
            addr = writer.get_extra_info('peername')
            camera = next(c for c in cameras if c['ip'] == addr[0])
    except StopIteration:
        return
    await handle_motion(camera)


def start(c, cams, cb):
    global conf, cameras, handle_motion, server
    conf = c
    cameras = cams
    handle_motion = cb
    server = asyncio.start_server(handle_motion_server_connection, '0.0.0.0', conf['port'])

def stop():
    server.close()