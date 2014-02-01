'''
Created on 2014-1-14

@author: Administrator
'''

import json
import os
import zipfile
import re
import datetime

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

class MessageHandler:

    def __init__(self, protocol, device):
        self.protocol = protocol
        self.device = device

    def send(self):
        message = self.getSendMessage()
        if message:
            self.protocol.sendMessage(str(message).encode('utf-8'))
            print('{0}. Send {1}'.format(self.device.cid, str(message)))
            return True
        else:
            return False

    def getSendMessage(self):
        pass

class Register(MessageHandler):

    def getSendMessage(self):
        message = Message(6001)
        message.put('clientId', self.device.cid)
        return message

class MasterUpdater(MessageHandler):

    def getSendMessage(self):
        updateUrl = self.getUpdateUrl()
        if updateUrl:
            message = Message(7001)
            message.put('updateUrl', updateUrl[0])
            message.put('buildDate', updateUrl[1])
            return message
        else:
            return None

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
                    break
        return None

class TestingRunner(MessageHandler):

    def getSendMessage(self):
        message = Message(7002)
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        params = (self.device.model, date, self.device.cid, timestamp)
        tests = [{
                  'id': 1,
                  'type': 'command',
                  'name': 'monkey',
                  'cmd': 'monkey -s 31 --ignore-crashes --ignore-timeouts --ignore-native-crashes -v -v -v 50000',
                  'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey.txt'.format(*params)
                 },
                 {
                  'id': 2,
                  'type': 'command',
                  'name': 'monkey-com.android.settings',
                  'cmd': 'sh start_monkey_exit.sh com.android.settings com.android.settings.Settings 100 5',
                  'uploadPath': '/pub/log/monkey/{0}/{1}/{2}-{3}-monkey-com.android.settings.txt'.format(*params)
                 }]
        message.put('tests', tests)
        return message

if __name__ == '__main__':
    message = Message(7002)
    users = [{'name': 'tom', 'age': 22}, {'name': 'anny', 'age': 18}]
    message.put('users', users)
    print(str(message))