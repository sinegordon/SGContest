from multiprocessing import current_process

class BaseProcessor:
    def __init__(self, name, config):
        self.name = name
        if 'service' in config:
            self.name = config['service'] + '.' + name
        self.pid = current_process().pid
        self.config = config
    
    def process(self, message, config=None):
        pass
    
    def log_fmt(self, message):
        s = f'PID = {self.pid}. {message}'
        return s

    def log(self, message):
        print(self.log_fmt(message))
