import json

from pymongo import MongoClient
from multiprocessing import Queue
from typing import Dict, Any
from datetime import datetime

from worker import WorkerHandle


class WorkerPool:
    def __init__(self, config: Dict[Any, Any]):
        self.queue = Queue()
        self.workers = []
        self.added_problems_id_list = []
        self.config = config
        count = self.config.get("workers", 2)
        self.add_worker(count)

    def add_worker(self, count):
        for _ in range(count):
            w = WorkerHandle(self.config, self.queue)
            self.workers.append(w)
            w.start()
        return "Worker(s) added!"

    def get_message_result(self, id, message):
        for worker in self.workers:
            for res_id in worker.results:
                if id == res_id:
                    res = worker.results[res_id].copy()
                    del worker.results[res_id]
                    self.added_problems_id_list.remove(res_id)
                    return json.dumps({"jsonrpc": "2.0", "result": res, "id": res_id})
        return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -2, "message": "Message ID not found in results"}})

    def get_base_dump(self, id, message):
        date = message["date"]
        processor_name = message["processor_name"]
        admin_key = message.get("admin_key", "")
        if admin_key != self.config["admin_key"]:
            return {"jsonrpc": "2.0", "id": id, "error": {"code": -3, "message": "Need admin_key for process request!"}}
        client = MongoClient(self.config["processors"][processor_name]["mongo_host"],
            self.config["processors"][processor_name]["mongo_port"])
        db_messages = client[self.config["processors"][processor_name]["mongo_db_messages"]]
        collection = db_messages[date]
        data = list(collection.find({}))
        for m in data:
            del m["_id"]
        return json.dumps({"jsonrpc": "2.0", "result": data, "id": id})

    def get_user_info(self, id, message):
        if "user_name" not in message:
            return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -5, "message": "Need user_name key!"}})
        user_name = message["user_name"]
        client = MongoClient(self.config["user_info_mongo"]["mongo_host"], 
            self.config["user_info_mongo"]["mongo_port"])
        db_info = client["info"]
        collection = db_info[self.config["user_info_mongo"]["mongo_db_users"]]
        if user_name == "*":
            data = list(collection.find({}))
            for x in data:
                del x["_id"]
            return json.dumps({"jsonrpc": "2.0", "result": data, "id": id})
        else:
            data = list(collection.find({"user_name": user_name}))
            if len(data) > 0:
                data = data[0]
                del data["_id"]
                return json.dumps({"jsonrpc": "2.0", "result": data, "id": id})
            else:
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -4, "message": "No user_name in base!"}})

    def add_user_info(self, id, message):
        if "user_name" not in message:
            return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -5, "message": "Need user_name key!"}})
        if "data" not in message:
            return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -6, "message": "Need data key!"}})
        user_name = message["user_name"]
        client = MongoClient(self.config["user_info_mongo"]["mongo_host"],
            self.config["user_info_mongo"]["mongo_port"])
        db_info = client["info"]
        collection = db_info[self.config["user_info_mongo"]["mongo_db_users"]]
        data = list(collection.find({"user_name": user_name}))
        if len(data) > 0:
            data = data[0]
            res = collection.update_one({
                "_id": data["_id"]
                },
                {
                "$set": {
                    "data": message["data"]
                }
                }, upsert=False
            )
        else:
            collection.insert_one(message)
        return json.dumps({"jsonrpc": "2.0", "result": "sucess", "id": id})

    def get_courses_data(self, id, message):
        client = MongoClient(
            self.config["processors"]["get_courses_data_processor"]["mongo_host"],
            self.config["processors"]["get_courses_data_processor"]["mongo_port"])
        self.db_courses = client[self.config["processors"]["get_courses_data_processor"]["mongo_db_courses"]]
        self.db_messages = client[self.config["processors"]["get_courses_data_processor"]["mongo_db_messages"]]
        try:
            need_keys = ("mqtt_key", "user", "type", "data_key", "action")
            data_dict = {}
            if not all(k in message for k in need_keys):
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -7, "message": "Missing one of needs key!"}})
            if message["action"] != "get_data":
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -8, "message": "No supported action!"}})
            try:
                l = []
                if message["type"] == "courses":
                    ret = self.db_courses.command("listCollections")
                    print(f"DB All Info - {ret}")
                    for x in ret["cursor"]["firstBatch"]:
                        l.append(x["name"])
                elif message["type"] == "problems":
                    collection = self.db_courses[message["data_key"]]
                    ret = list(collection.find({}))
                    for x in ret:
                        l.append({str(x["problem"]): list(x["variants"].keys()), "rating": x.get(
                            "rating", 0), "task": x.get("task", "")})
                data_dict[message["type"]] = l
                print(f"Data - {data_dict}")
            except Exception as err:
                print(f"Process error: {str(err)}")
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -9, "message": str(err)}})
            return json.dumps({"jsonrpc": "2.0", "result": data_dict, "id": id})
        
        except Exception as err:
            print(f"Process error: {str(err)}")
            return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -10, "message": str(err)}})

    def clear_data(self, id, message):
        client = MongoClient(
            self.config["processors"]["get_courses_data_processor"]["mongo_host"],
            self.config["processors"]["get_courses_data_processor"]["mongo_port"])
        self.db_courses = client[self.config["processors"]["get_courses_data_processor"]["mongo_db_courses"]]
        self.db_messages = client[self.config["processors"]["get_courses_data_processor"]["mongo_db_messages"]]
        try:
            need_keys = ("mqtt_key", "user", "type", "data_key", "action")
            data_dict = {}
            if not all(k in message for k in need_keys):
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -7, "message": "Missing one of needs key!"}})
            if message["action"] != "clear_data":
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -8, "message": "No supported action!"}})
            try:
                # Удаление курса
                if message["type"] == "course":
                    print(f"Deleting course '{message['data_key']}'")
                    self.db_courses[message["data_key"]].drop()
                    data_dict[message["data_key"]] = "Droped!"
                # Удаление задач - пока не реализовано
                elif message["type"] == "problem":
                    pass
            except Exception as err:
                print(f"Process error: {str(err)}")
                return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -12, "message": str(err)}})
            return json.dumps({"jsonrpc": "2.0", "result": data_dict, "id": id})
        except Exception as err:
            print(f"Process error: {str(err)}")
            return json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -12, "message": str(err)}})

    def add_processor(self, id, message):
        msg = {"method": "add_processor", "name": message["name"]}
        s = json.dumps(msg)
        for worker in self.workers:
            worker.service_queue.put(s)
        return json.dumps({"jsonrpc": "2.0", "id": id, "result": "success"})

    def add_message(self, id, message):
        message["id"] = id
        msg = {"method": "process_message", "message": message}
        s = json.dumps(msg)
        if id not in self.added_problems_id_list:
            self.added_problems_id_list.append(id)
            self.queue.put(s)
        return json.dumps({"jsonrpc": "2.0", "id": id, "result": "success"})
