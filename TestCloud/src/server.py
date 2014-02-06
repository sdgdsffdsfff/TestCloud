'''
Created on 2014-1-9

@author: Administrator
'''

from autobahn.twisted.websocket import WebSocketServerProtocol, \
                                       WebSocketServerFactory
import sys
import json
import datetime
import os
import zipfile
import re

class Device:

    def __init__(self, protocol, params):
        self.protocol  = protocol
        self.ip        = params['ip']
        self.deviceId  = params['deviceId'][0]
        self.platform  = params['platform'][0]
        self.version   = params['version'][0]
        self.model     = params['model'][0]
        self.baseband  = params['baseband'][0]
        self.build     = params['build'][0]
        self.buildDate = params['buildDate'][0]
        self.online    = 1

    def getDevice(self):
        return {
                'ip': self.ip,
                'deviceId': self.deviceId,
                'platform': self.platform,
                'version': self.version,
                'model': self.model,
                'baseband': self.baseband,
                'build': self.build,
                'buildDate': self.buildDate,
                'online': self.online
        }

class Client:

    def __init__(self, protocol, params):
        self.protocol = protocol
        self.ip       = params['ip']
        self.deviceId = params['deviceId'][0]

    def getDevice(self):
        return {
                'ip': self.ip,
                'deviceId': self.deviceId
        }

class Message:

    def __init__(self, msg=None):
        self.json = dict()
        if type(msg) == int:
            self.json['type'] = msg

    def put(self, key, value):
        self.json[key] = value

    def get(self, key):
        self.json.get(key)

    def __str__(self):
        return json.dumps(self.json)

clients = dict()

def broadcastDevices():
    online = []
    msg = Message(6001)
    for key in devices:
        online.append(devices[key].getDevice())
    msg.put('devices', online)
    for key in clients:
        clients[key].protocol.sendMessage(str(msg).encode('utf-8'))

class TestClientProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print('Client connecting: {0}'.format(request.peer))
        request.params['ip'] = request.peer.split(':')[0]
        self.deviceId = request.params['deviceId'][0]
        clients[self.deviceId] = Client(self, request.params)

    def onOpen(self):
        print('WebSocket connection open.')

    def onMessage(self, payload, isBinary):
        text = payload.decode('utf-8')
        d = dict(json.loads(text))
        if d['type'] == 6001:
            broadcastDevices()
        elif d['type'] == 6002:
            sendTask(devices[d['deviceId']], bool(d['update']), d['tests'])

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))
        if clients.has_key(self.deviceId):
            clients.pop(self.deviceId)

devices = dict()

def getUpdateUrl(device):
    path = '\\\\10.204.75.220\\htdocs$\\{0}'
    if not os.path.exists(path.format(device.model)):
        return None
    update_zip = max(os.listdir(path.format(device.model)))
    if update_zip:
        update_path = os.path.join(path.format(device.model), update_zip)
        z = zipfile.ZipFile(update_path, 'r')
        b = z.read('system/build.prop')
        s = b.decode('utf-8')
        l = s.split('\n')
        for ll in l:
            if ll.startswith('ro.build.date='):
                v = ll[14:]
                p = re.compile('\d+')
                vv = p.findall(v)
                date = '{0} {1}'.format('-'.join(vv[:3]), ':'.join(vv[3:]))
                if date > device.buildDate:
                    return ('http://10.204.75.220:8181/{0}/{1}'.format(device.model, update_zip), date)
    return None

