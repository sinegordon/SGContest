import os
import sys
from pathlib import Path

from django.test import TestCase
from django.urls import reverse
import django

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contest_client_project.settings")
django.setup()

from client.services import parse_bulk_problems_json, parse_tests_text


class ClientPageTests(TestCase):
    def test_index_page_loads(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_ops_requires_staff(self):
        response = self.client.get(reverse("ops"))
        self.assertEqual(response.status_code, 302)

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
