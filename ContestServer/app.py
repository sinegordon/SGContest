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


class GetUserInfo():
    '''API method for get user info from base'''
    def on_post(self, req, resp):
        try:
            resp.body = pool.get_user_info(req.media)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')


class AddUserInfo():
    '''API method for add user info to base'''
    def on_post(self, req, resp):
        try:
            resp.body = pool.add_user_info(req.media)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')


class GetCoursesData():
    '''API method for get data of courses and problems collections'''

    def on_post(self, req, resp):
        try:
            resp.body = pool.get_courses_data(req.media)
            resp.status = falcon.HTTP_200
        except Exception as err:
            resp.status = falcon.HTTP_500
            print(f'App error: {str(err)}')

class ClearData():
    '''API method for clear data in collections'''

    def on_post(self, req, resp):
        try:
            resp.body = pool.clear_data(req.media)
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
add_user_info = AddUserInfo()
get_user_info = GetUserInfo()
get_courses_data = GetCoursesData()
clear_data = ClearData()
api.add_route('/api/add_message', add_message_to_queue)
api.add_route('/api/get_message_result', get_message_result)
api.add_route('/api/get_base_dump', get_base_dump)
api.add_route('/api/get_user_info', get_user_info)
api.add_route('/api/add_user_info', add_user_info)
api.add_route('/api/get_courses_data', get_courses_data)
api.add_route('/api/clear_data', clear_data)
