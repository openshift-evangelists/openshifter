import os
import os.path
import json
import asyncio
import asyncio.subprocess
import logging

import aiohttp_jinja2
import jinja2

from aiohttp import web

loop = asyncio.get_event_loop()

class WebsocketListener:
    def __init__(self, websocket):
        self.websocket = websocket

    async def close(self):
        await self.websocket.close()

    def closed(self):
        return self.websocket.closed

    async def send(self, data):
        await self.websocket.send_str(data)

class Deployments:

    def __init__(self):
        self.listeners = {}
        self.processes = {}
        self.logger = logging.getLogger("Deployments")

    async def add_listener(self, name, listener):
        if name not in self.listeners:
            self.listeners[name] = []
        self.logger.info("Registering new listener")
        self.listeners[name].append(listener)
        if name in self.processes:
            await self.send(name, {'type': 'started'})

    def remove_listener(self, name, listener):
        if name in self.listeners:
            self.logger.info("Removing listener")
            self.listeners[name].remove(listener)

    async def create(self, name):
        if name not in self.processes:
            self.logger.info("Starting new deployment creation")
            await self.execute('create', name)

    async def destroy(self, name):
        if name not in self.processes:
            self.logger.info("Starting deployment destruction")
            await self.execute('destroy', name)

    async def execute(self, action, name):
        cmd = os.path.join(os.environ['ROOT_DIR'], 'entrypoint.sh')
        cmd += ' ' + action + ' ' + name
        process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self.processes[name] = process
        asyncio.ensure_future(self._read_stream(name, 'out', process.stdout))
        asyncio.ensure_future(self._read_stream(name, 'err', process.stderr))
        await self.send(name, {'type': 'started'})
        ec = await process.wait()
        await self.completed(name, ec)

    async def completed(self, name, ec):
        msg = {'type': 'completed', 'success': True}
        if ec > 0:
            msg['success'] = False
            msg['code'] = ec
        await self.send(name, msg)

        for listener in self.listeners[name]:
            await listener.close()

        self.processes.pop(name)

    async def send(self, name, data):
        if name in self.listeners:
            for listener in self.listeners[name]:
                if listener.closed():
                    self.listeners[name].remove(listener)
                else:
                    await listener.send(json.dumps(data))

    async def _read_stream(self, name, source, stream):
        while not stream.at_eof():
            data = await stream.readline()
            if len(data) > 0:
                await self.send(name, {'type': 'log', 'source': source, 'line': data.decode("utf-8")})

    async def deployments_handler(self, request):
        response = []
        for item in os.listdir("."):
            if os.path.isfile(item) and item.endswith(".yml"):
                name = item.replace(".yml", "")
                item = {
                    'name': name
                }
                if name in self.processes:
                    item['running'] = True
                response.append(item)
        return web.Response(text=json.dumps(response), content_type='application/json')

    async def create_deployment_handler(self, request):
        await self.create(request.match_info['name'])
        return web.Response(text="{}", content_type='application/json')

    async def destroy_deployment_handler(self, request):
        await self.destroy(request.match_info['name'])
        return web.Response(text="{}", content_type='application/json')


deployments = Deployments()

async def schema(request):
    with open(os.path.join(os.path.dirname(__file__), '..', 'schema.yml'), 'r') as file:
        return web.Response(text=file.read(), content_type='application/x-yaml')

async def stream(request):
    websocket = web.WebSocketResponse()
    await websocket.prepare(request)
    listener = WebsocketListener(websocket)
    await deployments.add_listener(request.match_info['name'], listener)

    try:
        async for msg in websocket:
            if msg.data == 'close':
                await websocket.close()
    except asyncio.CancelledError:
        pass
    finally:
        deployments.remove_listener(request.match_info['name'], listener)

    await websocket.close()

    return websocket

async def page(request):
    name = request.match_info['name']
    context = {'section': name, 'page': name}
    response = aiohttp_jinja2.render_template(name + '.html', request, context)
    return response

app = web.Application(loop=loop)

aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('web', 'templates'))

app.router.add_get('/', lambda request: web.HTTPFound('/page/dashboard'))
app.router.add_get('/page/{name}', page)

app.router.add_get('/schema.yml', schema)
app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'), name='static')

app.router.add_get('/api/deployments', deployments.deployments_handler)
app.router.add_post('/api/deployments/{name}', deployments.create_deployment_handler)
app.router.add_delete('/api/deployments/{name}', deployments.destroy_deployment_handler)

app.router.add_get('/stream/{name}', stream)

web.run_app(app, port=5000)