import json

from pymongo import MongoClient
from multiprocessing import Queue
from typing import Dict, Any

from worker import WorkerHandle


class WorkerPool:
    def __init__(self, config: Dict[Any, Any]):
        self.queue = Queue()
        self.workers = []
        self.config = config
        count = self.config.get('workers', 2)
        self.add_worker(count)

    def add_worker(self, count):
        for _ in range(count):
            w = WorkerHandle(self.config, self.queue)
            self.workers.append(w)
            w.start()
        return 'Worker(s) added!'

    def get_message_result(self, message):
        if 'id' not in message:
            return json.dumps({'error': 'Unknown message ID'})
        for worker in self.workers:
            for res_id in worker.results:
                if message['id'] == res_id:
                    res = worker.results[res_id].copy()
                    del worker.results[res_id]
                    return json.dumps(res)
        return json.dumps({'error': 'Message ID not found in results'})
    
    def get_base_dump(self, message):
        date = message["date"]
        processor_name = message["processor_name"]
        admin_key = message.get("admin_key", "")
        if admin_key != self.config["admin_key"]:
            return json.dumps({'error': 'Need admin_key for process request!'})
        client = MongoClient(self.config["processors"][processor_name]['mongo_host'], 
            self.config["processors"][processor_name]['mongo_port'])
        db_messages = client[self.config["processors"][processor_name]['mongo_db_messages']]
        collection = db_messages[date]
        data = list(collection.find({}))
        for m in data:
            del m['_id']
        return json.dumps({'data': data})
    
    def get_user_info(self, message):
        user_name = message["user_name"]
        client = MongoClient(self.config["user_info_mongo"]['mongo_host'], 
            self.config["user_info_mongo"]['mongo_port'])
        db_info = client['info']
        collection = db_info[self.config["user_info_mongo"]['mongo_db_users']]
        data = list(collection.find({"user_name": user_name}))
        if len(data) > 0:
            data = data[0]
            del data['_id']
            return json.dumps({'data': data})
        else:
            return json.dumps({'error': 'No user_name in base!'})
    
    def add_user_info(self, message):
        if "user_name" not in message:
            return json.dumps({'error': 'Need user_name key!'})
        if "data" not in message:
            return json.dumps({'error': 'Need data key!'})
        user_name = message["user_name"]
        client = MongoClient(self.config["user_info_mongo"]['mongo_host'], 
            self.config["user_info_mongo"]['mongo_port'])
        db_info = client['info']
        collection = db_info[self.config["user_info_mongo"]['mongo_db_users']]
        data = list(collection.find({"user_name": user_name}))
        if len(data) > 0:
            data = data[0]
            collection.update_one({
                "_id": data["_id"]
                },
                {
                "$set": {
                    "data": data["data"]
                }
                }, upsert=False
            )
        else:
            collection.insert_one(message)
        return json.dumps({'data': 'sucess'})

    def add_processor(self, name):
        message = {'method': 'add_processor', 'name': name}
        s = json.dumps(message)
        for worker in self.workers:
            worker.service_queue.put(s)
        return s

    def add_message(self, message):
        msg = {'method': 'process_message', 'message': message}
        s = json.dumps(msg)
        self.queue.put(s)
        return s
