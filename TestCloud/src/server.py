'''
Created on 2014-1-9

@author: Administrator
'''

from autobahn.twisted.websocket import WebSocketServerProtocol, \
                                       WebSocketServerFactory
import json
import message
import sys

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

clients = dict()

def broadcastDevices():
    online = []
    msg = message.Message(6001)
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
            message.sendTask(devices[d['deviceId']], bool(d['update']), d['tests'])

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
                message.sendTask(devices[self.deviceId])

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
