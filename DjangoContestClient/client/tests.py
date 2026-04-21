import os
import sys
from pathlib import Path
from unittest.mock import patch
import json

from django.contrib.auth import get_user_model
from django.db import connection
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
import django

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contest_client_project.settings")
django.setup()

from client.forms import CourseSettingsForm, SettingsForm
from client.models import CourseSettings
from client.services import (
    assign_selected_variants,
    parse_bulk_problems_json,
    parse_optional_json_object,
    parse_tests_text,
    select_problem_set,
)
from client.views import build_service

with connection.cursor() as cursor:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS client_coursesettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course VARCHAR(255) NOT NULL UNIQUE,
            rating_1_count INTEGER NOT NULL DEFAULT 1,
            rating_2_count INTEGER NOT NULL DEFAULT 0,
            rating_3_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )


class ClientPageTests(TestCase):
    def test_index_page_loads(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_index_shows_empty_state_for_loaded_user_without_tasks(self):
        session = self.client.session
        session["user_name"] = "alice"
        session["course"] = "empty_course"
        session["language"] = "python"
        session["user_data"] = {"empty_course": []}
        session.save()

        response = self.client.get(reverse("index"))

        self.assertContains(response, "Пользователь:")
        self.assertContains(response, "alice")
        self.assertContains(response, "Нет доступных задач")

    def test_settings_form_accepts_single_host_url(self):
        form = SettingsForm(
            {
                "user_name": "alice",
                "server_url": "http://contest:8000",
                "course": "empty_course",
                "language": "python",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["server_url"], "http://contest:8000")

    def test_course_settings_form_limits_choices_by_real_course_counts(self):
        form = CourseSettingsForm(
            initial={
                "course": "demo",
                "rating_1_count": 3,
                "rating_2_count": 5,
                "rating_3_count": 1,
            },
            rating_limits={1: 2, 2: 0, 3: 1},
        )

        self.assertEqual(form.fields["rating_1_count"].choices, [(0, "0"), (1, "1"), (2, "2")])
        self.assertEqual(form.fields["rating_2_count"].choices, [(0, "0")])
        self.assertEqual(form.fields["rating_3_count"].choices, [(0, "0"), (1, "1")])
        self.assertEqual(form.initial["rating_1_count"], 2)
        self.assertEqual(form.initial["rating_2_count"], 0)
        self.assertEqual(form.initial["rating_3_count"], 1)

    def test_load_user_invalid_form_shows_error_message(self):
        response = self.client.post(
            reverse("index"),
            {
                "action": "load_user",
                "user_name": "alice",
                "server_url": "://bad-url",
                "course": "empty_course",
                "language": "python",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Проверьте поля формы загрузки пользователя.")

    def test_index_does_not_show_server_url_field(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Адрес сервера</label>", html=False)
        self.assertNotContains(response, "Язык программирования</label>", html=False)

    def test_select_problem_form_limits_choices_to_real_problem_count(self):
        session = self.client.session
        session["user_name"] = "alice"
        session["course"] = "demo"
        session["language"] = "python"
        session["user_data"] = {
            "demo": [
                {"task": "Задача 1", "1": {"1": {}}},
                {"task": "Задача 2", "1": {"1": {}}},
                {"task": "Задача 3", "1": {"1": {}}},
            ]
        }
        session["current_problem_index"] = 1
        session.save()

        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="problem_index"', html=False)
        self.assertContains(response, '<option value="1">1</option>', html=False)
        self.assertContains(response, '<option value="2" selected>2</option>', html=False)
        self.assertContains(response, '<option value="3">3</option>', html=False)
        self.assertNotContains(response, '<option value="4">4</option>', html=False)

    @patch("client.views.build_service")
    def test_submit_solution_ajax_returns_json_without_redirect(self, build_service_mock):
        class FakeService:
            class ApiClient:
                base_url = "http://contest:8000"

            api_client = ApiClient()
            course = "demo"
            language = "python"
            user = "alice"
            user_data = {
                "demo": [
                    {
                        "1": {"1": {}, "2": {}},
                        "selected_variant": "2",
                        "task": "Старая задача",
                    }
                ]
            }

            def get_problem_count(self):
                return 1

            def get_problem_statement(self, problem_index):
                return self.user_data["demo"][problem_index]["task"]

            def submit_solution(self, problem_index, language, code):
                self.last_submit_args = (problem_index, language, code)
                self.user_data["demo"][problem_index]["task"] = "Новая задача\n-----\nРешение проверено."
                return "Решение проверено."

        build_service_mock.return_value = FakeService()
        session = self.client.session
        session["user_name"] = "alice"
        session["course"] = "demo"
        session["language"] = "python"
        session["user_data"] = {"demo": [{"1": {"1": {}, "2": {}}, "selected_variant": "2", "task": "Старая задача"}]}
        session["current_problem_index"] = 0
        session.save()

        upload = SimpleUploadedFile("solution.py", b"print(1)\n", content_type="text/x-python")
        response = self.client.post(
            reverse("index"),
            {
                "action": "submit_solution",
                "language": "c++",
                "code_file": upload,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode("utf-8"))
        self.assertTrue(data["ok"])
        self.assertEqual(data["message"], "Решение проверено.")
        self.assertIn("Новая задача", data["current_text"])
        self.assertEqual(build_service_mock.return_value.last_submit_args[1], "c++")
        self.assertEqual(self.client.session["language"], "c++")

    def test_submit_solution_form_shows_supported_languages(self):
        session = self.client.session
        session["user_name"] = "alice"
        session["course"] = "demo"
        session["language"] = "c"
        session["user_data"] = {
            "demo": [
                {"task": "Задача 1", "1": {"1": {}, "2": {}}, "selected_variant": "1"},
            ]
        }
        session["current_problem_index"] = 0
        session.save()

        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="language"', html=False)
        self.assertContains(response, '<option value="python">python</option>', html=False)
        self.assertContains(response, '<option value="c#">c#</option>', html=False)
        self.assertContains(response, '<option value="c" selected>c</option>', html=False)
        self.assertContains(response, '<option value="c++">c++</option>', html=False)
        self.assertNotContains(response, 'name="variant"', html=False)

    def test_assign_selected_variants_sets_random_variant_once(self):
        problems = [{"12": {"1": {}, "2": {}}, "task": "Demo"}]

        class FakeRandom:
            @staticmethod
            def choice(values):
                return values[-1]

        changed = assign_selected_variants(problems, FakeRandom())

        self.assertTrue(changed)
        self.assertEqual(problems[0]["selected_variant"], "2")

    def test_load_user_data_assigns_selected_variant_and_persists_user(self):
        from client.services import ContestWebService

        class FakeApiClient:
            def __init__(self):
                self.saved = None

            def get_user_info(self, user_name):
                return {"result": {"data": {}}}

            def get_courses_data(self, user_name, course):
                return {
                    "result": {
                        "problems": [
                            {"10": {"1": {}, "2": {}}, "task": "A", "rating": 1},
                        ]
                    }
                }

            def add_user_info(self, user_name, data):
                self.saved = (user_name, data)
                return {"result": "ok"}

        class FakeRandom:
            @staticmethod
            def sample(values, count):
                return list(values)[:count]

            @staticmethod
            def choice(values):
                return values[-1]

        api_client = FakeApiClient()
        service = ContestWebService(
            api_client,
            course="demo",
            random_generator=FakeRandom(),
            problem_counts={1: 1, 2: 0, 3: 0},
        )

        loaded = service.load_user_data("alice")

        self.assertEqual(loaded[0]["selected_variant"], "2")
        self.assertEqual(api_client.saved[0], "alice")
        self.assertEqual(api_client.saved[1]["demo"][0]["selected_variant"], "2")

    def test_ops_requires_staff(self):
        response = self.client.get(reverse("ops"))
        self.assertEqual(response.status_code, 302)

    @patch("client.views.build_ops_client")
    def test_ops_bulk_import_persists_selected_course_and_shows_course_problems(self, build_ops_client_mock):
        class FakeOpsClient:
            def add_or_update_problem(self, user_name, course, problem_number, variant, problem_type, rating, task, tests):
                return {"result": {"status": "ok", "course": course, "problem": problem_number, "variant": variant}}

            def get_courses_data(self, user_name, course):
                return {"result": {"problems": [{str(90): ["1", "2"], "rating": 1, "task": "Demo"}]}}

        build_ops_client_mock.return_value = FakeOpsClient()
        user = get_user_model().objects.create_user("staff", password="pass", is_staff=True)
        self.client.force_login(user)

        upload = SimpleUploadedFile(
            "problems.json",
            b'[{"problem": 90, "task": "Demo", "variants": {"1": {"1": {"in": "1", "out": "2", "score": 10}}}}]',
            content_type="application/json",
        )

        response = self.client.post(
            reverse("ops"),
            {
                "action": "bulk_import",
                "course": "test",
                "default_type": "equal",
                "default_rating": "1",
                "problems_file": upload,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("ops_results"))
        session = self.client.session
        self.assertEqual(session["ops_course"], "test")
        self.assertIn("ops_results", session)

        results_response = self.client.get(reverse("ops_results"))
        self.assertEqual(results_response.status_code, 200)
        self.assertContains(results_response, "test")
        self.assertContains(results_response, "Задачи курса test")
        self.assertContains(results_response, "Результат пакетного импорта")

    @patch("client.views.build_ops_client")
    def test_ops_get_dump_returns_json_file(self, build_ops_client_mock):
        class FakeOpsClient:
            def get_base_dump(self, date, processor_name, admin_key):
                return {"result": [{"processor": processor_name, "date": str(date)}]}

        build_ops_client_mock.return_value = FakeOpsClient()
        user = get_user_model().objects.create_user("ops", password="pass", is_staff=True)
        self.client.force_login(user)

        session = self.client.session
        session["ops_admin_key"] = "secret"
        session.save()

        response = self.client.post(
            reverse("ops"),
            {
                "action": "get_dump",
                "processor_name": "equal_processor",
                "date": "2026-04-21",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")
        self.assertIn(
            'attachment; filename="contest_dump_equal_processor_2026-04-21.json"',
            response["Content-Disposition"],
        )
        self.assertEqual(
            json.loads(response.content.decode("utf-8")),
            [{"processor": "equal_processor", "date": "2026-04-21"}],
        )

    def test_ops_results_page_loads_without_saved_results(self):
        user = get_user_model().objects.create_user("staff2", password="pass", is_staff=True)
        self.client.force_login(user)

        response = self.client.get(reverse("ops_results"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пока нет сохранённых результатов")

    def test_build_service_uses_course_settings_from_db(self):
        CourseSettings.objects.create(course="demo", rating_1_count=2, rating_2_count=1, rating_3_count=0)
        session = self.client.session
        session["course"] = "demo"
        session.save()

        request = self.client.get(reverse("index")).wsgi_request
        request.session = self.client.session
        service = build_service(request)

        self.assertEqual(service.problem_counts, {1: 2, 2: 1, 3: 0})

    @patch("client.views.build_ops_client")
    def test_ops_can_save_course_settings(self, build_ops_client_mock):
        class FakeOpsClient:
            def get_courses_data(self, user_name, course):
                return {
                    "result": {
                        "problems": [
                            {"90": ["1"], "rating": 1, "task": "A"},
                            {"91": ["1"], "rating": 1, "task": "B"},
                            {"92": ["1"], "rating": 2, "task": "C"},
                        ]
                    }
                }

        build_ops_client_mock.return_value = FakeOpsClient()
        user = get_user_model().objects.create_user("staff3", password="pass", is_staff=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse("ops"),
            {
                "action": "save_course_settings",
                "course": "demo",
                "rating_1_count": "2",
                "rating_2_count": "1",
                "rating_3_count": "0",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("ops_results"))
        settings_obj = CourseSettings.objects.get(course="demo")
        self.assertEqual(settings_obj.problem_counts, {1: 2, 2: 1, 3: 0})

    @patch("client.views.build_ops_client")
    def test_ops_can_load_course_settings_limits_without_redirect(self, build_ops_client_mock):
        class FakeOpsClient:
            def get_courses_data(self, user_name, course):
                return {
                    "result": {
                        "problems": [
                            {"90": ["1"], "rating": 1, "task": "A"},
                            {"91": ["1"], "rating": 1, "task": "B"},
                            {"92": ["1"], "rating": 2, "task": "C"},
                            {"93": ["1"], "rating": 3, "task": "D"},
                        ]
                    }
                }

        build_ops_client_mock.return_value = FakeOpsClient()
        user = get_user_model().objects.create_user("staff-load", password="pass", is_staff=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse("ops"),
            {
                "action": "load_course_settings",
                "course": "demo",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["ops_course"], "demo")
        self.assertContains(response, 'value="2"')
        self.assertContains(response, 'value="1"')
        self.assertContains(response, "Задач уровня 1 в курсе")
        self.assertContains(response, "Задач уровня 2 в курсе")
        self.assertContains(response, "Задач уровня 3 в курсе")
        self.assertContains(response, "Данные курса &#x27;demo&#x27; загружены")

    @patch("client.views.build_ops_client")
    def test_ops_can_reset_user_course_assignment(self, build_ops_client_mock):
        class FakeOpsClient:
            def __init__(self):
                self.saved = None

            def get_user_info(self, user_name):
                return {
                    "result": {
                        "user_name": user_name,
                        "data": {
                            "test": [{"90": ["1"], "rating": 1, "task": "Demo"}],
                            "other": [{"1": ["1"], "rating": 1, "task": "Other"}],
                        },
                    }
                }

            def create_or_update_user(self, user_name, data):
                self.saved = (user_name, data)
                return {"result": "success"}

        fake_client = FakeOpsClient()
        build_ops_client_mock.return_value = fake_client
        user = get_user_model().objects.create_user("staff4", password="pass", is_staff=True)
        self.client.force_login(user)

        response = self.client.post(
            reverse("ops"),
            {
                "action": "reset_user_course",
                "user_name": "alice",
                "course": "test",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("ops_results"))
        self.assertEqual(fake_client.saved, ("alice", {"other": [{"1": ["1"], "rating": 1, "task": "Other"}]}))

    def test_parse_tests_text(self):
        tests = parse_tests_text("1 | 10 | 11 | 5 | 3\n2 | 4 | 5 | 10")
        self.assertEqual(
            tests,
            {
                "1": {"in": "10", "out": "11", "score": 5, "time": 3},
                "2": {"in": "4", "out": "5", "score": 10},
            },
        )

    def test_parse_bulk_problems_json(self):
        data = parse_bulk_problems_json('[{"problem": 1, "variants": {"1": {"1": {"in": "1", "out": "2", "score": 10}}}}]')
        self.assertEqual(data[0]["problem"], 1)

    def test_parse_optional_json_object_returns_empty_dict_for_blank_input(self):
        self.assertEqual(parse_optional_json_object("", "user_data_json"), {})

    def test_parse_optional_json_object_parses_dict(self):
        self.assertEqual(parse_optional_json_object('{"score": 10}', "user_data_json"), {"score": 10})

    def test_select_problem_set_returns_empty_list_for_empty_course(self):
        self.assertEqual(select_problem_set([], {1: 1, 2: 0, 3: 0}), [])
