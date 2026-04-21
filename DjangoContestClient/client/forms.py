from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from urllib.parse import urlparse


LANGUAGE_CHOICES = (
    ("python", "python"),
    ("c#", "c#"),
    ("c", "c"),
    ("c++", "c++"),
)


class ServerUrlFormMixin:
    def clean_server_url(self):
        server_url = self.cleaned_data["server_url"].strip()
        parsed = urlparse(server_url)
        if not parsed.scheme:
            server_url = f"http://{server_url}"
            parsed = urlparse(server_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or not parsed.hostname:
            raise ValidationError("Введите правильный URL.")
        return server_url


class SettingsForm(ServerUrlFormMixin, forms.Form):
    user_name = forms.CharField(label="Имя студента", max_length=255)
    server_url = forms.CharField(label="Адрес сервера", initial=settings.CONTEST_SERVER_URL, max_length=255)
    course = forms.CharField(label="Код курса", initial="", max_length=255)
    language = forms.ChoiceField(label="Язык программирования", choices=LANGUAGE_CHOICES)


class SelectProblemForm(forms.Form):
    problem_index = forms.TypedChoiceField(label="Тестовая задача", coerce=int, choices=())

    def __init__(self, *args, problem_count=0, **kwargs):
        super().__init__(*args, **kwargs)
        max_problem_count = max(0, int(problem_count))
        choices = [(index, str(index)) for index in range(1, max_problem_count + 1)]
        self.fields["problem_index"].choices = choices


class SubmitSolutionForm(forms.Form):
    language = forms.ChoiceField(label="Язык проверки", choices=LANGUAGE_CHOICES, initial="python")
    code_file = forms.FileField(label="Файл с решением")


class AdminSettingsForm(ServerUrlFormMixin, forms.Form):
    server_url = forms.CharField(label="Адрес сервера", initial=settings.CONTEST_SERVER_URL, max_length=255)
    admin_key = forms.CharField(label="Admin key", required=False, max_length=255)
    service_user = forms.CharField(label="Технический пользователь", initial="admin", max_length=255)


class CourseLookupForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255, required=False)


class CreateCourseForm(forms.Form):
    course = forms.CharField(label="Новый курс", max_length=255)


class CreateUserForm(forms.Form):
    user_name = forms.CharField(label="Новый пользователь", max_length=255)
    user_data_json = forms.CharField(
        label="Данные пользователя JSON",
        widget=forms.Textarea,
        required=False,
        help_text='По умолчанию будет использован пустой объект: {}',
    )


class DumpLookupForm(forms.Form):
    processor_name = forms.CharField(label="Процессор", initial="equal_processor", max_length=255)
    date = forms.DateField(label="Дата", widget=forms.DateInput(attrs={"type": "date"}))


class CourseSettingsForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255)
    rating_1_count = forms.TypedChoiceField(label="Задач уровня 1", coerce=int, choices=((0, "0"),), initial=1)
    rating_2_count = forms.TypedChoiceField(label="Задач уровня 2", coerce=int, choices=((0, "0"),), initial=0)
    rating_3_count = forms.TypedChoiceField(label="Задач уровня 3", coerce=int, choices=((0, "0"),), initial=0)

    def __init__(self, *args, rating_limits=None, **kwargs):
        super().__init__(*args, **kwargs)
        rating_limits = rating_limits or {1: 0, 2: 0, 3: 0}
        for rating in (1, 2, 3):
            field_name = f"rating_{rating}_count"
            limit = max(0, int(rating_limits.get(rating, 0)))
            choices = [(value, str(value)) for value in range(0, limit + 1)]
            self.fields[field_name].choices = choices

            if not self.is_bound:
                current_value = self.initial.get(field_name, self.fields[field_name].initial)
                if current_value is None:
                    current_value = 0
                self.initial[field_name] = min(int(current_value), limit)


class ResetUserCourseForm(forms.Form):
    user_name = forms.CharField(label="Студент", max_length=255)
    course = forms.CharField(label="Курс", max_length=255)


class BulkImportProblemsForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255)
    default_type = forms.CharField(label="Тип по умолчанию", initial="equal", max_length=64)
    default_rating = forms.IntegerField(label="Сложность по умолчанию", initial=1, min_value=1)
    problems_file = forms.FileField(label="JSON-файл с задачами")
