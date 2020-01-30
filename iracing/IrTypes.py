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
__version__ = "0.97"

from distutils.log import info

import irsdk
import json

class LocalState:
    ir_connected = False
    date_time = -1
    tick = 0
    lap = 0
    sessionType = ''
    driverIdx = -1
    runningDriverId = ''

    def reset(self):
        self.date_time = -1
        self.tick = 0
        self.fuel = 0
        self.lap = 0
        self.sessionType = ''
        self.driverIdx = -1
        self.runningDriverId = ''

    def updateRunningDriver(self, ir):
        self.driverIdx = ir['DriverInfo']['DriverCarIdx']
        self.runningDriverId = str(ir['DriverInfo']['Drivers'][self.driverIdx]['UserID'])

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

    def __init__(self, syncState, ir):
        self.lap = ir['Lap']
        self.stintLap = syncState.stintLap
        self.stintCount = syncState.stintCount
        self.fuelLevel = ir['FuelLevel']
        self.trackTemp = ir['TrackTemp']
        self.sessionTime = ir['SessionTime'] / 86400
        self.laptime = ir['LapLastLapTime']
        self.driver = syncState.currentDriver

    def toDict(self):
        _lapdata = {}
        _lapdata['lap'] = self.lap
        _lapdata['stintLap'] = self.stintLap
        _lapdata['stintCount'] = self.stintCount
        _lapdata['driver'] = self.driver
        _lapdata['laptime'] = self.laptime / 86400
        _lapdata['fuelLevel'] = self.fuelLevel
        _lapdata['trackTemp'] = self.trackTemp
        _lapdata['sessionTime'] = self.sessionTime

        return _lapdata

    def lapDataMessage(self):
        _lapMsg = toMessageJson('lapdata', self.toDict())
        return json.dumps(_lapMsg)
        
