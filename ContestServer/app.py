import falcon
import json

from pool import WorkerPool

pool = WorkerPool(json.load(open('./config.json')))

class AddMessageToQueue():
    '''API method for transaction data processing'''
    def on_get(self, req, resp):
        try:
            resp.body = pool.add_message(json.loads(req.params['json']))
            resp.status = falcon.HTTP_200
        except:
            resp.status = falcon.HTTP_500
    def on_post(self, req, resp):
        try:
            resp.body = pool.add_message(req.media)
            resp.status = falcon.HTTP_200
        except:
            resp.status = falcon.HTTP_500

class GetMessageResult():
    '''API method for show tests result'''
    def on_get(self, req, resp):
        try:
            resp.body = pool.get_message_result(json.loads(req.params['json']))
            resp.status = falcon.HTTP_200
        except:
            resp.status = falcon.HTTP_500
    def on_post(self, req, resp):
        try:
            resp.body = pool.get_message_result(req.media)
            resp.status = falcon.HTTP_200
        except:
            resp.status = falcon.HTTP_500

# Run API
api = falcon.API()
api.req_options.auto_parse_form_urlencoded = True
add_message_to_queue = AddMessageToQueue()
get_message_result = GetMessageResult()
api.add_route('/api/add_message', add_message_to_queue)
api.add_route('/api/get_message_result', get_message_result)