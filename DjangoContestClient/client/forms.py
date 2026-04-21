from django import forms


LANGUAGE_CHOICES = (
    ("python", "python"),
    ("c#", "c#"),
    ("c", "c"),
    ("c++", "c++"),
)


class SettingsForm(forms.Form):
    user_name = forms.CharField(label="Имя студента", max_length=255)
    server_url = forms.URLField(label="Адрес сервера", initial="http://62.76.72.55:57888")
    course = forms.CharField(label="Код курса", initial="kate_test", max_length=255)
    language = forms.ChoiceField(label="Язык программирования", choices=LANGUAGE_CHOICES)


class SelectProblemForm(forms.Form):
    problem_index = forms.IntegerField(min_value=1, label="Тестовая задача")


class SubmitSolutionForm(forms.Form):
    variant = forms.IntegerField(min_value=1, label="Вариант", initial=1)
    code_file = forms.FileField(label="Файл с решением")
