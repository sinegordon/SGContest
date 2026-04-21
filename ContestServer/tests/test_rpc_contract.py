import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
import types


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "falcon" not in sys.modules:
    sys.modules["falcon"] = types.SimpleNamespace(
        API=lambda: SimpleNamespace(
            req_options=SimpleNamespace(auto_parse_form_urlencoded=False),
            add_route=lambda *args, **kwargs: None,
        ),
        HTTP_200="200 OK",
        HTTP_500="500 Internal Server Error",
    )

if "pool" not in sys.modules:
    class DummyWorkerPool:
        def __init__(self, config):
            self.config = config

    sys.modules["pool"] = types.SimpleNamespace(WorkerPool=DummyWorkerPool)

from app import Run, SUPPORTED_METHODS  # noqa: E402


class StubPool:
    def __init__(self):
        self.calls = []

    def _response(self, request_id, method, params):
        self.calls.append((method, request_id, params))
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"method": method, "params": params},
            }
        )

    def add_message(self, request_id, params):
        return self._response(request_id, "add_message", params)

    def get_message_result(self, request_id, params):
        return self._response(request_id, "get_message_result", params)

    def get_courses_data(self, request_id, params):
        return self._response(request_id, "get_courses_data", params)

    def add_user_info(self, request_id, params):
        return self._response(request_id, "add_user_info", params)

    def get_user_info(self, request_id, params):
        return self._response(request_id, "get_user_info", params)

    def get_base_dump(self, request_id, params):
        return self._response(request_id, "get_base_dump", params)

    def clear_data(self, request_id, params):
        return self._response(request_id, "clear_data", params)

    def add_processor(self, request_id, params):
        return self._response(request_id, "add_processor", params)

    def create_course(self, request_id, params):
        return self._response(request_id, "create_course", params)


class FailingPool:
    def add_message(self, request_id, params):
        raise RuntimeError("boom")


class RunResourceTests(unittest.TestCase):
    def call_resource(self, resource, payload):
        req = SimpleNamespace(media=payload)
        resp = SimpleNamespace(status=None, text=None)
        resource.on_post(req, resp)
        return resp

    def test_supported_methods_contract_is_explicit(self):
        self.assertEqual(
            set(SUPPORTED_METHODS),
            {
                "add_message",
                "get_message_result",
                "get_courses_data",
                "add_user_info",
                "get_user_info",
                "get_base_dump",
                "clear_data",
                "add_processor",
                "create_course",
            },
        )

    def test_add_message_smoke(self):
        pool = StubPool()
        resource = Run(pool)
        params = {"user": "alice", "action": "get_data"}
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "1", "method": "add_message", "params": params},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(json.loads(resp.text)["result"]["method"], "add_message")
        self.assertEqual(pool.calls, [("add_message", "1", params)])

    def test_get_message_result_smoke(self):
        pool = StubPool()
        resource = Run(pool)
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "2", "method": "get_message_result", "params": {}},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(json.loads(resp.text)["result"]["method"], "get_message_result")

    def test_get_courses_data_smoke(self):
        pool = StubPool()
        resource = Run(pool)
        params = {
            "mqtt_key": "234",
            "user": "alice",
            "type": "courses",
            "data_key": "",
            "action": "get_data",
        }
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "3", "method": "get_courses_data", "params": params},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(json.loads(resp.text)["result"]["method"], "get_courses_data")

    def test_add_user_info_smoke(self):
        pool = StubPool()
        resource = Run(pool)
        params = {"user_name": "alice", "data": {"score": 10}}
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "4", "method": "add_user_info", "params": params},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(json.loads(resp.text)["result"]["method"], "add_user_info")

    def test_create_course_smoke(self):
        pool = StubPool()
        resource = Run(pool)
        params = {"course": "python"}
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "4c", "method": "create_course", "params": params},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(json.loads(resp.text)["result"]["method"], "create_course")

    def test_get_user_info_smoke(self):
        pool = StubPool()
        resource = Run(pool)
        params = {"user_name": "alice"}
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "5", "method": "get_user_info", "params": params},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(json.loads(resp.text)["result"]["method"], "get_user_info")

    def test_missing_id_returns_rpc_error(self):
        pool = StubPool()
        resource = Run(pool)
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "method": "add_message", "params": {}},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(
            json.loads(resp.text),
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -1, "message": "Unknown message ID"},
            },
        )

    def test_missing_params_returns_rpc_error(self):
        pool = StubPool()
        resource = Run(pool)
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "6", "method": "add_message"},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(
            json.loads(resp.text),
            {
                "jsonrpc": "2.0",
                "id": "6",
                "error": {"code": -11, "message": "Unknown message params!"},
            },
        )

    def test_missing_method_returns_rpc_error(self):
        pool = StubPool()
        resource = Run(pool)
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "7", "params": {}},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(
            json.loads(resp.text),
            {
                "jsonrpc": "2.0",
                "id": "7",
                "error": {"code": -21, "message": "Unknown message method!"},
            },
        )

    def test_unknown_method_returns_rpc_error(self):
        pool = StubPool()
        resource = Run(pool)
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "8", "method": "unknown", "params": {}},
        )

        self.assertEqual(resp.status, "200 OK")
        self.assertEqual(
            json.loads(resp.text),
            {
                "jsonrpc": "2.0",
                "id": "8",
                "error": {"code": -21, "message": "Unknown message method!"},
            },
        )

    def test_pool_exceptions_return_http_500(self):
        resource = Run(FailingPool(), allowed_methods=("add_message",))
        resp = self.call_resource(
            resource,
            {"jsonrpc": "2.0", "id": "9", "method": "add_message", "params": {}},
        )

        self.assertEqual(resp.status, "500 Internal Server Error")
        self.assertEqual(
            json.loads(resp.text),
            {
                "jsonrpc": "2.0",
                "id": "9",
                "error": {"code": -31, "message": "boom"},
            },
        )


if __name__ == "__main__":
    unittest.main()
