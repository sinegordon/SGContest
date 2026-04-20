from pymongo import MongoClient


class UserRepository:
    def __init__(self, config):
        mongo_config = config["user_info_mongo"]
        client = MongoClient(
            mongo_config["mongo_host"],
            mongo_config["mongo_port"],
        )
        db_info = client["info"]
        self.collection = db_info[mongo_config["mongo_db_users"]]

    def get_user_info(self, user_name):
        if user_name == "*":
            data = list(self.collection.find({}))
            for item in data:
                del item["_id"]
            return data

        data = list(self.collection.find({"user_name": user_name}))
        if len(data) > 0:
            user = data[0]
            del user["_id"]
            return user
        return None

    def add_user_info(self, message):
        user_name = message["user_name"]
        data = list(self.collection.find({"user_name": user_name}))
        if len(data) > 0:
            user = data[0]
            self.collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"data": message["data"]}},
                upsert=False,
            )
        else:
            self.collection.insert_one(message)
