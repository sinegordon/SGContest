from pymongo import MongoClient
import sys
import json
import time
import os
from datetime import datetime
from processors import BaseProcessor
import resource

class Processor(BaseProcessor):
    def __init__(self, name, config):
        super().__init__(name, config)
        client = MongoClient(config['mongo_host'], config['mongo_port'])
        self.db_courses = client[config['mongo_db_courses']]
        self.db_messages = client[config['mongo_db_messages']]

    def process(self, message, config=None):        
        if isinstance(config, dict):
            config = {**self.config, **config}
        else:
            config = self.config

        try:
            need_keys = ('id', 'mqtt_key', 'user', 'type', 'data_key', 'action')
            data_dict = {}
            if not all(k in message for k in need_keys):
                return None
            if message['action'] != 'get_data':
                return None
            try:
                l = []
                if message['type'] == 'courses':
                    ret = self.db_courses.command('listCollections')
                    print(f"DB All Info - {ret}")
                    for x in ret['cursor']['firstBatch']:
                        l.append(x['name'])
                elif message['type'] == 'problems':
                    collection = self.db_courses[message['data_key']]
                    ret = list(collection.find({}))
                    for x in ret:
                        l.append({str(x['problem']): list(x['variants'].keys()), "rating": x.get('rating', 0), "task": x.get('task', "")})
                data_dict[message["type"]] = l
                print(f"Data - {data_dict}")
            except Exception as e:
                self.log(f'Process error: {str(e)}')
                return None
            collection_date = datetime.today().strftime('%Y-%m-%d')
            # Select problem collection
            collection = self.db_messages[f'{collection_date}']
            json_data = {'message': message, 'result': data_dict}
            self.log(f'Save to MongoDB: {json_data}.')
            transaction_id = collection.insert_one(json_data).inserted_id
            self.log(f'MongoDB response: {transaction_id}.')
            del json_data['_id']
            return json_data
        except Exception as err:
            self.log(f'Process error: {str(err)}')
            return None
