import json


def rpc_result(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "result": result, "id": request_id})


def rpc_error(request_id, code, message):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }
    )
