# Teamtactics

This application is intended to collect realtime telemetry from iRacing team
members during a team event.

## Problem

Some of the telemetry data in iRacing is delayed for all currently not driving
team members because of anti-cheat reasons.
This affects some data which is needed to calculate driving tactics, especially
but not only - fuel data.

## Solution

If all team members are running the teamtactics client, the following telemetry
data is collected and aggregated into a cloud server:

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
* TrackLocations
* Flags

With this information the team's strategy can be calculated based on near realtime data.
A client which makes use of this data is subject of another project.

## Configuration and usage

	[DEFAULT]
	
	[global]
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

	[connect]
	# Fill in the client access token from your TeamTactics profile at
	# https://iracing-team-tactics.appspot.com/profile
	clientAccessToken =

	# URL where the client send its messages to - usually no subject to change
	postUrl       = noFallback


To start a session recording:

	teamtactics.exe
	

## Developer info
### Prerequisites
#### Python irsdk

	pip3 install pyirsdk

### Packaging

    pyinstaller --clean --icon dist/teamtactics2.ico -F teamtactics2.py

To build setup package comile

	tt2setup.iss

using InnoSetup compiler

