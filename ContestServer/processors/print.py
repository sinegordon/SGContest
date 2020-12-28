from processors import BaseProcessor


class Processor(BaseProcessor):
    def __init__(self, name, config):
        super().__init__(name, config)

    def process(self, data, config=None):
        print('Data to be processed: {}'.format(data))
