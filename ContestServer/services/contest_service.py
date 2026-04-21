from repositories import CourseRepository, DumpRepository, UserRepository


class ContestService:
    def __init__(self, config, worker_manager):
        self.config = config
        self.worker_manager = worker_manager
        self.course_repository = CourseRepository(config)
        self.dump_repository = DumpRepository(config)
        self.user_repository = UserRepository(config)

    def get_message_result(self, request_id):
        return self.worker_manager.get_message_result(request_id)

    def get_base_dump(self, processor_name, date):
        return self.dump_repository.get_base_dump(processor_name, date)

    def get_user_info(self, user_name):
        return self.user_repository.get_user_info(user_name)

    def add_user_info(self, message):
        self.user_repository.add_user_info(message)

    def get_courses_data(self, data_type, data_key):
        return self.course_repository.get_courses_data(data_type, data_key)

    def create_course(self, course_name):
        return self.course_repository.create_course(course_name)

    def clear_data(self, data_type, data_key, problem_number=None):
        return self.course_repository.clear_data(data_type, data_key, problem_number)

    def add_processor(self, name):
        self.worker_manager.add_processor(name)

    def add_message(self, request_id, message):
        self.worker_manager.add_message(request_id, message)
