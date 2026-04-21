from django import forms


LANGUAGE_CHOICES = (
    ("python", "python"),
    ("c#", "c#"),
    ("c", "c"),
    ("c++", "c++"),
)


class SettingsForm(forms.Form):
    user_name = forms.CharField(label="Имя студента", max_length=255)
    server_url = forms.URLField(label="Адрес сервера", initial="http://62.76.72.55:57888", assume_scheme="http")
    course = forms.CharField(label="Код курса", initial="kate_test", max_length=255)
    language = forms.ChoiceField(label="Язык программирования", choices=LANGUAGE_CHOICES)


class SelectProblemForm(forms.Form):
    problem_index = forms.IntegerField(min_value=1, label="Тестовая задача")


class SubmitSolutionForm(forms.Form):
    variant = forms.IntegerField(min_value=1, label="Вариант", initial=1)
    code_file = forms.FileField(label="Файл с решением")


class AdminSettingsForm(forms.Form):
    server_url = forms.URLField(label="Адрес сервера", initial="http://62.76.72.55:57888", assume_scheme="http")
    admin_key = forms.CharField(label="Admin key", required=False, max_length=255)
    service_user = forms.CharField(label="Технический пользователь", initial="admin", max_length=255)


class CourseLookupForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255, required=False)


class DumpLookupForm(forms.Form):
    processor_name = forms.CharField(label="Процессор", initial="equal_processor", max_length=255)
    date = forms.DateField(label="Дата", widget=forms.DateInput(attrs={"type": "date"}))


class ProblemCrudForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255)
    problem = forms.IntegerField(label="Номер задачи", min_value=1)
    variant = forms.CharField(label="Вариант", initial="1", max_length=32)
    problem_type = forms.CharField(label="Тип", initial="equal", max_length=64)
    rating = forms.IntegerField(label="Сложность", initial=1, min_value=1)
    task = forms.CharField(label="Условие", widget=forms.Textarea, required=False)
    tests_text = forms.CharField(
        label="Тесты по строкам",
        widget=forms.Textarea,
        required=False,
        help_text="Формат строки: test_id | input | output | score | time(optional)",
    )
    tests_json = forms.CharField(
        label="Тесты JSON",
        widget=forms.Textarea,
        required=False,
        help_text='Например: {"1": {"in": "1", "out": "2", "score": 10}}',
    )


class DeleteProblemForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255)
    problem = forms.IntegerField(label="Номер задачи", min_value=1)


class BulkImportProblemsForm(forms.Form):
    course = forms.CharField(label="Курс", max_length=255)
    default_type = forms.CharField(label="Тип по умолчанию", initial="equal", max_length=64)
    default_rating = forms.IntegerField(label="Сложность по умолчанию", initial=1, min_value=1)
    problems_file = forms.FileField(label="JSON-файл с задачами")
