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

def checkSessionFlags(sessionFlags):
    _flags = []

    if sessionFlags & 0x00000001:
        _flags.append('CHECKERD')
    if sessionFlags & 0x00000002:
        _flags.append('WHITE')
    if sessionFlags & 0x00000004:
        _flags.append('GREEN')
    if sessionFlags & 0x00000008:
        _flags.append('YELLOW')
    if sessionFlags & 0x00000010:
        _flags.append('RED')
    if sessionFlags & 0x00000020:
        _flags.append('BLUE')
    if sessionFlags & 0x00000040:
        _flags.append('DEBRIS')
    if sessionFlags & 0x00000080:
        _flags.append('CROSSED')
    if sessionFlags & 0x00000100:
        _flags.append('YELLOW_WAVED')
    if sessionFlags & 0x00000200:
        _flags.append('ONE_TO_GREEN')
    if sessionFlags & 0x00000400:
        _flags.append('GREEN_HELD')
    if sessionFlags & 0x00000800:
        _flags.append('TEN_TO_GO')
    if sessionFlags & 0x00001000:
        _flags.append('FIVE_TO_GO')
    if sessionFlags & 0x00002000:
        _flags.append('RANDOM_WAVED')
    if sessionFlags & 0x00004000:
        _flags.append('CAUTION')
    if sessionFlags & 0x00008000:
        _flags.append('CAUTION_WAVED')
    if sessionFlags & 0x00010000:
        _flags.append('BLACK')
    if sessionFlags & 0x00020000:
        _flags.append('DQ')
    if sessionFlags & 0x00040000:
        _flags.append('SERVICEABLE')
    if sessionFlags & 0x00080000:
        _flags.append('FURLED')
    if sessionFlags & 0x0010000:
        _flags.append('REPAIR')
    if sessionFlags & 0x10000000:
        _flags.append('START_HIDDEN')
    if sessionFlags & 0x20000000:
        _flags.append('START_READY')
    if sessionFlags & 0x40000000:
        _flags.append('START_SET')

    return _flags