from pymongo import MongoClient


class CourseRepository:
    def __init__(self, config):
        processor_config = config["processors"]["get_courses_data_processor"]
        client = MongoClient(
            processor_config["mongo_host"],
            processor_config["mongo_port"],
        )
        self.db_courses = client[processor_config["mongo_db_courses"]]
        self.db_messages = client[processor_config["mongo_db_messages"]]

    def get_courses_data(self, data_type, data_key):
        items = []
        if data_type == "courses":
            ret = self.db_courses.command("listCollections")
            print(f"DB All Info - {ret}")
            for item in ret["cursor"]["firstBatch"]:
                items.append(item["name"])
        elif data_type == "problems":
            collection = self.db_courses[data_key]
            ret = list(collection.find({}))
            for item in ret:
                items.append(
                    {
                        str(item["problem"]): list(item["variants"].keys()),
                        "rating": item.get("rating", 0),
                        "task": item.get("task", ""),
                    }
                )
        result = {data_type: items}
        print(f"Data - {result}")
        return result

    def create_course(self, course_name):
        if not course_name:
            raise ValueError("Need course name for creating course")
        existing_names = self.db_courses.list_collection_names()
        if course_name in existing_names:
            return {course_name: "Already exists"}
        self.db_courses.create_collection(course_name)
        return {course_name: "Created!"}

    def clear_data(self, data_type, data_key, problem_number=None):
        data = {}
        if data_type == "course":
            print(f"Deleting course '{data_key}'")
            self.db_courses[data_key].drop()
            data[data_key] = "Droped!"
        elif data_type == "problem":
            if problem_number is None:
                raise ValueError("Need problem number for deleting problem")
            print(f"Deleting problem '{problem_number}' from course '{data_key}'")
            collection = self.db_courses[data_key]
            result = collection.delete_one({"problem": int(problem_number)})
            data[str(problem_number)] = "Droped!" if result.deleted_count else "Not found"
        return data
