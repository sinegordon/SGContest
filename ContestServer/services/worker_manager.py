import json

from multiprocessing import Queue

from worker import WorkerHandle


class WorkerManager:
    def __init__(self, config):
        self.config = config
        self.queue = Queue()
        self.workers = []
        self.added_problems_id_list = []

    def add_worker(self, count):
        for _ in range(count):
            worker = WorkerHandle(self.config, self.queue)
            self.workers.append(worker)
            worker.start()
        return "Worker(s) added!"

    def get_message_result(self, request_id):
        for worker in self.workers:
            for result_id in list(worker.results.keys()):
                if request_id == result_id:
                    result = worker.results[result_id].copy()
                    del worker.results[result_id]
                    if result_id in self.added_problems_id_list:
                        self.added_problems_id_list.remove(result_id)
                    return result, result_id
        return None, None

    def add_processor(self, name):
        message = json.dumps({"method": "add_processor", "name": name})
        for worker in self.workers:
            worker.service_queue.put(message)

    def add_message(self, request_id, message):
        message["id"] = request_id
        payload = json.dumps({"method": "process_message", "message": message})
        if request_id not in self.added_problems_id_list:
            self.added_problems_id_list.append(request_id)
            self.queue.put(payload)
