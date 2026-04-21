import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "services" not in sys.modules:
    class DummyWorkerManager:
        def __init__(self, config):
            self.config = config

        def add_worker(self, count):
            return "Worker(s) added!"

    class DummyContestService:
        def __init__(self, config, worker_manager):
            self.config = config
            self.worker_manager = worker_manager

        def get_message_result(self, request_id):
            return None, None

        def get_base_dump(self, processor_name, date):
            return []

        def get_user_info(self, user_name):
            return None

        def add_user_info(self, message):
            return None

        def get_courses_data(self, data_type, data_key):
            return {}

        def create_course(self, course_name):
            return {}

        def clear_data(self, data_type, data_key):
            return {}

        def add_processor(self, name):
            return None

        def add_message(self, request_id, message):
            return None

    sys.modules["services"] = types.SimpleNamespace(
        ContestService=DummyContestService,
        WorkerManager=DummyWorkerManager,
    )

from pool import WorkerPool  # noqa: E402


class FakeService:
    def __init__(self):
        self.calls = []
        self.message_result = (None, None)
        self.base_dump = [{"x": 1}]
        self.user_info = {"user_name": "alice"}
        self.courses_data = {"courses": ["test"]}
        self.created_course = {"python": "Created!"}
        self.cleared_data = {"course": "Droped!"}

    def get_message_result(self, request_id):
        self.calls.append(("get_message_result", request_id))
        return self.message_result

    def get_base_dump(self, processor_name, date):
        self.calls.append(("get_base_dump", processor_name, date))
        return self.base_dump

    def get_user_info(self, user_name):
        self.calls.append(("get_user_info", user_name))
        return self.user_info

    def add_user_info(self, message):
        self.calls.append(("add_user_info", message))

    def get_courses_data(self, data_type, data_key):
        self.calls.append(("get_courses_data", data_type, data_key))
        return self.courses_data

    def clear_data(self, data_type, data_key, problem_number=None):
        self.calls.append(("clear_data", data_type, data_key, problem_number))
        return self.cleared_data

    def create_course(self, course_name):
        self.calls.append(("create_course", course_name))
        return self.created_course

    def add_processor(self, name):
        self.calls.append(("add_processor", name))

    def add_message(self, request_id, message):
        self.calls.append(("add_message", request_id, message.copy()))


class WorkerPoolRefactorTests(unittest.TestCase):
    def make_pool(self):
        pool = WorkerPool.__new__(WorkerPool)
        pool.config = {"admin_key": "secret"}
        pool.worker_manager = SimpleNamespace(add_worker=lambda count: "Worker(s) added!")
        pool.service = FakeService()
        return pool

    def test_get_message_result_uses_service(self):
        pool = self.make_pool()
        pool.service.message_result = ({"done": True}, "abc")

        resp = pool.get_message_result("abc", {})

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": {"done": True}, "id": "abc"},
        )
        self.assertEqual(pool.service.calls[0], ("get_message_result", "abc"))

    def test_get_message_result_not_found(self):
        pool = self.make_pool()

        resp = pool.get_message_result("abc", {})

        self.assertEqual(
            json.loads(resp),
            {
                "jsonrpc": "2.0",
                "id": "abc",
                "error": {"code": -2, "message": "Message ID not found in results"},
            },
        )

    def test_get_base_dump_checks_admin_key(self):
        pool = self.make_pool()

        resp = pool.get_base_dump("1", {"date": "2024-01-01", "processor_name": "equal"})

        self.assertEqual(
            json.loads(resp),
            {
                "jsonrpc": "2.0",
                "id": "1",
                "error": {"code": -3, "message": "Need admin_key for process request!"},
            },
        )

    def test_get_base_dump_uses_service(self):
        pool = self.make_pool()

        resp = pool.get_base_dump(
            "1",
            {"date": "2024-01-01", "processor_name": "equal", "admin_key": "secret"},
        )

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": [{"x": 1}], "id": "1"},
        )

    def test_get_user_info_validation(self):
        pool = self.make_pool()

        resp = pool.get_user_info("1", {})

        self.assertEqual(
            json.loads(resp),
            {
                "jsonrpc": "2.0",
                "id": "1",
                "error": {"code": -5, "message": "Need user_name key!"},
            },
        )

    def test_get_user_info_not_found(self):
        pool = self.make_pool()
        pool.service.user_info = None

        resp = pool.get_user_info("1", {"user_name": "bob"})

        self.assertEqual(
            json.loads(resp),
            {
                "jsonrpc": "2.0",
                "id": "1",
                "error": {"code": -4, "message": "No user_name in base!"},
            },
        )

    def test_add_user_info_success(self):
        pool = self.make_pool()

        resp = pool.add_user_info("1", {"user_name": "alice", "data": {"score": 1}})

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": "sucess", "id": "1"},
        )
        self.assertEqual(pool.service.calls[0][0], "add_user_info")

    def test_get_courses_data_success(self):
        pool = self.make_pool()

        resp = pool.get_courses_data(
            "1",
            {
                "mqtt_key": "1",
                "user": "alice",
                "type": "courses",
                "data_key": "",
                "action": "get_data",
            },
        )

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": {"courses": ["test"]}, "id": "1"},
        )

    def test_clear_data_success(self):
        pool = self.make_pool()

        resp = pool.clear_data(
            "1",
            {
                "mqtt_key": "1",
                "user": "alice",
                "type": "course",
                "data_key": "python",
                "action": "clear_data",
            },
        )

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": {"course": "Droped!"}, "id": "1"},
        )

    def test_create_course_success(self):
        pool = self.make_pool()

        resp = pool.create_course("1", {"course": "python"})

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": {"python": "Created!"}, "id": "1"},
        )
        self.assertEqual(pool.service.calls[0], ("create_course", "python"))

    def test_create_course_validation(self):
        pool = self.make_pool()

        resp = pool.create_course("1", {})

        self.assertEqual(
            json.loads(resp),
            {
                "jsonrpc": "2.0",
                "id": "1",
                "error": {"code": -13, "message": "Need course key!"},
            },
        )

    def test_clear_problem_success(self):
        pool = self.make_pool()

        resp = pool.clear_data(
            "1",
            {
                "mqtt_key": "1",
                "user": "alice",
                "type": "problem",
                "data_key": "python",
                "problem": 7,
                "action": "clear_data",
            },
        )

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": {"course": "Droped!"}, "id": "1"},
        )
        self.assertEqual(pool.service.calls[0], ("clear_data", "problem", "python", 7))

    def test_add_processor_success(self):
        pool = self.make_pool()

        resp = pool.add_processor("1", {"name": "equal_processor"})

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": "success", "id": "1"},
        )

    def test_add_message_success(self):
        pool = self.make_pool()
        message = {"user": "alice"}

        resp = pool.add_message("1", message)

        self.assertEqual(
            json.loads(resp),
            {"jsonrpc": "2.0", "result": "success", "id": "1"},
        )
        self.assertEqual(pool.service.calls[0], ("add_message", "1", {"user": "alice"}))


if __name__ == "__main__":
    unittest.main()
