import falcon
import json

from pool import WorkerPool

pool = WorkerPool(json.load(open('./config.json')))

class Run():
    '''API method for run function'''

    def on_post(self, req, resp):
        try:
            resp.status = falcon.HTTP_200
            message = req.media
            if "id" not in message:
                resp.body = json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -1, "message": "Unknown message ID"}})
                return
            id = message["id"]
            if "params" not in message:
                resp.body = json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -11, "message": "Unknown message params!"}})
                return
            params = message["params"]
            if "method" not in message:
                resp.body = json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -21, "message": "Unknown message method!"}})
                return
            method = message["method"]
            resp.body = getattr(pool, method)(id, params)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.body = json.dumps({"jsonrpc": "2.0", "id": id, "error": {"code": -31, "message": str(err)}})
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')


# Run API
api = falcon.API()
api.req_options.auto_parse_form_urlencoded = True
run = Run()
api.add_route('/api/run', run)