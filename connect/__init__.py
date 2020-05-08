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
#__version__ = "0.5"

import logging
import sys
import requests
import time
import json

class Connector:
    postUrl = ''
    headers = {'x-teamtactics-token': 'None'}
    invalidMessageCount = 0

    def __init__(self, config):
        print('Initializing connector')
        if config.has_option('connect', 'postUrl'):
            self.postUrl = str(config['connect']['postUrl'])
    
        if self.postUrl == '':
            print('No Url configured, only logging events')
        elif self.postUrl != '':
            print('Using Url ' + self.postUrl + ' to publish events')
            if config.has_option('connect', 'clientAccessToken'):
                self.headers = { 'x-teamtactics-token': config['connect']['clientAccessToken'], 'Content-Type': 'application/json'}

        if config.has_option('global', 'logfile'):
            logging.basicConfig(filename=str(config['global']['logfile']),level=logging.INFO,format='%(asctime)s$%(message)s')

    def publish(self, jsonData):
        try:
            logging.info(jsonData)
            if self.postUrl != '' and self.invalidMessageCount < 10:
                response = requests.post(self.postUrl, data=jsonData, headers=self.headers, timeout=10.0)
                returnMessage = response.text
                if returnMessage == 'AUTHORIZATION_ERROR':
                    print('Client access token ' + self.headers['x-teamtactics-token'] + ' is not accepted.')
                    print('Please check on https://iracing-team-tactics.appspot.com/profile')
                    time.sleep(10)
                    logging.error('AUTHORIZATION_ERROR')
                    sys.exit(1)
                elif returnMessage == 'TOKEN_ERROR':
                    print('The authorization header did not reach the server, maybe proxy/firewall issue.')
                    logging.error('TOKEN_ERROR')
                    time.sleep(10)
                    sys.exit(1)
                elif returnMessage == 'VALIDATION_ERROR':
                    self.invalidMessageCount += 1
                    if self.invalidMessageCount == 10:
                        print('Reached invalid message count of 10.')
                        print('This client will not send any further messages until restarted.')
                elif returnMessage == 'UNSUPPORTED_CLIENT':
                    print('Client protocol not accepted')
                    logging.error('UNSUPPORTED_CLIENT')
                    time.sleep(10)
                    sys.exit(1)

                return returnMessage

        except Exception as ex:
            print('Unable to publish data: ' + str(ex))

    def getClientVersion(self):
        response = requests.get('https://api.github.com/repos/simracingtools/teamtactics/releases/latest')
        return response.json()

    def pingServer(self, clientId, protocolVersion, clientVersion):
        _msg = {}
        _msg['type'] = 'ping'
        _msg['version'] = protocolVersion
        _msg['sessionId'] = 'NONE'
        _msg['teamId'] = 'NONE'
        _msg['clientId'] = clientId
        _msg['payload'] = { 'clientVersion': clientVersion }

        return self.publish(json.dumps(_msg))


