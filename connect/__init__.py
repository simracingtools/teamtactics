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
__copyright__ = "2020, bausdorf engineering"
__date__ = "2020/01/06"
__deprecated__ = False
__email__ = "rbausdorf@gmail.com"
__license__ = "GPLv3"
__status__ = "Beta"

import logging
import sys
import requests
import time
import json


class Connector:
    post_url = ''
    headers = {'x-teamtactics-token': 'None'}
    invalid_message_count = 0

    def __init__(self, config):
        print('Initializing connector')
        if config.has_option('connect', 'postUrl'):
            self.post_url = str(config['connect']['postUrl'])

        if self.post_url == '':
            print('No Url configured, only logging events')
        elif self.post_url != '':
            print('Using Url ' + self.post_url + ' to publish events')
            if config.has_option('connect', 'clientAccessToken'):
                self.headers = {'x-teamtactics-token': config['connect']['clientAccessToken'],
                                'Content-Type': 'application/json; charset=utf-8'}

        if not config.has_option('global', 'logfile'):
            return
        logging.basicConfig(filename=str(config['global']['logfile']), level=logging.INFO,format='%(asctime)s$%(message)s')

    def publish(self, json_data):
        try:
            logging.info(json_data)
            if self.post_url != '' and self.invalid_message_count < 10:
                response = requests.post(self.post_url, data=json_data, headers=self.headers, timeout=10.0)
                return_message = response.text
                if 'AUTHORIZATION_ERROR' == return_message:
                    print('Client access token ' + self.headers['x-teamtactics-token'] + ' is not accepted.')
                    print('Please check on https://iracing-team-tactics.appspot.com/profile')
                    time.sleep(10)
                    logging.error('AUTHORIZATION_ERROR')
                    sys.exit(1)
                elif 'TOKEN_ERROR' == return_message:
                    print('The authorization header did not reach the server, maybe proxy/firewall issue.')
                    logging.error('TOKEN_ERROR')
                    time.sleep(10)
                    sys.exit(1)
                elif 'VALIDATION_ERROR' == return_message:
                    self.invalid_message_count += 1
                    if self.invalid_message_count == 10:
                        print('Reached invalid message count of 10.')
                        print('This client will not send any further messages until restarted.')
                elif 'UNSUPPORTED_CLIENT' == return_message:
                    print('Client protocol not accepted')
                    logging.error('UNSUPPORTED_CLIENT')
                    time.sleep(10)
                    sys.exit(1)

                return return_message

        except Exception as ex:
            print('Unable to publish data: ' + str(ex))

    @staticmethod
    def get_client_version():
        response = requests.get('https://api.github.com/repos/simracingtools/teamtactics/releases/latest')
        return response.json()

    def ping_server(self, client_id, protocol_version, client_version):
        msg = {'type': 'ping', 'version': protocol_version, 'sessionId': 'NONE', 'teamId': 'NONE', 'client_id': client_id,
               'payload': {'clientVersion': client_version}}

        return self.publish(json.dumps(msg))
