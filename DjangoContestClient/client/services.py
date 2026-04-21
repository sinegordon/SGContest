import random
import json
import time
import uuid

import requests


class ContestApiError(Exception):
    pass


class ContestApiClient:
    def __init__(self, base_url, session=None, timeout=10):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

    def call(self, method, params, request_id=None):
        request_id = request_id or str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        try:
            response = self.session.post(
                f"{self.base_url}/api/run",
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as err:
            raise ContestApiError(f"Network error: {err}") from err

        if not response.ok:
            raise ContestApiError(f"HTTP error: {response.status_code}")

        try:
            data = response.json()
        except ValueError as err:
            raise ContestApiError("Server returned invalid JSON") from err

        if not isinstance(data, dict):
            raise ContestApiError("Server returned unexpected response")
        if "error" in data:
            raise ContestApiError(data["error"].get("message", "Unknown API error"))
        if "result" not in data:
            raise ContestApiError("Server response does not contain result")
        return data

    def get_user_info(self, user_name):
        return self.call("get_user_info", {"user_name": user_name})

    def add_user_info(self, user_name, data):
        return self.call("add_user_info", {"user_name": user_name, "data": data})

    def get_courses_data(self, user_name, course):
        return self.call(
            "get_courses_data",
            {
                "mqtt_key": "234",
                "user": user_name,
                "type": "problems",
                "data_key": course,
                "action": "get_data",
            },
        )

    def get_courses_catalog(self, user_name="admin"):
        return self.call(
            "get_courses_data",
            {
                "mqtt_key": "234",
                "user": user_name,
                "type": "courses",
                "data_key": "",
                "action": "get_data",
            },
        )

    def clear_course(self, user_name, course):
        return self.call(
            "clear_data",
            {
                "mqtt_key": "234",
                "user": user_name,
                "type": "course",
                "data_key": course,
                "action": "clear_data",
            },
        )

    def create_course(self, course_name):
        return self.call("create_course", {"course": course_name})

    def get_base_dump(self, date, processor_name, admin_key):
        return self.call(
            "get_base_dump",
            {
                "date": str(date),
                "processor_name": processor_name,
                "admin_key": admin_key,
            },
        )

    def add_message(self, params, request_id=None):
        return self.call("add_message", params, request_id=request_id)

    def get_message_result(self, request_id):
        return self.call("get_message_result", {}, request_id=request_id)

    def poll_message_result(self, request_id, timeout=30, interval=1):
        started_at = time.time()
        while time.time() - started_at <= timeout:
            try:
                return self.get_message_result(request_id)
            except ContestApiError:
                time.sleep(interval)
        raise ContestApiError("Задача не была проверена за отведенное время. Попробуйте еще раз.")

    def add_or_update_problem(self, user_name, course, problem_number, variant, problem_type, rating, task, tests):
        request_id = str(uuid.uuid4())
        self.add_message(
            {
                "mqtt_key": 123,
                "user": user_name,
                "type": problem_type,
                "rating": int(rating),
                "course": course,
                "problem": int(problem_number),
                "variant": str(variant),
                "action": "add_problem",
                "task": task,
                "tests": tests,
            },
            request_id=request_id,
        )
        return self.poll_message_result(request_id)

    def create_or_update_user(self, user_name, data):
        return self.add_user_info(user_name, data)


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
        available_numbers = grouped.get(rating, [])
        if not available_numbers:
            continue
        sample_size = min(count, len(available_numbers))
        selected_numbers.extend(rng.sample(available_numbers, sample_size))
    return [problem for problem in problems if any(number in problem for number in selected_numbers)]


def get_problem_variant_keys(problem):
    numeric_key = [key for key in problem.keys() if key.isnumeric()][0]
    variants = problem.get(numeric_key, {})
    return sorted(str(variant) for variant in variants.keys())


def assign_selected_variants(problems, rng=None):
    rng = rng or random
    changed = False
    for problem in problems:
        variant_keys = get_problem_variant_keys(problem)
        if not variant_keys:
            continue
        selected_variant = str(problem.get("selected_variant", "")).strip()
        if selected_variant not in variant_keys:
            problem["selected_variant"] = rng.choice(variant_keys)
            changed = True
    return changed


def format_check_result(result):
    if result["max_res_score"] == result["res_score"]:
        bad_input = ""
    else:
        bad_input = "Ошибочные результаты получены на следующих входных данных:\n"
        index = 1
        for test_result in result.values():
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


class ContestWebService:
    def __init__(self, api_client, course="kate_test", random_generator=None, problem_counts=None):
        self.api_client = api_client
        self.course = course
        self.random = random_generator or random
        self.user_data = {}
        self.user = ""
        self.language = "python"
        self.problem_counts = problem_counts or {1: 1, 2: 0, 3: 0}

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
            assign_selected_variants(selected, self.random)
            self.user_data[self.course] = selected
            self.api_client.add_user_info(user_name, self.user_data)
        elif assign_selected_variants(self.user_data[self.course], self.random):
            self.api_client.add_user_info(user_name, self.user_data)

        return self.user_data[self.course]

    def get_problem_count(self):
        return len(self.user_data.get(self.course, []))

    def get_problem_variant_count(self, problem_index):
        problem = self.user_data[self.course][problem_index]
        return max(1, len(get_problem_variant_keys(problem)))

    def get_selected_variant(self, problem_index):
        problem = self.user_data[self.course][problem_index]
        selected_variant = str(problem.get("selected_variant", "")).strip()
        if selected_variant:
            return selected_variant
        variant_keys = get_problem_variant_keys(problem)
        if not variant_keys:
            return "1"
        selected_variant = self.random.choice(variant_keys)
        problem["selected_variant"] = selected_variant
        self.api_client.add_user_info(self.user, self.user_data)
        return selected_variant

    def get_problem_statement(self, problem_index):
        problem = self.user_data[self.course][problem_index]
        last_result = problem.get("last_result", "")
        if last_result:
            last_result = "\n-----\n" + last_result
        return problem["task"] + last_result

    def submit_solution(self, problem_index, language, code):
        request_id = str(uuid.uuid4())
        params = {
            "mqtt_key": "123",
            "user": self.user,
            "language": language,
            "course": self.course,
            "action": "test_problem",
            "problem": get_problem_number(self.user_data[self.course][problem_index]),
            "variant": self.get_selected_variant(problem_index),
            "code": code,
        }
        self.api_client.add_message(params, request_id=request_id)
        result = self.api_client.poll_message_result(request_id)
        processor_result = result["result"]["equal_processor"]
        formatted = format_check_result(processor_result)
        self.user_data[self.course][problem_index]["last_result"] = formatted
        self.api_client.add_user_info(self.user, self.user_data)
        return formatted


def parse_tests_json(raw_json):
    if not raw_json.strip():
        raise ContestApiError("Заполните тесты через строки или JSON.")
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as err:
        raise ContestApiError(f"Некорректный JSON тестов: {err}") from err
    if not isinstance(data, dict):
        raise ContestApiError("Тесты должны быть JSON-объектом.")
    return data


def parse_tests_text(raw_text):
    if not raw_text.strip():
        raise ContestApiError("Заполните тесты через строки или JSON.")

    tests = {}
    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) not in (4, 5):
            raise ContestApiError(
                f"Строка теста {line_number} должна быть в формате: test_id | input | output | score | time(optional)"
            )
        test_id, test_in, test_out, score = parts[:4]
        if not test_id:
            raise ContestApiError(f"В строке {line_number} отсутствует test_id.")
        test_data = {
            "in": test_in,
            "out": test_out,
            "score": int(score),
        }
        if len(parts) == 5 and parts[4]:
            test_data["time"] = int(parts[4])
        tests[str(test_id)] = test_data
    if not tests:
        raise ContestApiError("Не удалось прочитать ни одного теста.")
    return tests


def parse_bulk_problems_json(raw_json):
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as err:
        raise ContestApiError(f"Некорректный JSON файла задач: {err}") from err
    if not isinstance(data, list):
        raise ContestApiError("Файл задач должен содержать JSON-массив.")
    return data


def parse_optional_json_object(raw_json, field_name):
    if not raw_json.strip():
        return {}
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as err:
        raise ContestApiError(f"Некорректный JSON для поля '{field_name}': {err}") from err
    if not isinstance(data, dict):
        raise ContestApiError(f"Поле '{field_name}' должно содержать JSON-объект.")
    return data
