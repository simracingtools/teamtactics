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

class Connector:
    postUrl = ''
    headers = {'x-teamtactics-token': 'None'}
    
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
            if self.postUrl != '':
                response = requests.post(self.postUrl, data=jsonData, headers=self.headers, timeout=10.0)
                return response

        except Exception as ex:
            print('Unable to publish data: ' + str(ex))

