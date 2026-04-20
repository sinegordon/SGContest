from pymongo import MongoClient


class DumpRepository:
    def __init__(self, config):
        self.config = config

    def get_base_dump(self, processor_name, date):
        processor_config = self.config["processors"][processor_name]
        client = MongoClient(
            processor_config["mongo_host"],
            processor_config["mongo_port"],
        )
        db_messages = client[processor_config["mongo_db_messages"]]
        collection = db_messages[date]
        data = list(collection.find({}))
        for item in data:
            del item["_id"]
        return data
