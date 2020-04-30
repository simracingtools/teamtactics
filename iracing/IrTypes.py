""" Daemon that can publishes iRacing telemetry values at MQTT topics.

Configure what telemery values from iRacing you would like to publish at which
MQTT topic.
Calculate the geographical and astronomical correct light situation on track. 
Send pit service flags and refuel amount to and receive pit commands from
a buttonbox using a serial connection.
 
This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""
__author__ = "Robert Bausdorf"
__contact__ = "rbausdorf@gmail.com"
__copyright__ = "2020, bausdorf engineering"
#__credits__ = ["One developer", "And another one", "etc"]
__date__ = "2020/01/06"
__deprecated__ = False
__email__ =  "rbausdorf@gmail.com"
__license__ = "GPLv3"
#__maintainer__ = "developer"
__status__ = "Beta"
__version__ = "1.30"

from distutils.log import info

import irsdk
import json
import iracing
import logging

class LocalState:
    ir_connected = False
    date_time = -1
    tick = 0
    lap = 0
    sessionType = ''
    driverIdx = -1
    runningDriverId = ''
    runningDriverName = ''
    runningTeam = ''
    clientId = ''
    teamId = ''
    sessionId = -1
    subSessionId = -1
    collectionName = ''
    sessionNum = -1
    lastLaptime = 0

    def reset(self):
        self.date_time = -1
        self.tick = 0
        self.fuel = 0
        self.lap = 0
        self.sessionType = ''
        self.driverIdx = -1
        self.runningDriverId = ''
        self.runningDriverName = ''
        self.sessionId = -1
        self.subSessionId = -1
        self.sessionNum = -1
        self.collectionName = ''
        self.clientId = ''
        self.teamId = ''
        self.lastLaptime = 0

    def updateRunningDriver(self, ir):
        self.driverIdx = ir['DriverInfo']['DriverCarIdx']
        self.runningDriverId = str(ir['DriverInfo']['Drivers'][self.driverIdx]['UserID'])
        self.runningDriverName = str(ir['DriverInfo']['Drivers'][self.driverIdx]['UserName'])
        self.teamId = str(ir['DriverInfo']['Drivers'][self.driverIdx]['TeamID'])
        self.runningTeam = str(ir['DriverInfo']['Drivers'][self.driverIdx]['TeamName']).replace(' ', '')

    def updateSession(self, ir):
        _sessionChanged = False

        if self.sessionId != ir['WeekendInfo']['SessionID']:
            print('SessionId change from ' + str(self.sessionId) + ' to ' + str(ir['WeekendInfo']['SessionID']))
            self.sessionId = ir['WeekendInfo']['SessionID']
            _sessionChanged = True

        if self.subSessionId != ir['WeekendInfo']['SubSessionID']:
            print('SubSessionId change from ' + str(self.subSessionId) + ' to ' + str(ir['WeekendInfo']['SubSessionID']))
            self.subSessionId = ir['WeekendInfo']['SubSessionID']
            _sessionChanged = True

        if self.sessionNum != ir['SessionNum']:
            print('SessionNum change from ' + str(self.sessionNum) + ' to ' + str(ir['SessionNum']))
            self.sessionNum = ir['SessionNum']
            _sessionChanged = True

        if _sessionChanged:
            self.collectionName = self.getCollectionName(ir)

        return _sessionChanged

    def getCollectionName(self, ir):
        _driverIdx = ir['DriverInfo']['DriverCarIdx']
        teamName = ir['DriverInfo']['Drivers'][_driverIdx]['TeamName']

        if self.sessionId == 0 or ir['DriverInfo']['Drivers'][_driverIdx]['TeamID'] == 0:
            # single session
            car = ir['DriverInfo']['Drivers'][_driverIdx]['CarPath']
            return str(teamName) + '@' + str(car) + '#' + ir['WeekendInfo']['TrackName'] + '#' + str(self.sessionNum)
        else:
            # team session
            return str(teamName) + '@' + str(self.sessionId) + '#' + str(self.subSessionId) + '#' + str(self.sessionNum)

    def itsMe(self, iracingId):
        if self.runningDriverId == iracingId:
            return True

        return False

class LapData:
    lap = 0
    stintLap = 0
    stintCount = 1
    driver = ''
    laptime = 0
    fuelLevel = 0
    trackTemp = 0
    sessionTime = 0

    def __init__(self, currentDriver, ir):
        self.lap = ir['Lap']
        self.fuelLevel = ir['FuelLevel']
        self.trackTemp = ir['TrackTemp']
        self.sessionTime = ir['SessionTime']
        self.laptime = ir['LapLastLapTime']
        self.driver = currentDriver

    def toDict(self):
        _lapdata = {}
        _lapdata['lap'] = self.lap
        _lapdata['driver'] = self.driver
        _lapdata['laptime'] = self.laptime
        _lapdata['fuelLevel'] = self.fuelLevel
        _lapdata['trackTemp'] = self.trackTemp
        _lapdata['sessionTime'] = self.sessionTime

        return _lapdata

    def lapDataMessage(self, state):
        return toMessageJson('lapdata', state, self.toDict())
     
class SessionInfo:
    sessionId = ''
    track = ''
    sessionLaps = 0
    sessionTime = 0
    sessionType = ''
    teamName = ''
    maxFuel = 0
    car = ''
    carId = ''
    trackId = ''

    def __init__(self, sessionId, ir):
        _driverIdx = ir['DriverInfo']['DriverCarIdx']
        _sessionNum = ir['SessionNum']
        self.sessionId = sessionId
        self.track = ir['WeekendInfo']['TrackName']
        self.teamName = ir['DriverInfo']['Drivers'][_driverIdx]['TeamName']
        self.car = ir['DriverInfo']['Drivers'][_driverIdx]['CarScreenName']
        self.maxFuel = ir['DriverInfo']['DriverCarFuelMaxLtr'] * ir['DriverInfo']['DriverCarMaxFuelPct']
        self.sessionLaps = ir['SessionInfo']['Sessions'][_sessionNum]['SessionLaps']
        self.sessionTime = ir['SessionInfo']['Sessions'][_sessionNum]['SessionTime']
        self.sessionType = ir['SessionInfo']['Sessions'][_sessionNum]['SessionType']
        self.trackId = ir['WeekendInfo']['TrackID']
        self.carId = ir['DriverInfo']['Drivers'][_driverIdx]['CarID']
        if self.sessionTime != 'unlimited':
            self.sessionTime = float(ir['SessionInfo']['Sessions'][_sessionNum]['SessionTime'][:-4])


    def toDict(self):
        _info = {}
        _info['track'] = self.track
        _info['sessionId'] = self.sessionId
        _info['sessionLaps'] = self.sessionLaps
        _info['sessionTime'] = self.sessionTime
        _info['sessionType'] = self.sessionType
        _info['teamName'] = self.teamName
        _info['car'] = self.car
        _info['maxFuel'] = self.maxFuel
        _info['carId'] = self.carId
        _info['trackId'] = self.trackId

        return _info

    def sessionDataMessage(self, state):
        return toMessageJson('sessionInfo', state, self.toDict())

class RunData:
    fuelLevel = 0
    flags = []
    sessionTime = -1
    sessionToD = -1
    estLaptime = 0
    lapNo = 0
    timeInLap = -1

    def update(self, ir):
        _changed = False
        if self.fuelLevel != ir['FuelLevel'] and ir['FuelLevel'] > 0:
            _changed = True
            self.fuelLevel = ir['FuelLevel']
        if self.flags != ir['SessionFlags']:
            _changed = True
            self.flags = ir['SessionFlags']
        if self.estLaptime != ir['DriverInfo']['DriverCarEstLapTime']:
            _changed = True
            self.estLaptime = ir['DriverInfo']['DriverCarEstLapTime']

        self.sessionTime = ir['SessionTime']
        self.sessionToD = ir['SessionTimeOfDay']
        self.lapNo = ir['Lap']
        self.timeInLap = ir['LapCurrentLapTime']
        if self.fuelLevel == 0:
            _changed = False
            
        return _changed

    def toDict(self):
        _dict = {}
        _dict['fuelLevel'] = self.fuelLevel
        _dict['flags'] = iracing.checkSessionFlags(self.flags)
        _dict['sessionTime'] = self.sessionTime
        _dict['sessionToD'] = self.sessionToD
        _dict['estLaptime'] = self.estLaptime
        _dict['lapNo'] = self.lapNo
        _dict['timeInLap'] = self.timeInLap

        return _dict

    def runDataMessage(self, state):
        return toMessageJson('runData', state, self.toDict())

    def syncData(self, ir, state):
        _syncData = {}
        _syncData['irid'] = state.clientId
        _syncData['sessionTime'] = ir['SessionTime']

        _driverIdx = ir['DriverInfo']['DriverCarIdx']
        _syncData['isInCar'] = (state.clientId == str(ir['DriverInfo']['Drivers'][_driverIdx]['UserID']))

        return _syncData

    def syncDataMessage(self, state, ir):
        return toMessageJson('syncData', state, self.syncData(ir, state))

class EventData:
    sessionTime = 0.0
    sessionToD = 0.0
    trackLocation = -1
    flags = []
    towTime = 0.0
    repairTime = 0.0
    optRepairTime = 0.0

    def updateEvent(self, state, ir):
        _changed = False
        self.sessionTime = ir['SessionTime']
        self.sessionToD = ir['SessionTimeOfDay']
        self.flags = ir['SessionFlags']
    
        if self.repairTime != ir['PitRepairLeft']:
            self.repairTime = ir['PitRepairLeft']
            _changed = True

        if self.optRepairTime != ir['PitOptRepairLeft']:
            self.optRepairTime = ir['PitOptRepairLeft']
            _changed = True

        if self.towTime != ir['PlayerCarTowTime']:
            self.towTime = ir['PlayerCarTowTime']
            _changed = True

        if self.trackLocation !=  ir['CarIdxTrackSurface'][state.driverIdx]:
            self.trackLocation = ir['CarIdxTrackSurface'][state.driverIdx]
            _changed = True

        return _changed        

    def toDict(self):
        _dict = {}
        _dict['sessionTime'] = self.sessionTime
        _dict['sessionToD'] = self.sessionToD
        _dict['trackLocation'] = self.trackLocation
        _dict['flags'] = self.flags
        _dict['towingTime'] = self.towTime
        _dict['repairTime'] = self.repairTime
        _dict['optRepairTime'] = self.optRepairTime
        return _dict

    def eventDataMessage(self, state):
        return toMessageJson('event', state, self.toDict())

def toMessageJson(type, state, payload):
    _msg = {}
    _msg['type'] = type
    _msg['version'] = __version__
    _msg['sessionId'] = state.collectionName
    _msg['teamId'] = state.teamId
    _msg['clientId'] = state.clientId
    _msg['payload'] = payload

    return json.dumps(_msg)
