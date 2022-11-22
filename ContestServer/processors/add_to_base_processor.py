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
            need_keys = ('id', 'mqtt_key', 'user', 'type', 'course', 'problem', 'variant', 'tests')
            if not all(k in message for k in need_keys):
                return None
            if message['id'] != 'add_problem':
                return None
            pr = int(message['problem'])
            var = message['variant']
            problem_dict = {}
            try:
                collection = self.db_courses[message["course"]]
                print(f"Course - {collection}")
                problem_config = list(collection.find({'problem': pr}))
                print(f"Problem - {problem_config}")
                insert_key = False;
                if len(problem_config) == 0:
                    problem_dict = {}
                    insert_key = True        
                else:
                    problem_dict = problem_config[0]
                if not insert_key:
                    problem_dict["variants"][var] = message["tests"]
                    collection.update_one({
                        "_id": problem_dict["_id"]
                        },
                        {
                        "$set": {
                            "variants": problem_dict["variants"]
                        }
                        }, upsert=False)
                else:
                    problem_dict["problem"] = pr
                    problem_dict["type"] = message["type"]
                    problem_dict["variants"] = {}
                    problem_dict["variants"][var] = message["tests"]
                    transaction_id = collection.insert_one(problem_dict).inserted_id
                    self.log(f'MongoDB response: {transaction_id}.')
            except Exception as e:
                self.log(f'Process error: {str(e)}')
                return None
            return problem_dict
        except Exception as err:
            self.log(f'Process error: {str(err)}')
            return None
