#!python3
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
from _ast import Not

__author__ = "Robert Bausdorf"
__contact__ = "rbausdorf@gmail.com"
__copyright__ = "2019, bausdorf engineering"
#__credits__ = ["One developer", "And another one", "etc"]
__date__ = "2019/06/01"
__deprecated__ = False
__email__ =  "rbausdorf@gmail.com"
__license__ = "GPLv3"
#__maintainer__ = "developer"
__status__ = "Beta"
__version__ = "0.8"

import sys
import configparser
import irsdk
import os
import time
import json
import logging
from google.cloud import firestore
from datetime import datetime
from datetime import timedelta

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    date_time = -1
    tick = 0
    lap = 0
    sessionId = -1
    subSessionId = -1
    sessionNum = -1

class TeamState:
    teamName = ''
    currentDriver = ''
    overallPosition = -1
    classPosition = -1
    lap = 0
    lastLaptime = 0
    onPitRoad = -1
    trackLoc = -1
    pitstops = []
    
    def fromDict(self, dict):
        self.teamName = dict['teamName']
        self.currentDriver = dict['currentDriver']
        self.overallPosition = dict['overallPosition']
        self.classPosition = dict['classPosition']
        self.lap = dict['lap']
        self.lastLaptime = dict['lastLaptime']
        self.onPitRoad = dict['onPitRoad']
        self.trackLoc = dict['traclLoc']
        self.pitstops = dict['pitstops']
    
    def toDict(self):
        dict = {}
        dict['teamName'] = self.teamName
        dict['currentDriver'] = self.currentDriver
        dict['overallPosition'] = self.overallPosition
        dict['classPosition'] = self.classPosition
        dict['lap'] = self.lap
        dict['lastLapTime'] = self.lastLaptime
        dict['onPitRoad'] = self.onPitRoad
        dict['tracLoc'] = self.trackLoc
        dict['pitstops'] = self.pitstops

        return dict

class TrackEvent:
    currentDriver = ''
    type = ''
    sessionTime = -1

# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():        
    
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset all your in State variables
        state.date_time = -1
        state.tick = 0
        state.lap = 0
        state.sessionId = -1
        state.subSessionId = -1
        state.sessionNum = -1

        # we are shut down ir library (clear all internal variables)
        ir.shutdown()
        print('irsdk disconnected')

    elif not state.ir_connected:
        # Check if a dump file should be used to startup IRSDK
        if config.has_option('global', 'simulate'):
            is_startup = ir.startup(test_file=config['global']['simulate'])
            print('starting up using dump file: ' + str(config['global']['simulate']))
        else:
            is_startup = ir.startup()
            if debug:
                print('DEBUG: starting up with simulation')

        if is_startup and ir.is_initialized and ir.is_connected:
            state.ir_connected = True
            # Check need and open serial connection

            print('irsdk connected')

            checkSessionChange()

            collectionName = getCollectionName()
            print(collectionName)
#            col_ref = db.collection(collectionName)
#            if state.sessionType == 'single':
#                try:
#                    docs = list(col_ref.stream())
#                    if len(docs) > 0:
#                        print('Single session, deleting all data in collection ' + collectionName)
#                        for doc in docs:
#                            doc.reference.delete()
#                    
#                    col_ref.document('Info').set(getInfoDoc())
#                except Exception as ex:
#                    print('Firestore error: ' + str(ex))

def getCollectionName():

    trackName = ir['WeekendInfo']['TrackName']
    return str(trackName) + '@' + state.sessionId + '#' + state.subSessionId + '#' + str(state.sessionNum)

def checkPitRoad():
        
        try:
            col_ref = db.collection(collectionName).document('Info')
            col_ref.set(infodoc)
        except Exception as ex:
            print('Unable to write info document: ' + str(ex))

def checkSessionChange():
    sessionChange = False
    
    if state.sessionId != str(ir['WeekendInfo']['SessionID']):
        state.sessionId = str(ir['WeekendInfo']['SessionID'])
        sessionChange = True
                
    if state.subSessionId != str(ir['WeekendInfo']['SubSessionID']):
        state.subSessionId = str(ir['WeekendInfo']['SubSessionID'])
        sessionChange = True

    if state.sessionNum != ir['SessionNum']:
        state.sessionNum = ir['SessionNum']
        sessionChange = True

