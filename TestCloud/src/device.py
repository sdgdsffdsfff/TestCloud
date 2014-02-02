'''
Created on 2014-1-14

@author: Administrator
'''

import sqlite3
import json

class Device:

    DB_NAME = 'testcloud.db'

    def __init__(self, protocol, params):
        self.protocol  = protocol
        self.deviceId  = params['deviceId'][0]
        self.platform  = params['platform'][0]
        self.version   = params['version'][0]
        self.model     = params['model'][0]
        self.baseband  = params['baseband'][0]
        self.build     = params['build'][0]
        self.address   = params['address'][0]
        self.user      = params['user'][0]
        self.buildDate = params['buildDate'][0]

        #self.cid = self.register()
        #self.updateBuildDate()

    def __str__(self):
        return json.dumps({
                'deviceId': self.deviceId,
                'platform': self.platform,
                'version': self.version,
                'model': self.model,
                'baseband': self.baseband,
                'build': self.build,
                'address': self.address,
                'user': self.user,
                'buildDate': self.buildDate
        })

    def getInfo(self):
        return {
                'deviceId': self.deviceId,
                'platform': self.platform,
                'version': self.version,
                'model': self.model,
                'baseband': self.baseband,
                'build': self.build,
                'address': self.address,
                'user': self.user,
                'buildDate': self.buildDate,
                'ip': self.protocol.tcpip
        }

    def queryId(self):
        conn = sqlite3.connect(self.DB_NAME)
        cur = conn.cursor()
        cur.execute('select id from devices where device_id=? and platform=? and version=? and model=? and build=? and address=? and user=?', (self.deviceId, self.platform, self.version, self.model, self.build, self.address, self.user))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else 0

    def generateId(self):
        conn = sqlite3.connect(self.DB_NAME)
        cur = conn.cursor()
        cur.execute('insert into devices(device_id,platform,version,model,baseband,build,address,user,build_date) values (?,?,?,?,?,?,?,?,?)', (self.deviceId, self.platform, self.version, self.model, self.baseband, self.build, self.address, self.user, self.buildDate))
        conn.commit()
        cur.close()
        conn.close()
        return self.queryId()

    def updateBuildDate(self):
        conn = sqlite3.connect(self.DB_NAME)
        cur = conn.cursor()
        cur.execute('update devices set build_date=? where id=?', (self.buildDate, self.cid))
        conn.commit()
        cur.close()
        conn.close()

    def register(self):
        cid = self.queryId()
        if not cid:
            cid = self.generateId()
        return cid