import os
import time
import json
import logging
from google.cloud import pubsub_v1
from datetime import datetime
from random import uniform

class SyncState:
    ir_connected = False
    date_time = -1
    tick = 0
    lap = 0
    fuel = 0
    fuelPerLap = 0
    driver = 'Robert Bausdorf'

if __name__ == '__main__':
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './iracing-team-tactics-pub-sub-9d86401be6cb.json'
    print('Use Google Credential file ' + os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_name}`
    topic_path = 'projects/iracing-team-tactics/topics/driver-state'

    state = {}
    state['lap'] = 17
    state['fuel'] = 62
    state['fuelPerLap'] = 2.345
    state['driver'] = 'Robert Bausdorf'

    for n in range(1, 5):
        data = u'Message number {}'.format(n)
        # Data must be a bytestring
        data = data.encode('utf-8')
        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data=data)
        print('Published {} of message ID {}.'.format(data, future.result()))
        print(state)
        time.sleep(1)
            