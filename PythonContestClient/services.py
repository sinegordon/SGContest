import random
import uuid


def get_problem_number(problem_data):
    return int([key for key in problem_data.keys() if key.isnumeric()][0])


def split_problems_by_rating(problems):
    grouped = {1: [], 2: [], 3: []}
    for problem in problems:
        problem_number = [key for key in problem.keys() if key.isnumeric()][0]
        rating = problem.get("rating", 0)
        if rating in grouped:
            grouped[rating].append(problem_number)
    return grouped


def select_problem_set(problems, counts_by_rating, rng=None):
    rng = rng or random
    grouped = split_problems_by_rating(problems)
    selected_numbers = []
    for rating, count in counts_by_rating.items():
        if count <= 0:
            continue
        selected_numbers.extend(rng.sample(grouped[rating], count))
    return [problem for problem in problems if any(number in problem for number in selected_numbers)]


def format_check_result(result):
    if result["max_res_score"] == result["res_score"]:
        bad_input = ""
    else:
        bad_input = "Ошибочные результаты получены на следующих входных данных:\n"
        index = 1
        for key, test_result in result.items():
            if isinstance(test_result, dict) and "test_in" in test_result and test_result["score"] == 0:
                bad_input += f"{index}) {str(test_result['test_in']).strip()}\n"
                if "timed out" in test_result["test_out"]:
                    bad_input += "Таймаут\n"
                break
    return (
        "Задача проверена.\n"
        f"Результат:\nНабрано {result['res_score']} баллов из {result['max_res_score']} возможных.\n"
        f"{bad_input}"
    )


class ContestClientService:
    def __init__(self, api_client, course="kate_test", random_generator=None):
        self.api_client = api_client
        self.course = course
        self.random = random_generator or random
        self.user_data = {}
        self.user = ""
        self.problem_counts = {1: 1, 2: 0, 3: 0}

    def load_user_data(self, user_name):
        if not user_name:
            raise ValueError("Задайте имя студента!")

        self.user = user_name
        user_info = self.api_client.get_user_info(user_name)
        if "result" in user_info and "data" in user_info["result"]:
            self.user_data = user_info["result"]["data"]

        if self.course not in self.user_data:
            problems_response = self.api_client.get_courses_data(user_name, self.course)
            problems = problems_response["result"]["problems"]
            selected = select_problem_set(problems, self.problem_counts, self.random)
            self.user_data[self.course] = selected
            self.api_client.add_user_info(user_name, self.user_data)

        return self.user_data[self.course]

    def get_problem_variant_count(self, problem_index):
        problem = self.user_data[self.course][problem_index]
        numeric_key = [key for key in problem.keys() if key.isnumeric()][0]
        return max(1, len(problem[numeric_key]))

    def get_problem_statement(self, problem_index):
        problem = self.user_data[self.course][problem_index]
        last_result = problem.get("last_result", "")
        if last_result:
            last_result = "\n-----\n" + last_result
        return problem["task"] + last_result

    def submit_solution(self, problem_index, variant, language, code):
        request_id = str(uuid.uuid4())
        params = {
            "mqtt_key": "123",
            "user": self.user,
            "language": language,
            "course": self.course,
            "action": "test_problem",
            "problem": get_problem_number(self.user_data[self.course][problem_index]),
            "variant": str(variant),
            "code": code,
        }
        self.api_client.add_message(params, request_id=request_id)
        result = self.api_client.poll_message_result(request_id)
        processor_result = result["result"]["equal_processor"]
        formatted = format_check_result(processor_result)
        self.user_data[self.course][problem_index]["last_result"] = formatted
        self.api_client.add_user_info(self.user, self.user_data)
        return formatted
