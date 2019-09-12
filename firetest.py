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
        
        data['FuelLevel'] = 38
        
        for lap in range (1, 15):
            data_ref = db.collection('123445#1232324').document(str(lap))

            data['Driver'] = 229120
            data['Laptime'] = uniform(70.0, 74.0) 
            data['FuelUsed'] = uniform(2.0, 2.2)
            data['FuelLevel'] = data['FuelLevel'] - data['FuelUsed']
            
            print(data)
            data_ref.set(data)
            