# our main loop, where we retrieve data
# and do something useful with it
def loop():
    # on each tick we freeze buffer with live telemetry
    # it is optional, useful if you use vars like CarIdxXXX
    # in this way you will have consistent data from this vars inside one tick
    # because sometimes while you retrieve one CarIdxXXX variable
    # another one in next line of code can be changed
    # to the next iracing internal tick_count
    ir.freeze_var_buffer_latest()

    state.tick += 1

    collectionName = getCollectionName()
    col_ref = db.collection(collectionName)
    
    # check for pit enter/exit
    #checkPitRoad()

    driverList = ir['DriverInfo']['Drivers']
    positions = ir['SessionInfo']['Sessions'][state.sessionNum]['ResultsPositions']
    if positions == None:
        return
    
    position = 0
    while position < len(positions):
        driverIdx = positions[position]['CarIdx']
        driver = driverList[driverIdx]
        dict = {}
    #if lap != state.lap and lastLaptime != state.lastLaptime:
        state.lap = lap

        dict['teamName'] = driver['TeamName']
        dict['currentDriver'] = driver['UserName']
        dict['overallPosition'] = position
        dict['classPosition'] = positions[position]['ClassPosition']
        dict['lap'] = ir['CarIdxLap'][driverIdx]
        dict['lastLapTime'] = positions[position]['LastTime'] / 86400
        dict['SessionTime'] = ir['SessionTime'] / 86400

        dict['onPitRoad'] = ir['CarIdxOnPitRoad'][driverIdx]
        dict['trackLoc'] = ir['CarIdxTrackSurface']
        dict['pitstops'] = []

        dataChanged = False
        
        if teams[driverIdx]:
            teams[driverIdx]['teamName'] = driver['TeamName']
            teams[driverIdx]['currentDriver'] = driver['UserName']
            teams[driverIdx]['overallPosition'] = position
            teams[driverIdx]['classPosition'] = positions[position]['ClassPosition']
            teams[driverIdx]['lap'] = ir['CarIdxLap'][driverIdx]
            teams[driverIdx]['lastLapTime'] = positions[position]['LastTime'] / 86400
            teams[driverIdx]['SessionTime'] = ir['SessionTime'] / 86400

            if teams[driverIdx]['onPitRoad'] != dict['onPitRoad']:
                trackEvent = TrackEvent()
                trackEvent.currentDriver = driver['UserName']
                if dict['onPitRoad']:
                    trackEvent.type = 'PitEnter'
                else:
                    trackEventType = 'PitExit'

                teams[driverIdx]['pitstops'].append(pitEvent)
                dataChanged = True
            
            if teams[driverIdx]['trackLoc'] != dict['trackLoc']:
                trackEvent = TrackEvent()
                trackEvent.currentDriver = driver['UserName']
                #irsdk_NotInWorld       -1
                #irsdk_OffTrack          0
                #irsdk_InPitStall        1
                #irsdk_AproachingPits    2
                #irsdk_OnTrack           3
                if dict['trackLoc'] == -1:
                    trackEvent.type = 'OffWorld'
                elif dict['trackLoc'] == 0:
                    trackEvent.type = 'OffTrack'
                elif dict['trackLoc'] == 1:
                    trackEvent.type = 'InPitStall'
                elif dict['trackLoc'] == 2:
                    trackEvent.type = 'AproachingPits'
                elif dict['trackLoc'] == 3:
                    trackEvent.type = 'OnTrack'

                teams[driverIdx]['events'].append(trackEvent)
                dataChanged = True
        else:
            teams[driverIdx] = dict
            dataChanged = True

        if dataChanged:
            print(json.dumps(teams[driverIdx]))
#        if iracingId == str(ir['DriverInfo']['Drivers'][state.driverIdx]['UserID']):
#           try:
#                col_ref.document(str(lap)).set(data)
#            except Exception as ex:
#                print('Unable to write lap data for lop ' + str(lap) + ': ' + str(ex))
#            try:
#                col_ref.document('State').set(syncState.toDict())
#            except Exception as ex:
#                print('Unable to write state document: ' + str(ex))

    else:
        checkSessionChange()


def banner():
    print("=============================")
    print("|   iRacing Race Control    |")
    print("|           " + str(__version__) + "            |")
    print("=============================")


# Here is our main program entry
if __name__ == '__main__':
    # Read configuration file
    config = configparser.ConfigParser()    
    try: 
        config.read('irtactics.ini')
    except Exception as ex:
        print('unable to read configuration: ' + str(ex))
        sys.exit(1)

    # Print banner an debug output status
    banner()
    if config.has_option('global', 'debug'):
        debug = config.getboolean('global', 'debug')
    else:
        debug = False
    
    if debug:
        print('Debug output enabled')

    if config.has_option('global', 'proxy'):
        proxyUrl = str(config['global']['proxy'])
        os.environ['http_proxy'] = proxyUrl
        os.environ['https_proxy'] = proxyUrl

    if config.has_option('global', 'firebase'):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './' + str(config['global']['firebase'])
        if debug:
            print('Use Google Credential file ' + os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

        try:
            db = firestore.Client()
        except Exception as ex:
            print('Unable to connect to Firebase: ' + str(ex))
            sys.exit(1)

    else:
        print('option firebase not configured or irtactics.ini not found')
        sys.exit(1)
        
    if config.has_option('global', 'logfile'):
        logging.basicConfig(filename=str(config['global']['logfile']),level=logging.INFO)

    if config.has_option('global', 'iracingId'):
        iracingId = config['global']['iracingId']
        print('iRacing ID: ' + str(iracingId))
    else:
        print('option iRacingId not configured or irtactics.ini not found')
        sys.exit(1)

    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    teams = []
    # Project ID is determined by the GCLOUD_PROJECT environment variable

    try:
        # infinite loop
        while True:
            # check if we are connected to iracing
            check_iracing()
                
            # if we are, then process data
            if state.ir_connected:
                loop()

            # sleep for half a second
            # maximum you can use is 1/60
            # cause iracing update data with 60 fps
            time.sleep(0.5)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        print('exiting')
        time.sleep(1)
        pass