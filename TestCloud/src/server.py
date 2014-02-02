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

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))
        if clients.has_key(self.deviceId):
            clients.pop(self.deviceId)

devices = dict()

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
                queue = []
                msg = Message(6003)
                updateUrl = self.getUpdateUrl()
                if updateUrl and False:
                    queue.append({'type': 7001, 'updateUrl': updateUrl[0], 'buildDate': updateUrl[1]})
                #date = datetime.datetime.now().strftime('%Y-%m-%d')
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                params = (timestamp, self.device.build, self.device.buildDate.replace('-', '').replace(':', '').replace(' ', ''))
                tests = [
                {
                    'id': 1,
                    'name': 'monkey',
                    'cmd': 'monkey -s 25 --ignore-timeouts --ignore-crashes -v 20000 --pct-nav 0 --pct-trackball 0',
                    'uploadPath': '/pub/log/{0}/{1}-{2}-monkey.txt'.format(*params)
                },
#                 {
#                     'id': 2,
#                     'name': 'monkey-com.android.gallery3d',
#                     'cmd': 'sh start_monkey_exit.sh com.android.gallery3d com.android.camera.CameraLauncher 10000 10',
#                     'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.gallery3d.txt'.format(*params)
#                 },
#                 {
#                     'id': 3,
#                     'name': 'monkey-com.android.contacts.people',
#                     'cmd': 'sh start_monkey_exit.sh com.android.contacts com.android.contacts.activities.PeopleActivity 10000 10',
#                     'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.contacts.people.txt'.format(*params)
#                 },
#                 {
#                     'id': 4,
#                     'name': 'monkey-com.android.mms',
#                     'cmd': 'sh start_monkey_exit.sh com.android.mms com.android.mms.ui.FunctionSwitchActivity 10000 10',
#                     'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.mms.txt'.format(*params)
#                 },
#                 {
#                     'id': 5,
#                     'name': 'monkey-com.android.contacts.dialer',
#                     'cmd': 'sh start_monkey_exit.sh com.android.contacts com.android.contacts.DialerActivity 10000 10',
#                     'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.contacts.dialer.txt'.format(*params)
#                 },
#                 {
#                     'id': 6,
#                     'name': 'monkey-com.android.settings',
#                     'cmd': 'sh start_monkey_exit.sh com.android.settings com.android.settings.Settings 10000 10',
#                     'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.settings.txt'.format(*params)
#                 },
#                 {
#                     'id': 7,
#                     'name': 'monkey-com.android.strengthenmusic',
#                     'cmd': 'sh start_monkey_exit.sh com.android.strengthenmusic com.android.strengthenmusic.ui.MusicWelcome 10000 10',
#                     'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.strengthenmusic.txt'.format(*params)
#                 },
                {
                    'id': 8,
                    'name': 'stress',
                    'cmd': 'am start -n com.ztemt.test.auto/.AutoTestActivity --es mode auto --ei times 10',
                    'uploadPath': '/pub/log/{0}/{1}-{2}-stress.txt'.format(*params)
                }]
                queue.append({'type': 7002, 'tests': str(tests)})
                msg.put('queue', queue)
                self.sendMessage(str(msg).encode('utf-8'))

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))
        if devices.has_key(self.deviceId):
            devices[self.deviceId].online = 0
        broadcastDevices()

    def getUpdateUrl(self):
        path = '\\\\10.204.75.220\\htdocs$\\{0}'
        if not os.path.exists(path.format(self.device.model)):
            return None
        update_zip = max(os.listdir(path.format(self.device.model)))
        if update_zip:
            update_path = os.path.join(path.format(self.device.model), update_zip)
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
                    if date > self.device.buildDate:
                        return ('http://10.204.75.220:8181/{0}/{1}'.format(self.device.model, update_zip), date)
        return None

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