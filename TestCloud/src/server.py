'''
Created on 2014-1-9

@author: Administrator
'''

from autobahn.twisted.websocket import WebSocketServerProtocol, \
                                       WebSocketServerFactory
import os
import zipfile
import re
import sys
import json
import message
from device import Device

devices = dict()

def canMasterUpdate(model, buildDate):
    path = '\\\\10.204.75.220\\htdocs$\\{0}'
    if not os.path.exists(path.format(model)):
        return None
    update_zip = max(os.listdir(path.format(model)))
    if update_zip:
        update_path = os.path.join(path.format(model), update_zip)
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
                if date > buildDate:
                    return 'http://10.204.75.220:8181/{0}/{1}'.format(model, update_zip)
                break
    return None

class TestCloudProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        #self.tcpip = request.peer.split(':')[0]
        self.device = Device(request.params)

    def onOpen(self):
        print("WebSocket connection open.")
        handler = message.Register(self, self.device)
        handler.send()
        handler = message.MasterUpdater(self, self.device)
        if not handler.send():
            handler = message.TestingRunner(self, self.device)
            handler.send()

    def onMessage(self, payload, isBinary):
        if isBinary:
            print('Binary message received: {0} bytes'.format(len(payload)))
        else:
            text = payload.decode('utf-8')
            print('{0}. Received {1}'.format(self.device.cid, text))
            d = dict(json.loads(text))
            if d['type'] == 7001 and d['progress'] == -2:
                handler = message.TestingRunner(self, self.device)
                handler.send()
            elif d['type'] == 7002 and d['progress'] != 0:
                pass

    def onClose(self, wasClean, code, reason):
        print('WebSocket connection closed: {0}'.format(reason))

if __name__ == '__main__':
    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory('ws://127.0.0.1:9000', debug=False)
    factory.protocol = TestCloudProtocol

    reactor.listenTCP(9000, factory)
    reactor.run()