import os
import os.path
import json
import asyncio
import asyncio.subprocess

import aiohttp_jinja2
import jinja2

from aiohttp import web

listeners = {}
processes = {}

async def read(name, source, stream):
    while not stream.at_eof():
        data = await stream.readline()
        if len(data) > 0:
            for listener in listeners[name]:
                if listener.closed:
                    listeners[name].remove(listener)
                else:
                    listener.send_str(json.dumps({'source': source, 'line': data.decode("utf-8")}))

async def manage_deployment(action, name):
    cmd = os.path.join(os.environ['ROOT_DIR'], 'entrypoint.sh')
    cmd += ' ' + action + ' ' + name
    process = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    processes[name] = process
    asyncio.ensure_future(read(name, 'out', process.stdout))
    asyncio.ensure_future(read(name, 'err', process.stderr))
    await process.wait()
    processes.pop(name)
    for listener in listeners[name]:
        await listener.close()

@aiohttp_jinja2.template('index.html')
async def handle(request):
    return {}

async def schema(request):
    with open(os.path.join(os.path.dirname(__file__), '..', 'schema.yml'), 'r') as file:
        return web.Response(text=file.read(), content_type='application/x-yaml')

async def deployments(request):
    response = []
    for item in os.listdir("."):
        if os.path.isfile(item) and item.endswith(".yml"):
            response.append(item.replace(".yml", ""))
    return web.Response(text=json.dumps(response), content_type='application/json')

async def new_deployment(request):
    name = request.match_info['name']
    if name not in processes:
        await manage_deployment('create', name)
    return web.Response(text="{}", content_type='application/json')

async def delete_deployment(request):
    name = request.match_info['name']
    if name not in processes:
        await manage_deployment('destroy', name)
    return web.Response(text="{}", content_type='application/json')

async def stream(request):
    name = request.match_info['name']
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    if name not in listeners:
        listeners[name] = []
    listeners[name].append(ws)
    async for msg in ws:
        if msg.data == 'close':
            await ws.close()
    listeners[name].remove(ws)
    return ws

app = web.Application()

aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('web', 'templates'))

app.router.add_get('/', handle)
app.router.add_get('/schema.yml', schema)
app.router.add_get('/deployments', deployments)
app.router.add_post('/deployments/{name}', new_deployment)
app.router.add_delete('/deployments/{name}', delete_deployment)
app.router.add_get('/stream/{name}', stream)
app.router.add_static('/static/', path=os.path.join(os.path.dirname(__file__), 'static'), name='static')

web.run_app(app, port=5000)