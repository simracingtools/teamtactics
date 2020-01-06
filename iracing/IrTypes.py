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
from distutils.log import info

import irsdk
import json

class LapData:
    lap = 0
    driver = ''
    laptime = 0
    fuelLevel = 0
    trackTemp = 0
    sessionTime = 0

    def __init__(self, ir, driver):
        self.lap = ir['Lap']
        self.fuelLevel = ir['FuelLevel']
        self.trackTemp = ir['TrackTemp']
        self.sessionTime = ir['SessionTime'] / 86400
        self.laptime = ir['LapLastLapTime']
        self.driver = driver

    def toDict(self):
        _lapdata = {}
        _lapdata['Lap'] = self.lap
        _lapdata['Driver'] = self.driver
        _lapdata['Laptime'] = self.laptime
        _lapdata['FuelLevel'] = self.fuelLevel
        _lapdata['TrackTemp'] = self.trackTemp
        _lapdata['SessionTime'] = self.sessionTime

        return _lapdata

    def toJson(self):

        _lapJson = json.dumps(LapData.toDict(self))

        return _lapJson

class SyncState:
    lap = 0
    lastLaptime = 0
    stintCount = 1
    stintLap = 0
    enterPits = 0
    exitPits = 0
    stopMoving = 0
    startMoving = 0
    sessionId = ''
    subSessionId = ''
    sessionNum = 0
    currentDriver = ''
    trackLocation = -1

    def updateSession(self, sessionId, subSessionId, sessionNum):
        self.sessionId = sessionId
        self.subSessionId = subSessionId
        self.sessionNum = sessionNum

    def updateDriver(self, driver):
        self.currentDriver = driver
        
    def fromDict(self, dict):
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
        self.currentDriver = dict['currentDriver']
    
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

        return _syncState
    
    def updatePits(self, lap, trackLocation, sessionTime):
        #irsdk_NotInWorld       -1
        #irsdk_OffTrack          0
        #irsdk_InPitStall        1
        #irsdk_AproachingPits    2
        #irsdk_OnTrack           3

        if trackLocation == 3 and lap != self.lap and self.exitPits > 0:
            # reset pit times 
            self.enterPits = 0
            self.stopMoving = 0
            self.startMoving = 0
            self.exitPits = 0

        if trackLocation > 0 and self.trackLocation != trackLocation:
            # check only if no OffTrack and no NotInWorld
            self.trackLocation = trackLocation

            if trackLocation == 2:
                if self.enterPits == 0:
                    self.enterPits = sessionTime / 86400
                elif self.startMoving == 0 and self.stopMoving > 0:
                    self.startMoving = sessionTime / 86400
            elif trackLocation == 1:
                if self.stopMoving == 0:
                    self.stopMoving = sessionTime / 86400
            elif trackLocation == 3:
                if self.exitPits == 0:
                    self.exitPits = sessionTime / 86400

                    self.stintCount += 1
                    self.stintLap = 0

    def updateLap(self, lap, laptime):
        if self.lap != lap and laptime > 0:
            self.lap = lap
            self.lastLaptime = laptime / 86400
            self.stintLap += 1

    def pitstopData(self):
        _pitstopData = {}
        _pitstopData['stint'] = self.stintCount
        _pitstopData['enterPits'] = self.enterPits
        _pitstopData['stopMoving'] = self.stopMoving
        _pitstopData['startMoving'] = self.startMoving
        _pitstopData['exitPits'] = self.exitPits

        return _pitstopData
