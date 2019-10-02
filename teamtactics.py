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
__version__ = "0.9"

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
    stintCount = 1
    stintLap = 0
    lastLaptime = 0
    fuel = 0
    onPitRoad = -1
    enterPits = 0
    exitPits = 0
    sessionId = ''
    subSessionId = ''
    currentDriver = ''

# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():        
    
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset all your in State variables
        state.date_time = -1
        state.tick = 0
        state.fuel = 0
        state.lap = 0
        state.stintCount = 1
        state.stintLap = 0
        state.lastLaptime = 0
        state.onPitRoad = -1
        state.enterPits = 0
        state.exitPits = 0
        state.sessionId = ''
        state.subSessionId = ''
        state.currentDriver = ''

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

def checkDriver(driverIdx):
    currentDriver = ir['DriverInfo']['Drivers'][driverIdx]['UserName']

    if state.currentDriver != currentDriver:
        print('Driver: ' + currentDriver)
        state.currentDriver = currentDriver

def getCollectionName(driverIdx, collectionType):
    if collectionType == 'test':
        car = ir['DriverInfo']['Drivers'][driverIdx]['CarPath']
        return iracingId + '@' + str(car) + '#' + ir['WeekendInfo']['TrackName']
    else:
        teamId = ir['DriverInfo']['Drivers'][driverIdx]['TeamID']
        if state.sessionId == '0':
            print('This seems to be an offline session, try restart in test mode')
            sys.exit(1)

        return str(teamId) + '@' + state.sessionId + '#' + state.subSessionId

def getInfoDoc(sessionNum, driverIdx):
    info = {}
    info['Track'] = ir['WeekendInfo']['TrackName']
    info['SessionLaps'] = ir['SessionInfo']['Sessions'][sessionNum]['SessionLaps']
    info['SessionTime'] = ir['SessionInfo']['Sessions'][sessionNum]['SessionTime']
    if info['SessionTime'] != 'unlimited':
        info['SessionTime'] = float(ir['SessionInfo']['Sessions'][sessionNum]['SessionTime'][:-4]) / 86400
    info['SessionType'] = ir['SessionInfo']['Sessions'][sessionNum]['SessionType']
    info['TeamName'] = ir['DriverInfo']['Drivers'][driverIdx]['TeamName']

    return info

def checkPitRoad():
    if ir['OnPitRoad']:
        if state.onPitRoad == 0:
            state.enterPits = float(ir['SessionTimeOfDay'])-3600
            print('Enter pitroad: ' + str(state.enterPits))
            state.onPitRoad = 1
        elif state.onPitRoad == -1:
            state.onPitRoad = 1
    else:
        if state.onPitRoad == 1:
            state.exitPits = float(ir['SessionTimeOfDay'])-3600
            print('Exit pitroad: ' + str(state.exitPits))
            state.onPitRoad = 0
        elif state.onPitRoad == -1:
            state.onPitRoad = 0

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
    lap = ir['LapCompleted']
    lastLaptime = 0
    if ir['LapLastLapTime'] > 0:
        lastLaptime = ir['LapLastLapTime']
    
    driverIdx = ir['DriverInfo']['DriverCarIdx']
    sessionNum = ir['SessionNum']

    collectionName = getCollectionName(driverIdx, collectionType)
    
    # check for driver change
    checkDriver(driverIdx)

    # check for pit enter/exit
    checkPitRoad()

    data = {}
    #if lap != state.lap and lastLaptime != state.lastLaptime:
    if lastLaptime > 0 and lastLaptime != state.lastLaptime:
        state.lap = lap
        state.lastLaptime = lastLaptime
        state.stintLap += 1

        data['Lap'] = lap
        data['StintLap'] = state.stintLap
        data['StintCount'] = state.stintCount
        data['Driver'] = ir['DriverInfo']['DriverUserID']
        data['Laptime'] = state.lastLaptime / 86400
        data['FuelUsed'] = state.fuel - ir['FuelLevel']
        state.fuel = ir['FuelLevel']
        data['FuelLevel'] = ir['FuelLevel']
        data['InPit'] = ir['OnPitRoad']
        data['TrackTemp'] = ir['TrackTemp']

        if ir['OnPitRoad']:
            state.stintCount = state.stintCount + 1
            state.stintLap = 0

        if state.enterPits:
            data['PitEnter'] = state.enterPits / 86400
            state.enterPits = 0
        else:
            data['PitEnter'] = 0

        if state.exitPits:
            data['PitExit'] = state.exitPits / 86400
            state.exitPits = 0
        else:
            data['PitExit'] = 0

        if iracingId == str(data['Driver']):
            db.collection(collectionName).document(str(lap)).set(data)

        if debug:
            logging.info(collectionName + ' lap ' + str(lap) + ': ' + json.dumps(data))

    else:
        if state.sessionId != str(ir['WeekendInfo']['SessionID']):
            state.sessionId = str(ir['WeekendInfo']['SessionID'])
                    
        if state.subSessionId != str(ir['WeekendInfo']['SubSessionID']):
            state.subSessionId = str(ir['WeekendInfo']['SubSessionID'])
            collectionName = getCollectionName(driverIdx, collectionType)
            print('SessionId: ' + collectionName)
            db.collection(collectionName).document('Info').set(getInfoDoc(sessionNum, driverIdx))

        if state.fuel == -1:
            state.fuel = ir['FuelLevel']


        
            
    # publish session time and configured telemetry values every minute
    
    # read and publish configured telemetry values every second - but only
    # if the value has changed in telemetry

def usage():
    print("usage:")
    print("teamtactics test | race")
    print("exiting ...")

def banner():
    print("=============================")
    print("|   iRacing Team Tactics    |")
    print("|           " + str(__version__) + "             |")
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
    # Project ID is determined by the GCLOUD_PROJECT environment variable
    collectionType = ''
    if len(sys.argv) > 1:
        collectionType = sys.argv[1]
    else:
        usage()
        sys.exit(1)
        
    if collectionType == 'test':
        print('Test mode')
    elif collectionType == 'race':
        print('Race mode')
    else:
        usage()
        sys.exit(1)

    try:
        # infinite loop
        while True:
            # check if we are connected to iracing
            check_iracing()
                
            # if we are, then process data
            if state.ir_connected:
                loop()

            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing update data with 60 fps
            time.sleep(1)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        print('exiting')
        time.sleep(1)
        pass