class SyncState:
    lap = 0
    lastLaptime = 0
    stintCount = 0
    stintLap = 0
    enterPits = 0
    exitPits = 0
    stopMoving = 0
    startMoving = 0
    sessionId = -1
    subSessionId = -1
    sessionNum = -1
    currentDriver = ''
    trackLocation = -1
    serviceFlags = 0
    pitRepairLeft = 0
    pitOptRepairLeft = 0
    towTime = 0
    pitState = ''

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

        return _sessionChanged

    def updateDriver(self, driver):
        if self.currentDriver != driver:
            self.currentDriver = driver
            return True

        return False
        
    def fromDict(self, dict, driver = ''):
        try:
            self.lap = dict['lap']
            self.lastLaptime = dict['lapTime']
            self.stintCount = dict['stintCount']
            self.stintLap = dict['stintLap']
            self.enterPits = dict['enterPits']
            self.exitPits = dict['exitPits']
            self.stopMoving = dict['stopMoving']
            self.startMoving = dict['startMoving']
            self.sessionId = dict['sessionId']
            self.subSessionId = dict['subSessionId']
            self.sessionNum = dict['sessionNum']
            if driver != '':
                self.currentDriver = dict['currentDriver']
            else:
                self.currentDriver = driver
            self.pitRepairLeft = dict['pitRepairLeft']
            self.pitOptRepairLeft = dict['pitOptRepairLeft']
            self.towTime = dict['towTime']
            self.pitState = dict['pitState']
        except Exception as ex:
            print('Problem: ' + str(ex))
    
    def toDict(self):
        _syncState = {}
        _syncState['lap'] = self.lap
        _syncState['lapTime'] = self.lastLaptime
        _syncState['stintCount'] = self.stintCount
        _syncState['stintLap'] = self.stintLap
        _syncState['enterPits'] = self.enterPits
        _syncState['exitPits'] = self.exitPits
        _syncState['stopMoving'] = self.stopMoving
        _syncState['startMoving'] = self.startMoving
        _syncState['sessionId'] = self.sessionId
        _syncState['subSessionId'] = self.subSessionId
        _syncState['sessionNum'] = self.sessionNum
        _syncState['currentDriver'] = self.currentDriver
        _syncState['serviceFlags'] = self.serviceFlags
        _syncState['pitRepairLeft'] = self.pitRepairLeft
        _syncState['pitOptRepairLeft'] = self.pitOptRepairLeft
        _syncState['towTime'] = self.towTime
        _syncState['pitState'] = self.pitState

        return _syncState
    
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

    def updatePits(self, state, ir):
        if self.lap <= 1:
            # dont count starting from box as pitstop
            return

        if self.pitRepairLeft == 0:
            self.pitRepairLeft = ir['PitRepairLeft']

        if self.pitOptRepairLeft == 0:
            self.pitOptRepairLeft = ir['PitOptRepairLeft']

        if self.towTime == 0:
            self.towTime = ir['PlayerCarTowTime']
        
        _trackLocation = ir['CarIdxTrackSurface'][state.driverIdx]
        _sessionTime = ir['SessionTime']
        #irsdk_NotInWorld       -1
        #irsdk_OffTrack          0
        #irsdk_InPitStall        1
        #irsdk_AproachingPits    2
        #irsdk_OnTrack           3
        if _trackLocation > 0 and self.trackLocation != _trackLocation:
            # check only if no OffTrack and no NotInWorld
            self.trackLocation = _trackLocation

            if self.pitState == '' and (_trackLocation == 2 or _trackLocation == 1):
                print('Enter pits: ' + str(_sessionTime))
                self.enterPits = _sessionTime / 86400
                self.serviceFlags = ir['PitSvFlags']
                self.pitState = 'ENTER'
            elif self.pitState == 'ENTER' and _trackLocation == 1:
                print('Stop moving: ' + str(_sessionTime))
                self.stopMoving = _sessionTime / 86400
                self.pitState = 'SERVICE'
            elif self.pitState == 'SERVICE' and _trackLocation == 2:
                print('Start moving: ' + str(_sessionTime))
                self.startMoving = _sessionTime / 86400
                self.pitState = 'EXIT'
            elif self.pitState == 'EXIT' and _trackLocation == 3:
                print('Exit pits: ' + str(_sessionTime))
                self.exitPits = _sessionTime / 86400

                self.stintCount += 1
                self.stintLap = 0

    def isPitopComplete(self):
        if self.enterPits > 0 and self.exitPits > 0:
            return True

        return False

    def resetPitstop(self):
        self.enterPits = 0
        self.exitPits = 0
        self.stopMoving = 0
        self.startMoving = 0
        self.pitOptRepairLeft = 0
        self.pitRepairLeft = 0
        self.towTime = 0
        self.pitState = ''

    def updateLap(self, lap, laptime):
        if self.lap != lap: # and laptime > 0:
            _lapDelta = lap - self.lap
            self.lap = lap
            self.lastLaptime = laptime
            self.stintLap += _lapDelta
            
        if self.stintCount == 0:
            self.stintCount = 1
            self.stintLap = lap

    def pitstopData(self):
        _pitstopData = {}
        _pitstopData['stint'] = self.stintCount - 1
        _pitstopData['lap'] = self.lap
        _pitstopData['driver'] = self.currentDriver
        _pitstopData['enterPits'] = self.enterPits
        _pitstopData['stopMoving'] = self.stopMoving
        _pitstopData['startMoving'] = self.startMoving
        _pitstopData['exitPits'] = self.exitPits
        _pitstopData['serviceFlags'] = self.serviceFlags
        _pitstopData['repairLeft'] = self.pitRepairLeft / 86400
        _pitstopData['optRepairLeft'] = self.pitOptRepairLeft / 86400
        _pitstopData['towTime'] = self.towTime / 86400

        return _pitstopData

    def pitstopDataMessage(self):
        return json.dumps(toMessageJson('pitstop', self.pitstopData()))

class SessionInfo:
    version = __version__
    sessionId = ''
    track = ''
    sessionLaps = 0
    sessionTime = 0
    sessionType = ''
    teamName = ''
    maxFuel = 0
    car = ''

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
        if self.sessionTime != 'unlimited':
            self.sessionTime = float(ir['SessionInfo']['Sessions'][_sessionNum]['SessionTime'][:-4]) / 86400


    def toDict(self):
        _info = {}
        _info['version'] = self.version
        _info['track'] = self.track
        _info['sessionId'] = self.sessionId
        _info['sessionLaps'] = self.sessionLaps
        _info['sessionTime'] = self.sessionTime
        _info['sessionType'] = self.sessionType
        _info['teamName'] = self.teamName
        _info['car'] = self.car
        _info['maxFuel'] = self.maxFuel

        return _info

    def sessionDataMessage(self):
        return json.dumps(toMessageJson('sessionInfo', self.toDict()))

def toMessageJson(type, payload):
    _msg = {}
    _msg['type'] = type
    _msg['payload'] = payload

    return json.dumps(_msg)


