# -*- coding: UTF-8 -*-
'''
Created on 2014-2-4

@author: Administrator
'''

import datetime
import json
import os
import re
import zipfile

DEF_TESTS = [
    '{"id": 1, "type": 7001, "params": "2000"}',
    '{"id": 2, "type": 7002, "params": "100 10"}',
    '{"id": 3, "type": 7003, "params": "100 10"}',
    '{"id": 4, "type": 7004, "params": "100 10"}',
    '{"id": 5, "type": 7005, "params": "100 10"}',
    '{"id": 6, "type": 7006, "params": "100 10"}',
    '{"id": 7, "type": 7007, "params": "100 10"}',
    '{"id": 8, "type": 7008, "params": "--ei times 1"}'
]

OPT_TESTS = {
    7001: {
        'name': 'monkey',
        'cmd': 'monkey -s 25 --ignore-timeouts --ignore-crashes -v {0} --pct-nav 0 --pct-trackball 0'
    },
    7002: {
        'name': 'monkey-com.android.gallery3d',
        'cmd': 'sh start_monkey_exit.sh com.android.gallery3d com.android.camera.CameraLauncher {0}'
    },
    7003: {
        'name': 'monkey-com.android.contacts.people',
        'cmd': 'sh start_monkey_exit.sh com.android.contacts com.android.contacts.activities.PeopleActivity {0}'
    },
    7004: {
        'name': 'monkey-com.android.mms',
        'cmd': 'sh start_monkey_exit.sh com.android.mms com.android.mms.ui.FunctionSwitchActivity {0}'
    },
    7005: {
        'name': 'monkey-com.android.contacts.dialer',
        'cmd': 'sh start_monkey_exit.sh com.android.contacts com.android.contacts.DialerActivity {0}'
    },
    7006: {
        'name': 'monkey-com.android.settings',
        'cmd': 'sh start_monkey_exit.sh com.android.settings com.android.settings.Settings {0}'
    },
    7007: {
        'name': 'monkey-com.android.strengthenmusic',
        'cmd': 'sh start_monkey_exit.sh com.android.strengthenmusic com.android.strengthenmusic.ui.MusicWelcome {0}'
    },
    7008: {
        'name': 'stress',
        'cmd': 'am start -n com.ztemt.test.auto/.AutoTestActivity --es mode auto {0}'
    }
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

def getBuildProp(z, prop):
    bp = z.read('system/build.prop')
    m = re.search(re.escape(prop) + r'=(.*)\n', bp)
    if m:
        return m.group(1).strip()

def getBuildDate(z):
    date = getBuildProp(z, 'ro.build.date')
    r = re.compile('\d+')
    p = r.findall(date)
    return '{0}-{1}-{2} {3}:{4}:{5}'.format(*p)

def getUpdateInfo(model, buildDate):
    parent = '\\\\10.204.75.220\\htdocs$\\{0}'.format(model)
    if os.path.exists(parent):
        name = max(os.listdir(parent))
        path = os.path.join(parent, name)
        z = zipfile.ZipFile(path, 'r')
        date = getBuildDate(z)
        if date > buildDate:
            return ('http://10.204.75.220:8181/{0}/{1}'.format(model, name), date)

def sendTask(device, update=True, tests=None):
    queue = []
    msg = Message(6003)
    updateInfo = getUpdateInfo(device.model, device.buildDate)
    if updateInfo and update:
        queue.append({'type': 7001, 'updateUrl': updateInfo[0], 'buildDate': updateInfo[1]})
    buildDate = ''.join([s for s in device.buildDate if s.isdigit()])
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    items = []
    tests = tests if tests else DEF_TESTS
    for test in tests:
        d = dict(json.loads(test))
        i = d['id']
        t = d['type']
        params = d['params']
        name = OPT_TESTS[t]['name']
        cmd = OPT_TESTS[t]['cmd'].format(params)
        paths = (device.deviceId, device.build, buildDate, timestamp, name)
        items.append({
            'id': i,
            'name': name,
            'cmd': cmd,
            'uploadPath': '/pub/log/{0}/{1}/{2}/{3}-{4}.txt'.format(*paths)
        })
    queue.append({'type': 7002, 'tests': str(items)})
    msg.put('queue', queue)
    device.protocol.sendMessage(str(msg).encode('utf-8'))

if __name__ == '__main__':
    print getUpdateInfo('NX503A', '2014-01-04 12:12:12')
