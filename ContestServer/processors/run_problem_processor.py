from pymongo import MongoClient
import sys
import json
import time
import os
from datetime import datetime
from processors import BaseProcessor
import resource
from subprocess import PIPE, Popen, STDOUT, TimeoutExpired
import uuid


class Processor(BaseProcessor):
    def __init__(self, name, config):
        super().__init__(name, config)
        client = MongoClient(config['mongo_host'], config['mongo_port'])
        self.db_courses = client[config['mongo_db_courses']]
        self.db_messages = client[config['mongo_db_messages']]
        self.languages_config = config["languages"]

    def process(self, message, config=None):        
        if isinstance(config, dict):
            config = {**self.config, **config}
        else:
            config = self.config

        try:
            need_keys = ('id', 'mqtt_key', 'user', 'language', 'code', 'tests')
            if not all(k in message for k in need_keys):
                return None
            if 'action' in message:
                return None
            code = message['code']
            fname = message['user']
            tests = message['tests']
            with open(fname, 'w') as write_file:
                write_file.write(code)
            # Проверка тестов
            results = {}
            success_count = 0
            res_score = 0
            max_res_score = 0
            for test_key in tests:
                result = {'score': 0, 'test_out': '', 'test_in': ''}
                test = tests[test_key]
                test_in = test['in']
                test_out = test['out']
                test_score = test['score']
                max_time = test.get('time', 10)
                max_res_score += test_score
                run_strs = self.languages_config[message['language']]
                try:
                    for s in run_strs[:-1]:
                        run_str = s.replace("#", fname)
                        p = Popen(run_str, shell=True, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
                        outs, errs = p.communicate(input=str.encode(test_in))
                    run_str = run_strs[-1].replace("#", fname)
                    p = Popen(run_str, shell=True, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
                    outs, errs = p.communicate(input=str.encode(test_in), timeout=max_time)
                    outs = outs.decode("utf-8").rstrip()
                    print(f'Test input - {test_in}')
                    print(f'Program output - {outs}')
                    print(f'Reference output - {test_out}')
                    self.log(f'Test input - {test_in}')
                    self.log(f'Program output - {outs}')
                    self.log(f'Reference output - {test_out}')
                    result['test_out'] = outs
                    result['test_in'] = test_in
                    if test_out == outs:
                        result['score'] = test_score
                        res_score += test_score
                        success_count += 1
                except Exception as e:
                    result['test_out'] = str(e)
                    p.kill()
                    outs, errs = p.communicate()
                results[test_key] = result
            collection_date = datetime.today().strftime('%Y-%m-%d')
            # Select problem collection
            collection = self.db_messages[f'{collection_date}']
            results['success_count'] = success_count
            results['res_score'] = res_score
            results['max_res_score'] = max_res_score
            results['timestamp'] = int(time.time())
            json_data = {'message': message, 'result': results}
            self.log(f'Save to MongoDB: {json_data}.')
            transaction_id = collection.insert_one(json_data).inserted_id
            self.log(f'MongoDB response: {transaction_id}.')
            del json_data['_id']
            return results
        except Exception as err:
            self.log(f'Process error: {str(err)}')
            return None