def sendTask(device, update, tests):
    queue = []
    msg = Message(6003)
    updateUrl = getUpdateUrl(device)
    if updateUrl and update:
        queue.append({'type': 7001, 'updateUrl': updateUrl[0], 'buildDate': updateUrl[1]})
    #date = datetime.datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    paths = (device.deviceId, device.build, device.buildDate.replace('-', '').replace(':', '').replace(' ', ''), timestamp)
    items= []
    for test in tests:
        d = dict(json.loads(test))
        i = d['id']
        t = d['type']
        params = d['params']
        if t == 7001:
            items.append({
                'id': i,
                'name': 'monkey',
                'cmd': 'monkey -s 25 --ignore-timeouts --ignore-crashes -v {0} --pct-nav 0 --pct-trackball 0'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey.txt'.format(*paths)
            })
        elif t == 7002:
            items.append({
                'id': i,
                'name': 'monkey-com.android.gallery3d',
                'cmd': 'sh start_monkey_exit.sh com.android.gallery3d com.android.camera.CameraLauncher {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey-com.android.gallery3d.txt'.format(*paths)
            })
        elif t == 7003:
            items.append({
                'id': i,
                'name': 'monkey-com.android.contacts.people',
                'cmd': 'sh start_monkey_exit.sh com.android.contacts com.android.contacts.activities.PeopleActivity {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey-com.android.contacts.people.txt'.format(*paths)
            })
        elif t == 7004:
            items.append({
                'id': i,
                'name': 'monkey-com.android.mms',
                'cmd': 'sh start_monkey_exit.sh com.android.mms com.android.mms.ui.FunctionSwitchActivity {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey-com.android.mms.txt'.format(*paths)
            })
        elif t == 7005:
            items.append({
                'id': i,
                'name': 'monkey-com.android.contacts.dialer',
                'cmd': 'sh start_monkey_exit.sh com.android.contacts com.android.contacts.DialerActivity {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey-com.android.contacts.dialer.txt'.format(*paths)
            })
        elif t == 7006:
            items.append({
                'id': i,
                'name': 'monkey-com.android.settings',
                'cmd': 'sh start_monkey_exit.sh com.android.settings com.android.settings.Settings {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey-com.android.settings.txt'.format(*paths)
            })
        elif t == 7007:
            items.append({
                'id': i,
                'name': 'monkey-com.android.strengthenmusic',
                'cmd': 'sh start_monkey_exit.sh com.android.strengthenmusic com.android.strengthenmusic.ui.MusicWelcome {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-monkey-com.android.strengthenmusic.txt'.format(*paths)
            })
        elif t == 7008:
            items.append({
                'id': i,
                'name': 'stress',
                'cmd': 'am start -n com.ztemt.test.auto/.AutoTestActivity --es mode auto {0}'.format(params),
                'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-stress.txt'.format(*paths)
            })
    queue.append({'type': 7002, 'tests': str(items)})
    msg.put('queue', queue)
    print(str(msg))
    device.protocol.sendMessage(str(msg).encode('utf-8'))

class TestPlatformProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print('Device connecting: {0}'.format(request.peer))
        request.params['ip'] = request.peer.split(':')[0]
        self.deviceId = request.params['deviceId'][0]
        self.device = Device(self, request.params)
        devices[self.deviceId] = self.device

    def onOpen(self):
        print('WebSocket connection open.')
        broadcastDevices()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print('Binary message received: {0} bytes'.format(len(payload)))
        else:
            text = payload.decode('utf-8')
            d = dict(json.loads(text))
            if d['type'] == 6003:
                tests = [
                    '{"id": 1, "type": 7001, "params": "200000"}',
                    '{"id": 2, "type": 7002, "params": "10000 10"}',
                    '{"id": 3, "type": 7003, "params": "10000 10"}',
                    '{"id": 4, "type": 7004, "params": "10000 10"}',
                    '{"id": 5, "type": 7005, "params": "10000 10"}',
                    '{"id": 6, "type": 7006, "params": "10000 10"}',
                    '{"id": 7, "type": 7007, "params": "10000 10"}',
                    '{"id": 8, "type": 7008, "params": "--ei times 10"}'
                ]
                sendTask(devices[self.deviceId], True, tests)

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))
        if devices.has_key(self.deviceId):
            devices[self.deviceId].online = 0
        broadcastDevices()

if __name__ == '__main__':
    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)

    platform = WebSocketServerFactory('ws://127.0.0.1:9000', debug=False)
    platform.protocol = TestPlatformProtocol

    client = WebSocketServerFactory('ws://127.0.0.1:9001', debug=False)
    client.protocol = TestClientProtocol

    reactor.listenTCP(9000, platform)
    reactor.listenTCP(9001, client)
    reactor.run()
