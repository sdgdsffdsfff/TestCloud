# -*- coding: UTF-8 -*-
'''
Created on 2014-2-4

@author: Administrator
'''

import json
import os
import re
import zipfile

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
    l = r.findall(date)
    return '{0}-{1}-{2} {3}:{4}:{5}'.format(*l)

def getUpdateInfo(model, buildDate):
    parent = '\\\\10.204.75.220\\htdocs$\\{0}'.format(model)
    if os.path.exists(parent):
        name = max(os.listdir(parent))
        path = os.path.join(parent, name)
        z = zipfile.ZipFile(path, 'r')
        date = getBuildDate(z)
        if date > buildDate:
            return ('http://10.204.75.220:8181/{0}/{1}'.format(model, name), date)

if __name__ == '__main__':
    print getUpdateInfo('NX503A', '2014-01-04 12:12:12')
