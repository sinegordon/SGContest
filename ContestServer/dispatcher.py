from functools import wraps

class DispatchError(Exception):
    pass

class Dispatcher:
    def is_dispatchable(self, method):
        return False

    def dispatch(self, method, *args, **kwargs):
        if hasattr(self, method) and self.is_dispatchable(method):
            return getattr(self, method)(*args, **kwargs)
        raise DispatchError(f'Method {method} is not dispatchable')
