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
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')
    def on_post(self, req, resp):
        try:
            resp.body = pool.add_message(req.media)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')

class GetMessageResult():
    '''API method for show tests result'''
    def on_get(self, req, resp):
        try:
            resp.body = pool.get_message_result(json.loads(req.params['json']))
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')
    def on_post(self, req, resp):
        try:
            resp.body = pool.get_message_result(req.media)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')

class GetBaseDump():
    '''API method for get day message dump from base'''
    def on_post(self, req, resp):
        try:
            resp.body = pool.get_base_dump(req.media)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')

# Run API
api = falcon.API()
api.req_options.auto_parse_form_urlencoded = True
add_message_to_queue = AddMessageToQueue()
get_message_result = GetMessageResult()
get_base_dump = GetBaseDump()
api.add_route('/api/add_message', add_message_to_queue)
api.add_route('/api/get_message_result', get_message_result)
api.add_route('/api/get_base_dump', get_base_dump)