import time
import uuid

import requests


class ContestApiError(Exception):
    pass


class ContestApiClient:
    def __init__(self, base_url, session=None, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def call(self, method, params, request_id=None):
        request_id = request_id or str(uuid.uuid4())
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        try:
            response = self.session.post(
                f"{self.base_url}/api/run",
                json=message,
                timeout=self.timeout,
            )
        except requests.RequestException as err:
            raise ContestApiError(f"Network error: {err}") from err
        if not response.ok:
            raise ContestApiError(f"HTTP error: {response.status_code}")
        try:
            payload = response.json()
        except ValueError as err:
            raise ContestApiError("Server returned invalid JSON") from err
        if not isinstance(payload, dict):
            raise ContestApiError("Server returned unexpected response")
        if "error" in payload:
            error = payload["error"]
            raise ContestApiError(error.get("message", "Unknown API error"))
        if "result" not in payload:
            raise ContestApiError("Server response does not contain result")
        return payload

    def get_user_info(self, user_name):
        return self.call("get_user_info", {"user_name": user_name})

    def add_user_info(self, user_name, data):
        return self.call("add_user_info", {"user_name": user_name, "data": data})

    def get_courses_data(self, user, course):
        return self.call(
            "get_courses_data",
            {
                "mqtt_key": "234",
                "user": user,
                "type": "problems",
                "data_key": course,
                "action": "get_data",
            },
        )

    def add_message(self, params, request_id=None):
        return self.call("add_message", params, request_id=request_id)

    def get_message_result(self, request_id):
        return self.call("get_message_result", {}, request_id=request_id)

    def poll_message_result(self, request_id, timeout=30, interval=1):
        started_at = time.time()
        while time.time() - started_at <= timeout:
            try:
                result = self.get_message_result(request_id)
            except ContestApiError:
                time.sleep(interval)
                continue
            if "result" in result:
                return result
            time.sleep(interval)
        raise ContestApiError("Задача не была проверена за отведенное время. Попробуйте еще раз.")
