from django.contrib import messages
from django.shortcuts import redirect, render

from client.forms import SelectProblemForm, SettingsForm, SubmitSolutionForm
from client.services import ContestApiClient, ContestApiError, ContestWebService


SESSION_KEYS = (
    "server_url",
    "course",
    "language",
    "user_name",
    "user_data",
    "current_problem_index",
)


def build_service(request):
    server_url = request.session.get("server_url", "http://62.76.72.55:57888")
    course = request.session.get("course", "kate_test")
    language = request.session.get("language", "python")
    user_name = request.session.get("user_name", "")
    user_data = request.session.get("user_data", {})

    service = ContestWebService(ContestApiClient(server_url), course=course)
    service.language = language
    service.user = user_name
    service.user_data = user_data
    return service


def save_service_state(request, service, current_problem_index):
    request.session["server_url"] = service.api_client.base_url
    request.session["course"] = service.course
    request.session["language"] = service.language
    request.session["user_name"] = service.user
    request.session["user_data"] = service.user_data
    request.session["current_problem_index"] = current_problem_index


def reset_session_state(request):
    for key in SESSION_KEYS:
        request.session.pop(key, None)


def decode_uploaded_file(uploaded_file):
    raw = uploaded_file.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1251")


def index_view(request):
    service = build_service(request)
    current_problem_index = request.session.get("current_problem_index", 0)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "reset":
            reset_session_state(request)
            messages.success(request, "Сессия сброшена.")
            return redirect("index")

        if action == "load_user":
            settings_form = SettingsForm(request.POST)
            if settings_form.is_valid():
                service = ContestWebService(
                    ContestApiClient(settings_form.cleaned_data["server_url"]),
                    course=settings_form.cleaned_data["course"],
                )
                service.language = settings_form.cleaned_data["language"]
                try:
                    service.load_user_data(settings_form.cleaned_data["user_name"])
                except (ValueError, ContestApiError) as err:
                    messages.error(request, str(err))
                else:
                    save_service_state(request, service, 0)
                    messages.success(request, "Пользователь загружен.")
                    return redirect("index")
        elif action == "select_problem":
            form = SelectProblemForm(request.POST)
            if form.is_valid() and service.get_problem_count() > 0:
                selected_index = max(0, min(form.cleaned_data["problem_index"] - 1, service.get_problem_count() - 1))
                save_service_state(request, service, selected_index)
                return redirect("index")
        elif action == "submit_solution" and service.get_problem_count() > 0:
            form = SubmitSolutionForm(request.POST, request.FILES)
            if form.is_valid():
                service.language = request.session.get("language", "python")
                try:
                    code = decode_uploaded_file(form.cleaned_data["code_file"])
                    service.submit_solution(current_problem_index, form.cleaned_data["variant"], service.language, code)
                except ContestApiError as err:
                    messages.error(request, str(err))
                else:
                    save_service_state(request, service, current_problem_index)
                    messages.success(request, "Решение проверено.")
                    return redirect("index")

    current_problem = None
    current_text = ""
    problem_count = service.get_problem_count()
    if problem_count > 0:
        current_problem_index = max(0, min(current_problem_index, problem_count - 1))
        current_problem = service.user_data[service.course][current_problem_index]
        current_text = service.get_problem_statement(current_problem_index)
        variant_count = service.get_problem_variant_count(current_problem_index)
    else:
        variant_count = 1

    context = {
        "settings_form": SettingsForm(
            initial={
                "user_name": request.session.get("user_name", ""),
                "server_url": request.session.get("server_url", "http://62.76.72.55:57888"),
                "course": request.session.get("course", "kate_test"),
                "language": request.session.get("language", "python"),
            }
        ),
        "select_problem_form": SelectProblemForm(initial={"problem_index": current_problem_index + 1}),
        "submit_solution_form": SubmitSolutionForm(initial={"variant": 1}),
        "is_loaded": problem_count > 0,
        "problem_count": problem_count,
        "variant_range": range(1, variant_count + 1),
        "current_problem_index": current_problem_index + 1,
        "current_problem": current_problem,
        "current_text": current_text,
        "course": request.session.get("course", "kate_test"),
        "language": request.session.get("language", "python"),
    }
    return render(request, "client/index.html", context)
