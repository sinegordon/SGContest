from typing import Any, Dict

from rpc import rpc_error, rpc_result
from services import ContestService, WorkerManager


class WorkerPool:
    def __init__(self, config: Dict[Any, Any]):
        self.config = config
        self.worker_manager = WorkerManager(config)
        self.service = ContestService(config, self.worker_manager)
        count = self.config.get("workers", 2)
        self.add_worker(count)

    def add_worker(self, count):
        return self.worker_manager.add_worker(count)

    def get_message_result(self, request_id, message):
        result, result_id = self.service.get_message_result(request_id)
        if result is not None:
            return rpc_result(result_id, result)
        return rpc_error(request_id, -2, "Message ID not found in results")

    def get_base_dump(self, request_id, message):
        date = message["date"]
        processor_name = message["processor_name"]
        admin_key = message.get("admin_key", "")
        if admin_key != self.config["admin_key"]:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -3, "message": "Need admin_key for process request!"},
            }
        data = self.service.get_base_dump(processor_name, date)
        return rpc_result(request_id, data)

    def get_user_info(self, request_id, message):
        if "user_name" not in message:
            return rpc_error(request_id, -5, "Need user_name key!")

        data = self.service.get_user_info(message["user_name"])
        if data is None:
            return rpc_error(request_id, -4, "No user_name in base!")
        return rpc_result(request_id, data)

    def add_user_info(self, request_id, message):
        if "user_name" not in message:
            return rpc_error(request_id, -5, "Need user_name key!")
        if "data" not in message:
            return rpc_error(request_id, -6, "Need data key!")

        self.service.add_user_info(message)
        return rpc_result(request_id, "sucess")

    def get_courses_data(self, request_id, message):
        try:
            need_keys = ("mqtt_key", "user", "type", "data_key", "action")
            if not all(key in message for key in need_keys):
                return rpc_error(request_id, -7, "Missing one of needs key!")
            if message["action"] != "get_data":
                return rpc_error(request_id, -8, "No supported action!")
            try:
                data = self.service.get_courses_data(message["type"], message["data_key"])
            except Exception as err:
                print(f"Process error: {str(err)}")
                return rpc_error(request_id, -9, str(err))
            return rpc_result(request_id, data)
        except Exception as err:
            print(f"Process error: {str(err)}")
            return rpc_error(request_id, -10, str(err))

    def clear_data(self, request_id, message):
        try:
            need_keys = ("mqtt_key", "user", "type", "data_key", "action")
            if not all(key in message for key in need_keys):
                return rpc_error(request_id, -7, "Missing one of needs key!")
            if message["action"] != "clear_data":
                return rpc_error(request_id, -8, "No supported action!")
            try:
                data = self.service.clear_data(
                    message["type"],
                    message["data_key"],
                    message.get("problem"),
                )
            except Exception as err:
                print(f"Process error: {str(err)}")
                return rpc_error(request_id, -12, str(err))
            return rpc_result(request_id, data)
        except Exception as err:
            print(f"Process error: {str(err)}")
            return rpc_error(request_id, -12, str(err))

    def add_processor(self, request_id, message):
        self.service.add_processor(message["name"])
        return rpc_result(request_id, "success")

    def add_message(self, request_id, message):
        self.service.add_message(request_id, message)
        return rpc_result(request_id, "success")
