import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services import (  # noqa: E402
    ContestClientService,
    format_check_result,
    get_problem_number,
    select_problem_set,
    split_problems_by_rating,
)


class FakeRandom:
    def sample(self, values, count):
        return values[:count]


class FakeApiClient:
    def __init__(self):
        self.user_info_response = {"result": {"data": {}}}
        self.courses_response = {
            "result": {
                "problems": [
                    {"1": ["1"], "rating": 1, "task": "Task 1"},
                    {"2": ["1"], "rating": 2, "task": "Task 2"},
                    {"3": ["1"], "rating": 3, "task": "Task 3"},
                ]
            }
        }
        self.added_messages = []
        self.saved_user_info = []
        self.polled_result = {
            "result": {
                "equal_processor": {
                    "1": {"score": 10, "test_in": "1", "test_out": "2"},
                    "res_score": 10,
                    "max_res_score": 10,
                }
            }
        }

    def get_user_info(self, user_name):
        return self.user_info_response

    def get_courses_data(self, user_name, course):
        return self.courses_response

    def add_user_info(self, user_name, data):
        self.saved_user_info.append((user_name, data))
        return {"result": "sucess"}

    def add_message(self, params, request_id=None):
        self.added_messages.append((request_id, params))
        return {"result": "success"}

    def poll_message_result(self, request_id, timeout=30, interval=1):
        return self.polled_result


class ServiceTests(unittest.TestCase):
    def test_get_problem_number(self):
        self.assertEqual(get_problem_number({"12": ["1"], "rating": 1}), 12)

    def test_split_problems_by_rating(self):
        grouped = split_problems_by_rating(
            [
                {"1": ["1"], "rating": 1},
                {"2": ["1"], "rating": 2},
                {"3": ["1"], "rating": 3},
            ]
        )
        self.assertEqual(grouped, {1: ["1"], 2: ["2"], 3: ["3"]})

    def test_select_problem_set(self):
        problems = [
            {"1": ["1"], "rating": 1, "task": "Task 1"},
            {"2": ["1"], "rating": 2, "task": "Task 2"},
            {"3": ["1"], "rating": 3, "task": "Task 3"},
        ]
        selected = select_problem_set(problems, {1: 1, 2: 0, 3: 1}, FakeRandom())
        self.assertEqual(selected, [problems[0], problems[2]])

    def test_format_check_result_success(self):
        result = format_check_result({"res_score": 10, "max_res_score": 10})
        self.assertIn("Набрано 10 баллов из 10 возможных.", result)

    def test_format_check_result_with_failure(self):
        result = format_check_result(
            {
                "1": {"score": 0, "test_in": "42", "test_out": "wrong"},
                "res_score": 0,
                "max_res_score": 10,
            }
        )
        self.assertIn("Ошибочные результаты", result)
        self.assertIn("42", result)

    def test_load_user_data_creates_assignment_when_missing(self):
        service = ContestClientService(FakeApiClient(), random_generator=FakeRandom())

        problems = service.load_user_data("alice")

        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["task"], "Task 1")

    def test_get_problem_statement_includes_last_result(self):
        api = FakeApiClient()
        service = ContestClientService(api, random_generator=FakeRandom())
        service.user_data = {"kate_test": [{"1": ["1"], "task": "Task 1", "last_result": "Done"}]}

        text = service.get_problem_statement(0)

        self.assertEqual(text, "Task 1\n-----\nDone")

    def test_submit_solution_saves_last_result(self):
        api = FakeApiClient()
        service = ContestClientService(api, random_generator=FakeRandom())
        service.user = "alice"
        service.user_data = {"kate_test": [{"1": ["1"], "task": "Task 1"}]}

        result = service.submit_solution(0, 1, "python", "print(1)")

        self.assertIn("Набрано 10 баллов", result)
        self.assertEqual(len(api.added_messages), 1)
        self.assertEqual(len(api.saved_user_info), 1)


if __name__ == "__main__":
    unittest.main()
