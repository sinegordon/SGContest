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
            need_keys = ('id', 'mqtt_key', 'user', 'type', 'course', 'problem', 'variant', 'tests', "action")
            if not all(k in message for k in need_keys):
                return None
            if message['action'] != 'add_problem':
                return None
            pr = int(message['problem'])
            var = message['variant']
            problem_dict = {}
            try:
                collection = self.db_courses[message["course"]]
                problem_config = list(collection.find({'problem': pr}))
                # Обновление или новая задача
                insert_key = False;
                if len(problem_config) == 0:
                    problem_dict = {}
                    insert_key = True        
                else:
                    problem_dict = problem_config[0]
                # Обновляем или вставляем условие задачи
                if "task" in message:
                    problem_dict["task"] = message["task"]
                elif "task" not in problem_dict:
                    problem_dict["task"] = "No task"                    
                if not insert_key:
                    problem_dict["variants"][var] = message["tests"]
                    collection.update_one({
                        "_id": problem_dict["_id"]
                        },
                        {
                        "$set": {
                            "task": problem_dict["task"],
                            "variants": problem_dict["variants"]
                        }
                        }, upsert=False)
                else:
                    problem_dict["problem"] = pr
                    problem_dict["type"] = message["type"]
                    problem_dict["rating"] = message["rating"]
                    problem_dict["variants"] = {}
                    problem_dict["variants"][var] = message["tests"]
                    transaction_id = collection.insert_one(problem_dict).inserted_id
                    self.log(f'MongoDB response: {transaction_id}.')
            except Exception as e:
                self.log(f'Process error: {str(e)}')
                return None
            collection_date = datetime.today().strftime('%Y-%m-%d')
            # Select problem collection
            collection = self.db_messages[f'{collection_date}']
            del problem_dict["_id"]
            json_data = {'message': message, 'result': problem_dict}
            self.log(f'Save to MongoDB: {json_data}.')
            transaction_id = collection.insert_one(json_data).inserted_id
            self.log(f'MongoDB response: {transaction_id}.')
            del json_data['_id']
            return problem_dict
        except Exception as err:
            self.log(f'Process error: {str(err)}')
            return None
