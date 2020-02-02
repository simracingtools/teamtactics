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
__version__ = "0.97"

import sys
import configparser
import irsdk
import os
import time
import json
import logging

from datetime import datetime
from datetime import timedelta

import connect
from iracing.IrTypes import SyncState
from iracing.IrTypes import LapData
from iracing.IrTypes import SessionInfo
from iracing.IrTypes import LocalState
from iracing.IrTypes import RunData

# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():        
    
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset all your in State variables
        state.reset()

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

            collectionName = syncState.getCollectionName(ir)
            if state.sessionType == 'single':
                print('Single session, deleting all data in collection ' + collectionName)
                connector.clearCollection(collectionName)


def checkDriver():
    currentDriver = ir['DriverInfo']['Drivers'][state.driverIdx]['UserName']

    if syncState.updateDriver(currentDriver):
        print('Driver change: ' + currentDriver)
        state.updateRunningDriver(ir)

        # sync state on self driving
        if state.itsMe(iracingId):
            collectionName = syncState.getCollectionName(ir)
            doc = connector.getDocument(collectionName, 'State')
            
            if doc is not None:
                print('Sync state on driver change')
                syncState.fromDict(doc, currentDriver)
                if debug:
                    print('State: ' + str(doc))
            else:
                print('No state in ' + collectionName)

def checkSessionChange():
    if syncState.updateSession(ir):

        state.updateRunningDriver(ir)
        connector.updatePostUrl(config, state.runningTeam)
        
        if syncState.sessionId == '0' or ir['DriverInfo']['Drivers'][state.driverIdx]['TeamID'] == 0:
            state.sessionType = 'single'
        else:
            state.sessionType = 'team'

        collectionName = syncState.getCollectionName(ir)
        print('SessionType: ' + state.sessionType)
        print('SessionId  : ' + collectionName)

        if state.itsMe(iracingId):
            sessionInfo = SessionInfo(collectionName, ir)
            
            print(sessionInfo.toDict())
            sessionData = sessionInfo.sessionDataMessage()
            
            connector.publish(sessionData)
            

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
        lastLaptime = ir['LapLastLapTime']  / 86400
    elif debug:
        print('no last laptime')

    # check for driver change
    checkDriver()

    # check for pit enter/exit
    syncState.updatePits(state, ir)
    
    collectionName = syncState.getCollectionName(ir)

    if lap > state.lap and lastLaptime != syncState.lastLaptime:
    #if lastLaptime > 0 and syncState.lastLaptime != lastLaptime:
        state.lap = lap
        syncState.updateLap(lap, lastLaptime)

        lapdata = LapData(syncState, ir)
        state.fuel = ir['FuelLevel']

        if state.itsMe(iracingId):
            if syncState.isPitopComplete():
                pitstopData = syncState.pitstopDataMessage()
                print(syncState.pitstopData())
                connector.publish(pitstopData)
                syncState.resetPitstop()
                

            lapmsg = lapdata.lapDataMessage()
            connector.publish(lapmsg)
            if debug:
                print(lapdata.toDict())

            connector.putDocument(collectionName, 'State', syncState.toDict())

    else:
        checkSessionChange()
        if state.itsMe(iracingId) and runData.update(ir):
            print(runData.toDict())
            connector.publish(runData.runDataMessage())

        doc = connector.getDocument(collectionName, 'State')
        
        if doc is not None:
            if debug:
                data = doc.to_dict()
                print('State: ' + str(data))
        else:
            if debug:
                print('No state document found - providing it')

            connector.putDocument(collectionName, 'State', syncState.toDict())
            
    # publish session time and configured telemetry values every minute
    
    # read and publish configured telemetry values every second - but only
    # if the value has changed in telemetry

def banner():
    print("=============================")
    print("|   iRacing Team Tactics    |")
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

    if config.has_option('connect', 'googleAccessToken'):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './' + str(config['connect']['googleAccessToken'])
        if debug:
            print('Use Google Credential file ' + os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

        try:
            connector = connect.Connector(config)
        except Exception as ex:
            print('Unable to connect to Google infrastructure: ' + str(ex))
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
    state = LocalState()
    syncState = SyncState()
    runData = RunData()
    # Project ID is determined by the GCLOUD_PROJECT environment variable

    while True:
        try:
        # infinite loop
        
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
            break
        except Exception as ex:
            print(str(ex))
            continue