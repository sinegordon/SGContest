import json
from pathlib import Path
from typing import Iterable, Optional

import falcon

from pool import WorkerPool


SUPPORTED_METHODS = (
    "add_message",
    "get_message_result",
    "get_courses_data",
    "add_user_info",
    "get_user_info",
    "get_base_dump",
    "clear_data",
    "add_processor",
    "create_course",
)


DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")


def create_pool(config_path: Optional[str] = None) -> WorkerPool:
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    with open(config_path) as config_file:
        config = json.load(config_file)
    return WorkerPool(config)


class Run:
    """JSON-RPC endpoint for contest operations."""

    def __init__(self, pool: WorkerPool, allowed_methods: Optional[Iterable[str]] = None):
        self.pool = pool
        self.allowed_methods = set(allowed_methods or SUPPORTED_METHODS)

    def _error_response(self, request_id, code, message):
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": code, "message": message},
            }
        )

    def on_post(self, req, resp):
        request_id = None
        try:
            resp.status = falcon.HTTP_200
            message = req.media
            if "id" not in message:
                resp.text = self._error_response(None, -1, "Unknown message ID")
                return
            request_id = message["id"]
            if "params" not in message:
                resp.text = self._error_response(request_id, -11, "Unknown message params!")
                return
            params = message["params"]
            if "method" not in message:
                resp.text = self._error_response(request_id, -21, "Unknown message method!")
                return
            method = message["method"]
            if method not in self.allowed_methods or not hasattr(self.pool, method):
                resp.text = self._error_response(request_id, -21, "Unknown message method!")
                return
            resp.text = getattr(self.pool, method)(request_id, params)
        except Exception as err:
            resp.text = self._error_response(request_id, -31, str(err))
            resp.status = falcon.HTTP_500
            print(f"App error: {str(err)}")


def create_api(pool: Optional[WorkerPool] = None, config_path: Optional[str] = None) -> falcon.API:
    api = falcon.API()
    api.req_options.auto_parse_form_urlencoded = True
    api.add_route("/api/run", Run(pool or create_pool(config_path)))
    return api


api = create_api() if DEFAULT_CONFIG_PATH.exists() else None
