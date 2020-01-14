# Teamtactics

This application is intended to collect realtime telemetry from iRacing team
members during a team event.

## Problem

Some of the telemetry data in iRacing is delayed for all currently not driving
team members because of anti-cheat reasons.
This affects some data which is needed to calculate driving tactics, especially
- but not only - fuel data.

## Solution

If all team members are running the teamtactics client, the following telemetry
data is collected and aggregated into a Google Firestore database:

* LapCompleted
* LapLastLapTime
* Driver Customer-ID
* FuelUsed
* FuelLevel
* OnPitRoad
* TrackTemp
* PitSvFlags
* SessionTime
* PlayerCarTowTime
* PitRepairLeft
* PitOptRepairLeft
* SessionTimeOfDay when entering/exiting pits and stop/start moving in pits

In addition a stint number and lap number in stint is calculated based to the
pit entry/exit events.

With this information the team's strategy can be calculated based on near realtime data.
A client which makes use of this data is subject of another project.

## Configuration and usage

	[DEFAULT]
	
	[global]
	# Firebase access credentials. This file has to be provided
	# by the Google Firestore owner. It has to placed in the same
	# directory as teamtactics.exe
	googleAccessToken = <firestoreCedentials.json>

	# message topic at Google sub-pub hub your team uses
	messageTopic = <your teams pub/sub topic>

	# Each team member has to configure its own iRacing ID here
	iracingId = <your iRacingId>
	
	# Proxy configuration. The given URL will be used as Proxy on both http and 
	# https protocol
	;proxy = <Proxy URL>

	## The following options are for development/debugging only. 
	# Generates additional debug output. Comment out or set to yes/True to enable
	;debug = yes

	# Logfile to which data is written in debug mode 
	logfile = irtactics.log

	# Uncomment to start the application using a data dump file from irsdk for 
	# testing/development purposes. The dump file can be created by issuing the 
	# command 'irsdk --dump data.dmp'
	;simulate = data/monzasunset.dump

To start a session recording:

	teamtactics.exe
	
## Data collections

All session data is gathered within a Firestore collection. For a single session the
collection name will be

	<UserName>@<car>#<track>#<SessionNumber>
	
, for a team session

	<teamName>@<sessionId>#<subsessionId>#<sessionNumber>
	
is used.

Each collection contains an 'info' document containing the track name, team name,
client version, max. session laps and max. session time. Depending on the event 
type only one of the latter is relevant.

Each collection also maintains a 'state' document containing the stint number,
stint laps, timestamps for pit lane entry/exit and start/stop of car movement,
Towing and Repair times and the session id's. This information is used to 
synchronize the teamtactics data among all team members.

The telemetry data mentioned above is collected in one document per lap - so document
'1' contains data for race lap 1.


## Developer info
### Prerequisites
#### Python irsdk

	pip3 install pyirsdk

#### Google cloud firestore

	pip3 install --upgrade google-cloud-firestore

#### Google cloud pub-sub hub

	pip3 install --upgrade google-cloud-pubsub

### Build



Follow instructions at 
https://stackoverflow.com/questions/55848884/google-cloud-firestore-distribution-doesnt-get-added-to-pyinstaller-build

Run

    pyinstaller --clean -F teamtactics.py

## Todo
python cloudiot_mqtt_example.py --registry_id=iRacing --cloud_region=europe-west1 --device_id=FBP-Team-Orange --algorithm=RS256 --private_key_file=fbp_member_private.pem --ca_certs roots.pem --project_id=iracing-team-tactics
