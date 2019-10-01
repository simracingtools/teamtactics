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
* SessionTimeOfDay when entering/exiting pits

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

# Build

Follow instructions at 
https://stackoverflow.com/questions/55848884/google-cloud-firestore-distribution-doesnt-get-added-to-pyinstaller-build

Run

    pyinstaller -F teamtactics.py
