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
this program. If not, see <https://www.gnu.org/licenses/>.
"""

__author__ = "Robert Bausdorf"
__contact__ = "rbausdorf@gmail.com"
__copyright__ = "2019, bausdorf engineering"
__date__ = "2019/06/01"
__deprecated__ = False
__email__ = "rbausdorf@gmail.com"
__license__ = "GPLv3"
__status__ = "Beta"
__version__ = "2.09"

import sys
import configparser
import irsdk
import os
import time

import connect
import iracing.IrTypes
from iracing.IrTypes import LapData
from iracing.IrTypes import SessionInfo
from iracing.IrTypes import LocalState
from iracing.IrTypes import RunData
from iracing.IrTypes import EventData
from iracing.IrTypes import TyreData


# here we check if we are connected to iRacing,
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

        if is_startup and ir.is_initialized and ir.is_connected:
            state.ir_connected = True
            state.clientId = iracingId

            print('irsdk connected')
            check_session_change()


def check_driver():
    driver_idx = ir['DriverInfo']['DriverCarIdx']
    current_driver = ir['DriverInfo']['Drivers'][driver_idx]['UserName']

    if state.runningDriverName != current_driver:
        print('Driver change: ' + current_driver)
        state.updateRunningDriver(ir)


def check_session_change():
    if state.updateSession(ir):

        state.updateRunningDriver(ir)

        if state.sessionId == '0' or ir['DriverInfo']['Drivers'][state.driverIdx]['TeamID'] == 0:
            state.sessionType = 'single'
        else:
            state.sessionType = 'team'

        collection_name = state.getCollectionName(ir)
        print('SessionType: ' + state.sessionType)
        print('SessionId  : ' + collection_name)

        # if state.itsMe(iracingId):
        session_info = SessionInfo(collection_name, ir)

        if debug:
            print(session_info.toDict())

        # Session change is announced to server even if not in car.
        # Duplicates are detected and filtered by the server
        connector.publish(session_info.sessionDataMessage(state))


# our main loop, where we retrieve data
# and do something useful with it
def loop():
    # on each tick we freeze buffer with live telemetry
    # it is optional, useful if you use vars like CarIdxXXX
    # in this way you will have consistent data from this vars inside one tick
    # because sometimes while you retrieve one CarIdxXXX variable
    # another one in next line of code can be changed
    # to the next iRacing internal tick_count
    ir.freeze_var_buffer_latest()

    state.tick += 1
    lap = ir['Lap']
    last_laptime = ir['LapLastLapTime']

    # check for driver change
    check_driver()

    # if lap > state.lap:
    # if lap > state.lap and lastLaptime != state.lastLaptime:
    if last_laptime != state.lastLaptime:
        state.lap = lap
        state.lastLaptime = last_laptime

        lapdata = LapData(state.runningDriverName, state.clientId, ir)
        state.fuel = ir['FuelLevel']

        if state.itsMe(iracingId):
            lapmsg = lapdata.lapDataMessage(state)
            connector.publish(lapmsg)
            print(lapdata.toDict())
    else:
        check_session_change()
        if state.itsMe(iracingId):
            if runData.update(ir):
                connector.publish(runData.runDataMessage(state))
            if eventData.updateEvent(state, ir):
                connector.publish(eventData.eventDataMessage(state))
            if tyreData.updateTyres(ir):
                connector.publish(tyreData.tyreDataMessage(state))
                print(tyreData.toDict())
        else:
            # every 3 ticks
            if state.tick % 3 == 0:
                connector.publish(runData.syncDataMessage(state, ir))


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

    try:
        connector = connect.Connector(config)
        lastestVersion = connector.get_client_version()
        if float(__version__) < float(lastestVersion['tag_name'][1:]):
            print('There is a newer Version available - please update to ' + lastestVersion['tag_name'])
            print(lastestVersion['assets'][0]['browser_download_url'])
        else:
            print('Version ' + lastestVersion['tag_name'] + ' is up to date')
    except Exception as ex:
        print('Unable initialize connector: ' + str(ex))
        sys.exit(1)

    if config.has_option('global', 'iracingId'):
        iracingId = config['global']['iracingId']
        if iracingId == '':
            print('option iRacingId is not set')
            sys.exit(1)

        print('iRacing ID: ' + str(iracingId))
    else:
        print('option iRacingId not configured or irtactics.ini not found')
        sys.exit(1)

    pingResponse = connector.ping_server(str(iracingId), iracing.IrTypes.__version__, __version__)
    if pingResponse != 'PING':
        print('Server does not answer ping: ' + str(pingResponse))
        time.sleep(10)
        sys.exit(1)
    else:
        print('Server reacheable and responding')

    # initializing ir and state
    ir = irsdk.IRSDK()
    state = LocalState()
    runData = RunData()
    eventData = EventData()
    tyreData = TyreData()

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
