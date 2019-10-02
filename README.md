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
* DriverUserID
* FuelUsed
* FuelLevel
* OnPitRoad
* TrackTemp
* SessionTimeOfDay when entering/exiting pits

In addition a stint number and lap number in stint is calculated based to the
pit entry/exit events.

With this information the teams strategy can be calculated based on near realtime data.
A client which makes use of this data is subject of another project.

## Configuration and usage

	[DEFAULT]
	
	[global]
	# Firebase access credentials. This file has to be provided
	# by the Google Firestore owner. It has to placed in the same
	# directory as teamtactics.exe
	firebase = <firestoreCedentials.json>

	# Each team member has to configure its own iRacing ID here
	iracingId = <your iRacingId>
	
	## The following options are for development/debugging only. 
	# Generates additional debug output. Comment out or set to yes/True to enable
	;debug = yes

	# Logfile to which data is written in debug mode 
	logfile = irtactics.log

	# Uncomment to start the application using a data dump file from irsdk for 
	# testing/development purposes. The dump file can be created by issuing the 
	# command 'irsdk --dump data.dmp'
	;simulate = data/monzasunset.dump

To start a test session recording:

	teamtactics.exe test
	
To start a race session recording:

	teamtactics.exe

## Data collections

All session data is gathered within a Firestore collection. For a test session the
collection name will be

	<iRacingId>@<car>#<track>
	
, for a race session

	<teamId>@<sessionId>#<subsessionId>
	
is used.

Each collection contains an 'info' document containing the track name, max. 
session laps and max. session time. Depending on the event type only one of the latter 
is relevant.
The telemetry data mentioned above is collected in one document per lap - so document
'1' contains data for race lap 1.



# Build

Follow instructions at 
https://stackoverflow.com/questions/55848884/google-cloud-firestore-distribution-doesnt-get-added-to-pyinstaller-build

Run

    pyinstaller -F teamtactics.py
