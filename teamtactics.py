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

__author__ = "Robert Bausdorf"
__contact__ = "rbausdorf@gmail.com"
__copyright__ = "2019, bausdorf engineering"
#__credits__ = ["One developer", "And another one", "etc"]
__date__ = "2019/06/01"
__deprecated__ = False
__email__ =  "rbausdorf@gmail.com"
__license__ = "GPLv3"
#__maintainer__ = "developer"
__status__ = "Production"
__version__ = "0.7"

import configparser
import irsdk
import os
import time
import json
from google.cloud import firestore
from datetime import datetime

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    date_time = -1
    tick = 0
    lap = 0
    fuel = 0
    onPitRoad = -1
    sessionId = ''

# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():        
    
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset all your in State variables
        state.date_time = -1
        state.tick = 0
        state.fuel = -1
        state.lap = -1
        state.onPitRoad = -1
        state.sessionId = ''

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

            state.sessionId = str(ir['WeekendInfo']['SessionID']) + '#' + str(ir['WeekendInfo']['SubSessionID'])
            state.fuel = ir['FuelLevel']

            print('irsdk connected')
            print('SessionID    ' + state.sessionId)
            
    
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
    data = {}
    if lap != state.lap:
        state.lap = lap

        data['Driver'] = ir['DriverInfo']['DriverUserID']
        data['Laptime'] = ir['LapLastLapTime']
        data['FuelUsed'] = state.fuel - ir['FuelLevel']
        state.fuel = ir['FuelLevel']

        data['ExitPit'] = 0
        data['StopStart'] = 0
        if ir['OnPitRoad']:
            if state.onPitRoad == 0:
                state.onPitRoad = 1
                data['EnterPit'] = datetime.now()
        else:
            if state.onPitRoad == 1:
                state.onPitRoad = 0
                data['ExitPit'] = datetime.now()

        data['FuelLevel'] = ir['FuelLevel']

        if debug:
            print(json.dumps(data))

    # publish session time and configured telemetry values every minute
    
    # read and publish configured telemetry values every second - but only
    # if the value has changed in telemetry

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
    except Exception:
        print('unable to read configuration: ' + Exception.__cause__)

    # Print banner an debug output status
    banner()
    if config.has_option('global', 'debug'):
        debug = config.getboolean('global', 'debug')
    
    if debug:
        print('Debug output enabled')

    if config.has_option('global', 'firebase'):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './' + str(config['global']['firebase'])
    
    if debug:
        print('Use Google Credential file ' + os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    # Project ID is determined by the GCLOUD_PROJECT environment variable
    db = firestore.Client()
    

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