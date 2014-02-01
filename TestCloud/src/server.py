'''
Created on 2014-1-9

@author: Administrator
'''

from autobahn.twisted.websocket import WebSocketServerProtocol, \
                                       WebSocketServerFactory
import sys
import json
import message
import datetime
from device import Device

clients = dict()

def broadcastOnlineDevices():
    online = []
    msg = message.Message(6001)
    for key in devices:
        online.append(devices[key].getInfo())
    msg.put('online', online)
    for key in clients:
        clients[key].sendMessage(str(msg).encode('utf-8'))

class TestClientProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print('Client connecting: {0}'.format(request.peer))
        self.tcpip = request.peer.split(':')[0]
        clients[self.tcpip] = self

    def onOpen(self):
        print('WebSocket connection open.')

    def onMessage(self, payload, isBinary):
        text = payload.decode('utf-8')
        print('{0}. Received {1}'.format(self.tcpip, text))
        d = dict(json.loads(text))
        if d['type'] == 6001:
            broadcastOnlineDevices()

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))
        if clients.has_key(self.tcpip):
            clients.pop(self.tcpip)

devices = dict()

class TestPlatformProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print('Device connecting: {0}'.format(request.peer))
        self.tcpip = request.peer.split(':')[0]
        devices[self.tcpip] = Device(self, request.params)
        broadcastOnlineDevices()

    def onOpen(self):
        print('WebSocket connection open.')
        handler = message.Register(self, devices[self.tcpip])
        handler.send()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print('Binary message received: {0} bytes'.format(len(payload)))
        else:
            text = payload.decode('utf-8')
            print('{0}. Received {1}'.format(devices[self.tcpip].cid, text))
            d = dict(json.loads(text))
            if d['type'] == 6003:
                queue = []
                msg = message.Message(6003)
                handler = message.MasterUpdater(self, devices[self.tcpip])
                updateUrl = handler.getUpdateUrl()
                if updateUrl:
                    queue.append({'type': 7001, 'updateUrl': updateUrl[0], 'buildDate': updateUrl[1]})
                date = datetime.datetime.now().strftime('%Y-%m-%d')
                timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                params = (devices[self.tcpip].model, date, devices[self.tcpip].cid, timestamp)
                tests = [
                {
                    'id': 1,
                    'name': 'monkey',
                    'cmd': 'monkey -s 25 --ignore-timeouts --ignore-crashes -v 20000 --pct-nav 0 --pct-trackball 0',
                    'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey.txt'.format(*params)
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
                    'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-stress.txt'.format(*params)
                }]
                queue.append({'type': 7002, 'tests': str(tests)})
                msg.put('queue', queue)
                print('{0}. Send {1}'.format(devices[self.tcpip].cid, str(msg)))
                self.sendMessage(str(msg).encode('utf-8'))

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))
        if devices.has_key(self.tcpip):
            devices.pop(self.tcpip)
        broadcastOnlineDevices()

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