import os
import time
import json
import logging
from google.cloud import firestore
from datetime import datetime
from random import uniform


if __name__ == '__main__':
        os.environ['http_proxy'] = 'http://cp-proxy.dlva.directline.de:8080'
        os.environ['https_proxy'] = 'http://cp-proxy.dlva.directline.de:8080'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './iRacingTeamTacticsFBP-5071713fe4c4.json'
        print('Use Google Credential file ' + os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

        db = firestore.Client()

        data = {}
        info = {}
        
        info['Track'] = 'Watkins Glen Classic'
        info['SessionLaps'] = 'unlimited'
        info['SessionTime'] = 14400.0 / 86400
        data_ref = db.collection('123445#1232324').document('Info')
        print(info)
        data_ref.set(info)
         
        
        data['FuelLevel'] = 38
        stintLap = 0
        stintCount = 1
        for lap in range (1, 50):
            data_ref = db.collection('123445#1232324').document(str(lap))
            
            stintLap = stintLap + 1

            data['Lap'] = lap
            data['StintLap'] = stintLap
            data['StintCount'] = stintCount

            data['Driver'] = 229120
            laptime = uniform(70.0, 74.0)
            data['Laptime'] = laptime / 86400
            data['FuelUsed'] = uniform(2.0, 2.2)
            data['FuelLevel'] = data['FuelLevel'] - data['FuelUsed']
            data['InPit'] = False

            if data['FuelLevel'] < 0:
                data['Laptime'] = data['Laptime'] + (uniform(60.0, 68.0) / 86400)
                data['InPit'] = True
                data['FuelLevel'] = 38
                stintCount = stintCount + 1
                stintLap = 0
                
            
            print(data)
            data_ref.set(data)
            