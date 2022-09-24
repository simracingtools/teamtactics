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

def check_session_flags(session_flags):
    flags_local = []

    if session_flags & 0x00000001:
        flags_local.append('CHECKERED')
    if session_flags & 0x00000002:
        flags_local.append('WHITE')
    if session_flags & 0x00000004:
        flags_local.append('GREEN')
    if session_flags & 0x00000008:
        flags_local.append('YELLOW')
    if session_flags & 0x00000010:
        flags_local.append('RED')
    if session_flags & 0x00000020:
        flags_local.append('BLUE')
    if session_flags & 0x00000040:
        flags_local.append('DEBRIS')
    if session_flags & 0x00000080:
        flags_local.append('CROSSED')
    if session_flags & 0x00000100:
        flags_local.append('YELLOW_WAVED')
    if session_flags & 0x00000200:
        flags_local.append('ONE_TO_GREEN')
    if session_flags & 0x00000400:
        flags_local.append('GREEN_HELD')
    if session_flags & 0x00000800:
        flags_local.append('TEN_TO_GO')
    if session_flags & 0x00001000:
        flags_local.append('FIVE_TO_GO')
    if session_flags & 0x00002000:
        flags_local.append('RANDOM_WAVED')
    if session_flags & 0x00004000:
        flags_local.append('CAUTION')
    if session_flags & 0x00008000:
        flags_local.append('CAUTION_WAVED')
    if session_flags & 0x00010000:
        flags_local.append('BLACK')
    if session_flags & 0x00020000:
        flags_local.append('DQ')
    if session_flags & 0x00040000:
        flags_local.append('SERVICEABLE')
    if session_flags & 0x00080000:
        flags_local.append('FURLED')
    if session_flags & 0x0010000:
        flags_local.append('REPAIR')
    if session_flags & 0x10000000:
        flags_local.append('START_HIDDEN')
    if session_flags & 0x20000000:
        flags_local.append('START_READY')
    if session_flags & 0x40000000:
        flags_local.append('START_SET')

    return flags_local
