import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api import ContestApiClient, ContestApiError  # noqa: E402


class FakeResponse:
    def __init__(self, ok=True, status_code=200, payload=None, json_error=None):
        self.ok = ok
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append((url, json, timeout))
        return self.response


class ApiTests(unittest.TestCase):
    def test_call_success(self):
        session = FakeSession(FakeResponse(payload={"jsonrpc": "2.0", "result": {"x": 1}, "id": "1"}))
        client = ContestApiClient("http://example.com", session=session, timeout=5)

        response = client.call("get_user_info", {"user_name": "alice"}, request_id="1")

        self.assertEqual(response["result"], {"x": 1})
        self.assertEqual(session.calls[0][0], "http://example.com/api/run")
        self.assertEqual(session.calls[0][2], 5)

    def test_call_http_error(self):
        client = ContestApiClient(
            "http://example.com",
            session=FakeSession(FakeResponse(ok=False, status_code=500)),
        )

        with self.assertRaises(ContestApiError) as ctx:
            client.call("get_user_info", {"user_name": "alice"}, request_id="1")

        self.assertIn("HTTP error: 500", str(ctx.exception))

    def test_call_invalid_json(self):
        client = ContestApiClient(
            "http://example.com",
            session=FakeSession(FakeResponse(json_error=ValueError("bad json"))),
        )

        with self.assertRaises(ContestApiError) as ctx:
            client.call("get_user_info", {"user_name": "alice"}, request_id="1")

        self.assertEqual(str(ctx.exception), "Server returned invalid JSON")

    def test_call_unexpected_payload(self):
        client = ContestApiClient(
            "http://example.com",
            session=FakeSession(FakeResponse(payload=["not", "a", "dict"])),
        )

        with self.assertRaises(ContestApiError) as ctx:
            client.call("get_user_info", {"user_name": "alice"}, request_id="1")

        self.assertEqual(str(ctx.exception), "Server returned unexpected response")

    def test_call_rpc_error(self):
        client = ContestApiClient(
            "http://example.com",
            session=FakeSession(FakeResponse(payload={"error": {"message": "Oops"}})),
        )

        with self.assertRaises(ContestApiError) as ctx:
            client.call("get_user_info", {"user_name": "alice"}, request_id="1")

        self.assertEqual(str(ctx.exception), "Oops")

    def test_call_missing_result(self):
        client = ContestApiClient(
            "http://example.com",
            session=FakeSession(FakeResponse(payload={"jsonrpc": "2.0", "id": "1"})),
        )

        with self.assertRaises(ContestApiError) as ctx:
            client.call("get_user_info", {"user_name": "alice"}, request_id="1")

        self.assertEqual(str(ctx.exception), "Server response does not contain result")


if __name__ == "__main__":
    unittest.main()
